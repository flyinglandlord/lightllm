import os
import torch
import flux

from .base_weight import BaseWeightTpl
from typing import Optional, Tuple, List, Dict, Any
from lightllm.common.basemodel.layer_infer.cache_tensor_manager import g_cache_manager
from lightllm.common.quantization.quantize_method import QuantizationMethod
from lightllm.utils.dist_utils import get_current_device_id
from torch.distributed import ProcessGroup


def generate_scale_name(name, weight_scale_suffix, act_scale_suffix):
    weight_scale_name = None
    act_scale_name = None
    if weight_scale_suffix is not None:
        weight_scale_name = ".".join(name.split(".")[:-1] + [weight_scale_suffix])
    if act_scale_suffix is not None:
        act_scale_name = ".".join(name.split(".")[:-1] + [act_scale_suffix])
    return weight_scale_name, act_scale_name


STATIC_QUANT = os.getenv("STATIC_QUANT", "0").upper() in ["1", "TRUE", "ON"]


class MMWeightTpl(BaseWeightTpl):
    def __init__(self, data_type: torch.dtype) -> None:
        super().__init__()
        self.data_type_ = data_type
        self.quant_method: Optional[QuantizationMethod] = None
        self.weight: Optional[torch.Tensor] = None
        self.bias: Optional[torch.Tensor] = None
        self.weight_scale: Optional[torch.Tensor] = None
        self.input_scale: Optional[torch.Tensor] = None
        self.enable_flux = os.getenv("ENABLE_FLUX", "0").upper() in ["ON", "TRUE", "1"]

    def set_quant_method(self, quant_method: QuantizationMethod) -> None:
        self.quant_method = quant_method

    def flux_gemm_rs(
        self,
        input_tensor: torch.Tensor,
        out: Optional[torch.Tensor] = None,
        use_custom_tensor_mananger: bool = True,
        tp_group: ProcessGroup = None,
    ):
        print("---------kernel start---------")
        # pad the input tensor to make it size(0) is multiple to self.world_size_
        # then move the input tensor to the specific device
        origin_input_M = input_tensor.size(0)
        if input_tensor.size(0) % self.world_size_ != 0:
            pad_size = (self.world_size_ - input_tensor.size(0) % self.world_size_) % self.world_size_
            pad_tensor = torch.zeros(
                pad_size, input_tensor.size(1), dtype=input_tensor.dtype, device=input_tensor.device
            )
            input_tensor = torch.cat([input_tensor, pad_tensor], dim=0)
        input_tensor = input_tensor.to(f"cuda:{torch.distributed.group.WORLD.rank()}")

        # check the weight contiguous
        if not self.weight.is_contiguous():
            self.weight = self.weight.contiguous()
        assert self.weight.is_contiguous(), "weight must be contiguous"

        # input_tensor: [4, 7168]
        # weight: [7168, 4096]
        print(f"weight shape: {self.weight.shape}")
        print(f"input_tensor shape: {input_tensor.shape}")
        print(f"cuda:{torch.distributed.group.WORLD.rank()}")
        M = input_tensor.size(0)
        local_M = input_tensor.size(0) // self.world_size_
        N = self.weight.size(1)
        local_K = self.weight.size(0)

        torch.cuda.synchronize()

        if out is None:
            # out shape: [4, 4096]
            shape = (origin_input_M, self.weight.shape[1])
            dtype = input_tensor.dtype
            device = input_tensor.device
            if use_custom_tensor_mananger:
                out = g_cache_manager.alloc_tensor(shape, dtype, device=device, is_graph_out=False)
            else:
                out = torch.zeros(shape, dtype=dtype, device=device)
        print("kernel define start")
        with flux.util.group_profile(
            name="gemm_rs_" + os.environ["TORCHELASTIC_RUN_ID"], do_prof=False, group=torch.distributed.group.WORLD
        ):
            gemm_rs_op = flux.GemmRS(
                torch.distributed.group.WORLD,
                1,
                (M + 1024 - 1) // 1024 * 1024,
                N,
                input_tensor.dtype,
                out.dtype,
                transpose_weight=True,
            )
            print(f"gemm_rs_kernel initialized M={M}, N={N}, local_K={local_K}")
            ans = gemm_rs_op.forward(
                input_tensor,
                self.weight,
                bias=self.bias,
                fast_accum=False,
                reduce_scatter_option=flux.ReduceScatterOption(),
            )
            # according to the self.tp_rank_, padding the out tensor to [origin_input_M, N]
            print(ans)
            print(ans.shape)
            tp_M_start_index = local_M * self.tp_rank_
            tp_M_end_index = local_M * (self.tp_rank_ + 1)
            if tp_M_end_index > origin_input_M:
                tp_M_end_index = origin_input_M
            # zero the out tensor
            out[tp_M_start_index:tp_M_end_index, :] = ans[: tp_M_end_index - tp_M_start_index, :]
            print("---------kernel end---------")
            return out, ans

    def flux_ag_gemm(
        self,
        input_tensor: torch.Tensor,
        out: Optional[torch.Tensor] = None,
        use_custom_tensor_mananger: bool = True,
        tp_group: ProcessGroup = None,
    ):
        print("---------kernel start---------")
        origin_input_M = input_tensor.size(0)
        if input_tensor.size(0) % self.world_size_ != 0:
            # if input_tensor.size(0) = 7, world_size = 4, pad_size = 1
            # if input_tensor.size(0) = 8, world_size = 4, pad_size = 0
            pad_size = (self.world_size_ - input_tensor.size(0) % self.world_size_) % self.world_size_
            pad_tensor = torch.zeros(
                pad_size, input_tensor.size(1), dtype=input_tensor.dtype, device=input_tensor.device
            )
            input_tensor = torch.cat([input_tensor, pad_tensor], dim=0)
        input_tensor = input_tensor.to(f"cuda:{torch.distributed.group.WORLD.rank()}")

        # check the weight contiguous
        if not self.weight.is_contiguous():
            self.weight = self.weight.contiguous()
        assert self.weight.is_contiguous(), "weight must be contiguous"

        print(f"weight shape: {self.weight.shape}")
        print(f"input_tensor shape: {input_tensor.shape}")
        print(f"cuda:{torch.distributed.group.WORLD.rank()}")
        M = input_tensor.shape[0]
        K = input_tensor.shape[1]
        N = self.weight.shape[1]
        local_M = input_tensor.size(0) // self.world_size_
        local_M_start_index = local_M * self.tp_rank_
        local_M_end_index = local_M * (self.tp_rank_ + 1)

        if out is None:
            shape = (input_tensor.shape[0], self.weight.shape[1])
            dtype = input_tensor.dtype
            device = input_tensor.device
            if use_custom_tensor_mananger:
                out = g_cache_manager.alloc_tensor(shape, dtype, device=device, is_graph_out=False)
            else:
                out = torch.zeros(shape, dtype=dtype, device=device)
        with flux.util.group_profile(
            name="ag_gemm_" + os.environ["TORCHELASTIC_RUN_ID"], do_prof=False, group=torch.distributed.group.WORLD
        ):
            ag_option = flux.AllGatherOption()
            ag_gemm_op = flux.AGKernel(
                torch.distributed.group.WORLD,
                1,
                M,
                N,
                K,
                input_tensor.dtype,
                output_dtype=out.dtype,
            )
            full_input = torch.empty((M, K), dtype=input_tensor.dtype, device=input_tensor.device)
            print(f"ag_gemm_kernel initialized M={M}, N={N}, K={K}")
            ans = ag_gemm_op.forward(
                input_tensor[local_M_start_index:local_M_end_index],
                self.weight,
                output=out,
                bias=self.bias,
                transpose_weight=True,
                gathered_input=full_input,
                all_gather_option=ag_option,
            )
            print("full_input", full_input)
            print(ans)
            print(ans.shape)
            out = ans[:origin_input_M, :]
            print("---------kernel end---------")
            return out

    def mm(
        self, input_tensor: torch.Tensor, out: Optional[torch.Tensor] = None, use_custom_tensor_mananger: bool = True
    ) -> torch.Tensor:
        if self.quant_method is not None:
            return self.quant_method.apply(
                input_tensor, self.weight, self.bias, out, use_custom_tensor_mananger=use_custom_tensor_mananger
            )
        if out is None:
            shape = (input_tensor.shape[0], self.weight.shape[1])
            dtype = input_tensor.dtype
            device = input_tensor.device
            if use_custom_tensor_mananger:
                out = g_cache_manager.alloc_tensor(shape, dtype, device=device, is_graph_out=False)
            else:
                out = torch.empty(shape, dtype=dtype, device=device)
        if self.bias is None:
            return torch.mm(input_tensor, self.weight, out=out)
        return torch.addmm(self.bias, input_tensor, self.weight, out=out)

    def verify_load(self) -> bool:
        load_ok = True
        # Verify weight. The weight must be not None.
        load_ok = load_ok and self.weight is not None
        # Verify bias. If bias_name is set, it must be not None.
        if self.has_bias:
            load_ok = load_ok and self.bias is not None
        if self.quantized_weight:
            load_ok = load_ok and self.weight_scale is not None
        if self.static_activation:
            load_ok = load_ok and self.input_scale is not None
        return load_ok

    def _post_load_weights(self) -> None:
        if self.quant_method is not None:
            if self.quantized_weight:
                if (
                    self.weight is not None
                    and self.weight_scale is not None
                    and (not self.static_activation or self.input_scale is not None)
                ):
                    if self.weight_scale.ndim > 1:
                        self.weight_scale = self.weight_scale.transpose(0, 1).cuda(get_current_device_id())
                    self.weight = [
                        self.weight.cuda(get_current_device_id()).transpose(0, 1),
                        self.weight_scale,
                        self.input_scale,
                    ]
            else:
                self.weight = self.quant_method.quantize(self.weight.to(self.data_type_).cuda(get_current_device_id()))
            return
        # 让 k dim 更连续，大多数split k 算法的算子可能能更快
        self.weight = self.weight.to(self.data_type_).cuda(get_current_device_id()).transpose(0, 1)


class MMWeight(MMWeightTpl):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(data_type)
        self.start = split_n_embed * self.tp_rank_
        self.end = split_n_embed * (self.tp_rank_ + 1)
        self.weight_name = weight_name
        self.bias_name = bias_name
        self.has_bias = bias_name is not None
        self.weight_scale_name, self.act_scale_name = generate_scale_name(
            weight_name, weight_scale_suffix, act_scale_suffix
        )
        self.quantized_weight = self.weight_scale_name is not None
        self.static_activation = self.act_scale_name is not None


class ROWMMWeight(MMWeight):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_name, data_type, split_n_embed, bias_name, weight_scale_suffix, act_scale_suffix)

    def load_hf_weights(self, weights: Dict[str, torch.Tensor]) -> None:
        weight = None
        weight_scale = None
        input_scale = None
        if self.weight_name in weights:
            weight = weights[self.weight_name]
            self.weight = weight[self.start : self.end]
        if self.bias_name in weights:
            bias = weights[self.bias_name].to(self.data_type_)[self.start : self.end]
            self.bias = bias.cuda(get_current_device_id())

        if self.weight_scale_name is not None and self.weight_scale_name in weights:
            block_size = 1
            if self.quant_method is not None:
                if hasattr(self.quant_method, "block_size"):
                    block_size = self.quant_method.block_size

            weight_scale = weights[self.weight_scale_name]
            # per channel or block-wise
            if weight_scale.shape[0] > 1:
                scale_start = (self.start + block_size - 1) // block_size
                scale_end = (self.end + block_size - 1) // block_size
                weight_scale = weight_scale.to(torch.float)[scale_start:scale_end]
            else:
                # per tensor
                weight_scale = weight_scale.to(torch.float)
            self.weight_scale = weight_scale

        if self.act_scale_name is not None and self.act_scale_name in weights:
            input_scale = weights[self.act_scale_name].to(torch.float)
            self.input_scale = input_scale.cuda(get_current_device_id())

        if weight is None and weight_scale is None and input_scale is None:
            return
        self._post_load_weights()
        return


class ROWMMWeightNoTP(ROWMMWeight):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_name, data_type, split_n_embed, bias_name, weight_scale_suffix, act_scale_suffix)
        self.start = 0
        self.end = split_n_embed


class COLMMWeight(MMWeight):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_name, data_type, split_n_embed, bias_name, weight_scale_suffix, act_scale_suffix)

    def load_hf_weights(self, weights: Dict[str, torch.Tensor]) -> None:
        weight = None
        weight_scale = None
        input_scale = None
        if self.weight_name in weights:
            weight = weights[self.weight_name]
            self.weight = weight[:, self.start : self.end]
        if self.bias_name in weights:
            bias = weights[self.bias_name]
            self.bias = (bias / self.world_size_).to(self.data_type_).cuda(get_current_device_id())

        if self.quantized_weight and self.weight_scale_name in weights:
            block_size = 1
            if self.quant_method is not None:
                if hasattr(self.quant_method, "block_size"):
                    block_size = self.quant_method.block_size
            weight_scale = weights[self.weight_scale_name]
            # block-wise
            if weight_scale.ndim >= 2:
                weight_scale = weight_scale[:, self.start // block_size : self.end // block_size].to(torch.float)
            else:
                # per tensor or per-channel
                weight_scale = weight_scale.to(torch.float)
            self.weight_scale = weight_scale

        if self.static_activation and self.act_scale_name in weights:
            input_scale = weights[self.act_scale_name].to(torch.float)
            self.input_scale = input_scale.cuda(get_current_device_id())

        if weight is None and weight_scale is None and input_scale is None:
            return
        self._post_load_weights()
        return


class COLMMWeightNoTp(COLMMWeight):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_name, data_type, split_n_embed, bias_name, weight_scale_suffix, act_scale_suffix)
        self.start = 0
        self.end = split_n_embed


class MultiMMWeight(MMWeightTpl):
    def __init__(
        self,
        weight_names: List[str],
        data_type: torch.dtype,
        split_n_embeds: List[int],
        bias_names: Optional[List[str]] = [],
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(data_type)
        if isinstance(split_n_embeds, int):
            self.split_n_embeds = [split_n_embeds] * len(weight_names)
        else:
            self.split_n_embeds = split_n_embeds

        self.starts = [i * self.tp_rank_ for i in self.split_n_embeds]
        self.ends = [i * (self.tp_rank_ + 1) for i in self.split_n_embeds]
        self.weight_names = weight_names
        self.bias_names = bias_names
        self.weight_scale_names = []
        self.act_scale_names = []
        for weight_name in weight_names:
            weight_scale_name, act_scale_name = generate_scale_name(weight_name, weight_scale_suffix, act_scale_suffix)
            self.weight_scale_names.append(weight_scale_name)
            self.act_scale_names.append(act_scale_name)
            self.quantized_weight = weight_scale_name is not None
            self.static_activation = act_scale_name is not None

        self.weights = [None] * len(self.weight_names)
        self.biases = [None] * len(self.bias_names)
        self.input_scales = [None] * len(self.weight_names)
        self.weight_scales = [None] * len(self.weight_names)
        self.has_bias = all(b is not None for b in self.bias_names) and len(bias_names) > 0


class MultiROWMMWeight(MultiMMWeight):
    def __init__(
        self,
        weight_names: List[str],
        data_type: torch.dtype,
        split_n_embeds: List[int],
        bias_names: Optional[List[str]] = [],
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_names, data_type, split_n_embeds, bias_names, weight_scale_suffix, act_scale_suffix)

    def _fuse(self) -> None:
        if self.weight is None and (None not in self.weights):
            self.weight = torch.cat(self.weights, dim=0)
            self._post_load_weights()
            delattr(self, "weights")

        if self.weight_scale is None and (None not in self.weight_scales):
            self.weight_scale = torch.cat(self.weight_scales, dim=0).cuda(get_current_device_id())
            self._post_load_weights()
            delattr(self, "weight_scales")

        if self.static_activation and self.input_scale is None and (None not in self.input_scales):
            input_scales = torch.stack(self.input_scales, dim=0)
            self.input_scale = torch.max(input_scales).cuda(get_current_device_id())
            self._post_load_weights()
            delattr(self, "input_scales")

        if self.has_bias:
            if self.bias is None and (None not in self.biases):
                self.bias = torch.cat(self.biases, dim=0).cuda(get_current_device_id())
                delattr(self, "biases")
        return self

    def load_hf_weights(self, weights: Dict[str, torch.Tensor]) -> None:
        weight = None
        for i in range(len(self.weight_names)):
            if self.weight_names[i] in weights:
                weight = weights[self.weight_names[i]]
                self.weights[i] = weight[self.starts[i] : self.ends[i]]
            if self.has_bias and self.bias_names[i] in weights:
                bias = weights[self.bias_names[i]].to(self.data_type_)
                self.biases[i] = bias[self.starts[i] : self.ends[i]]
            if self.quantized_weight and self.weight_scale_names[i] in weights:
                block_size = 1
                if self.quant_method is not None:
                    if hasattr(self.quant_method, "block_size"):
                        block_size = self.quant_method.block_size
                weight_scale = weights[self.weight_scale_names[i]]
                # block-wise or per-channel
                if weight_scale.shape[0] > 1:
                    weight_scale = weight_scale[self.starts[i] // block_size : self.ends[i] // block_size].to(
                        torch.float
                    )
                else:
                    # per tensor
                    weight_scale = weight_scale.to(torch.float)
                self.weight_scales[i] = weight_scale
            if self.static_activation and self.act_scale_names[i] in weights:
                input_scale = weights[self.act_scale_names[i]].to(torch.float)
                self.input_scales[i] = input_scale
        self._fuse()
        return


class MultiROWMMWeightNoTP(MultiROWMMWeight):
    def __init__(
        self,
        weight_names: List[str],
        data_type: torch.dtype,
        split_n_embeds: List[int],
        bias_names: Optional[List[str]] = [],
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_names, data_type, split_n_embeds, bias_names, weight_scale_suffix, act_scale_suffix)
        self.starts = [0 for i in self.split_n_embeds]
        self.ends = [i for i in self.split_n_embeds]


class MultiCOLMMWeight(MultiROWMMWeight):
    def __init__(
        self,
        weight_names: List[str],
        data_type: torch.dtype,
        split_n_embeds: List[int],
        bias_names: Optional[List[str]] = [],
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_names, data_type, split_n_embeds, bias_names, weight_scale_suffix, act_scale_suffix)

    def load_hf_weights(self, weights: Dict[str, torch.Tensor]) -> None:
        weight = None
        for i in range(len(self.weight_names)):
            if self.weight_names[i] in weights:
                weight = weights[self.weight_names[i]]
                self.weights[i] = weight[:, self.starts[i] : self.ends[i]]
            if self.has_bias and self.bias_names[i] in weights:
                bias = weights[self.bias_names[i]].to(self.data_type_)
                self.biases[i] = bias[:, self.starts[i] : self.ends[i]]
            if self.quantized_weight and self.weight_scale_names[i] in weights:
                weight_scale = weights[self.weight_scale_names[i]]
                self.weight_scales[i] = weight_scale.to(torch.float)
            if self.static_activation and self.act_scale_names[i] in weights:
                input_scale = weights[self.act_scale_names[i]].to(torch.float)
                self.input_scales[i] = input_scale
        self._fuse()
        return


class MultiCOLMMWeightNoTp(MultiROWMMWeightNoTP):
    def __init__(
        self,
        weight_names: List[str],
        data_type: torch.dtype,
        split_n_embeds: List[int],
        bias_names: Optional[List[str]] = [],
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_names, data_type, split_n_embeds, bias_names, weight_scale_suffix, act_scale_suffix)

    def load_hf_weights(self, weights: Dict[str, torch.Tensor]):
        weight = None
        for i in range(len(self.weight_names)):
            if self.weight_names[i] in weights:
                weight = weights[self.weight_names[i]].to(self.data_type_)
                self.weights[i] = weight[:, self.starts[i] : self.ends[i]]
            if self.has_bias and self.bias_names[i] in weights:
                bias = weights[self.bias_names[i]].to(self.data_type_)
                self.biases[i] = bias[:, self.starts[i] : self.ends[i]]
        self._fuse()
        return


class BMMWeightTpl(MMWeightTpl):
    def __init__(self, data_type: torch.dtype):
        super().__init__(data_type)

    def set_quant_method(self, quant_method: QuantizationMethod) -> None:
        if self.quantized_weight:
            # for the quantized fp8 weight of Deepseek v3
            self.quant_method = quant_method

    def bmm(
        self, input_tensor: torch.Tensor, out: Optional[torch.Tensor] = None, use_custom_tensor_mananger: bool = True
    ) -> torch.Tensor:
        if self.quant_method is not None:
            fpweight = self.dequant_weight(self.weight[0], self.weight[1])
        else:
            fpweight = self.weight
        if out is None:
            shape = (input_tensor.shape[0], input_tensor.shape[1], fpweight.shape[2])
            dtype = input_tensor.dtype
            device = input_tensor.device
            if use_custom_tensor_mananger:
                out = g_cache_manager.alloc_tensor(shape, dtype, device=device, is_graph_out=False)
            else:
                out = torch.empty(shape, dtype=dtype, device=device)
        if self.bias is None:
            return torch.bmm(input_tensor, fpweight, out=out)
        return torch.addbmm(self.bias, input_tensor, fpweight, out=out)

    def _post_load_weights(self) -> None:
        if self.quant_method is not None:
            if self.quantized_weight:
                if (
                    self.weight is not None
                    and self.weight_scale is not None
                    and (not self.static_activation or self.input_scale is not None)
                ):
                    if self.weight_scale.ndim > 1:
                        self.weight_scale = self.weight_scale.cuda(get_current_device_id())
                    self.weight = [self.weight.cuda(get_current_device_id()), self.weight_scale, self.input_scale]
            return
        self.weight = self.weight.cuda(get_current_device_id())


class BMMWeight(BMMWeightTpl):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(data_type)
        self.start = split_n_embed * self.tp_rank_
        self.end = split_n_embed * (self.tp_rank_ + 1)
        self.weight_name = weight_name
        self.bias_name = bias_name
        self.weight_scale_name, self.act_scale_name = generate_scale_name(
            weight_name, weight_scale_suffix, act_scale_suffix
        )
        self.quantized_weight = self.weight_scale_name is not None
        self.static_activation = self.act_scale_name is not None

    def verify_load(self) -> None:
        load_ok = True
        # Verify weight. The weight must be not None.
        load_ok = load_ok and self.weight is not None
        # Verify bias. If bias_name is set, it must be not None.
        if self.bias_name is not None:
            load_ok = load_ok and self.bias is not None
        return load_ok


class ROWBMMWeight(BMMWeight):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_name, data_type, split_n_embed, bias_name, weight_scale_suffix, act_scale_suffix)

    def dequant_weight(self, weight: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
        # for Deepseek v3
        # TODO a fast bmm quant kernel
        weight = weight.to(self.data_type_)
        block_size = weight.shape[-1] // scale.shape[-1]
        w_shape = weight.shape
        s_shape = scale.shape
        scale = scale.unsqueeze(-1).repeat(1, 1, 1, block_size).reshape(s_shape[0], s_shape[1], -1)
        scale = scale.unsqueeze(2).repeat(1, 1, block_size, 1).reshape(w_shape)
        return (weight * scale).to(self.data_type_)

    def load_hf_weights(self, weights: Dict[str, torch.Tensor]) -> None:
        weight = None
        weight_scale = None
        input_scale = None
        if self.weight_name in weights:
            weight = weights[self.weight_name]
            self.weight = weight[self.start : self.end]
        if self.bias_name in weights:
            bias = weights[self.bias_name].to(self.data_type_)[self.start : self.end]
            self.bias = bias.cuda(get_current_device_id())

        if self.weight_scale_name is not None and self.weight_scale_name in weights:
            weight_scale = weights[self.weight_scale_name]
            # per channel or block-wise
            if weight_scale.shape[0] > 1:
                weight_scale = weight_scale.to(torch.float)[self.start : self.end]
            else:
                # per tensor
                weight_scale = weight_scale.to(torch.float)
            self.weight_scale = weight_scale

        if self.act_scale_name is not None and self.act_scale_name in weights:
            input_scale = weights[self.act_scale_name].to(torch.float)
            self.input_scale = input_scale.cuda(get_current_device_id())

        if weight is None and weight_scale is None and input_scale is None:
            return
        self._post_load_weights()
        return


class ROWBMMWeightNoTp(ROWBMMWeight):
    def __init__(
        self,
        weight_name: str,
        data_type: torch.dtype,
        split_n_embed: int,
        bias_name: Optional[str] = None,
        weight_scale_suffix: Optional[str] = None,
        act_scale_suffix: Optional[str] = None,
    ) -> None:
        super().__init__(weight_name, data_type, split_n_embed, bias_name, weight_scale_suffix, act_scale_suffix)
        self.start = 0
        self.end = split_n_embed
