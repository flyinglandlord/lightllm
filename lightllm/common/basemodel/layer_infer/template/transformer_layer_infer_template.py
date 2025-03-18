import os
import torch
import torch.distributed as dist
from ..transformer_layer_infer import TransformerLayerInfer
from ...infer_struct import InferStateInfo
from lightllm.utils.infer_utils import mark_cost_time
from lightllm.common.basemodel.triton_kernel.destindex_copy_kv import destindex_copy_kv
from typing import Tuple


class TransformerLayerInferTpl(TransformerLayerInfer):
    """ """

    def __init__(self, layer_num, tp_rank, world_size, network_config, mode):
        super().__init__(layer_num, tp_rank, world_size, network_config, mode)
        # need to set by subclass
        self.eps_ = 1e-5
        self.tp_q_head_num_ = -1
        self.tp_k_head_num_ = -1
        self.tp_v_head_num_ = -1
        self.tp_o_head_num_ = -1
        self.head_dim_ = -1
        self.embed_dim_ = -1
        self.enable_dp = os.getenv("ENABLE_DP", "0").upper() in ["ON", "TRUE", "1"]
        self.enable_flux = os.getenv("ENABLE_FLUX", "0").upper() in ["ON", "TRUE", "1"]
        return

    def _att_norm(self, input, infer_state: InferStateInfo, layer_weight) -> torch.Tensor:
        raise Exception("need to impl")

    def _ffn_norm(self, input, infer_state: InferStateInfo, layer_weight) -> torch.Tensor:
        raise Exception("need to impl")

    def _pre_cache_kv(self, infer_state: InferStateInfo, layer_weight) -> Tuple[torch.Tensor, torch.Tensor]:
        if infer_state.mem_is_contiguous:
            cache_kv = infer_state.mem_manager.kv_buffer[self.layer_num_][
                infer_state.mem_start : infer_state.mem_end, :, :
            ]
        else:
            cache_kv = infer_state.kv_buffer
        return cache_kv

    def _get_qkv(
        self, input, cache_kv, infer_state: InferStateInfo, layer_weight
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        raise Exception("need to impl")

    def _post_cache_kv(self, cache_kv, infer_state: InferStateInfo, layer_weight):
        mem_manager = infer_state.mem_manager
        if not infer_state.mem_is_contiguous:
            self._copy_kv_to_mem_cache(cache_kv, infer_state.mem_index, mem_manager)
            return

    def _copy_kv_to_mem_cache(self, buffer, mem_index, mem_manager):
        destindex_copy_kv(buffer, mem_index, mem_manager.kv_buffer[self.layer_num_])
        return

    def _context_attention_kernel(self, q, kv, infer_state: InferStateInfo, layer_weight, out=None) -> torch.Tensor:
        raise Exception("need to impl")

    def _token_attention_kernel(self, q, infer_state: InferStateInfo, layer_weight, out=None) -> torch.Tensor:
        raise Exception("need to impl")

    def _get_o(self, input, infer_state: InferStateInfo, layer_weight) -> torch.Tensor:
        raise Exception("need to impl")

    def _ffn(self, input, infer_state: InferStateInfo, layer_weight) -> torch.Tensor:
        raise Exception("need to impl")

    def _context_attention(self, input_embding, infer_state: InferStateInfo, layer_weight):
        input1 = self._att_norm(input_embding, infer_state, layer_weight)
        cache_kv = self._pre_cache_kv(infer_state, layer_weight)
        q, cache_kv = self._get_qkv(input1, cache_kv, infer_state, layer_weight)
        input1 = None
        self._post_cache_kv(cache_kv, infer_state, layer_weight)
        o = self._context_attention_kernel(q, cache_kv, infer_state, layer_weight)
        q = None
        o = self._get_o(o, infer_state, layer_weight)
        if self.world_size_ > 1 and not self.enable_dp:
            dist.all_reduce(o, op=dist.ReduceOp.SUM, async_op=False)
        elif self.enable_flux:
            torch.distributed.reduce_scatter_tensor(o, o, group=dist.group.WORLD)
        input_embding.add_(o.view(-1, self.embed_dim_))
        return

    def _context_ffn(self, input_embdings, infer_state: InferStateInfo, layer_weight):
        input1 = self._ffn_norm(input_embdings, infer_state, layer_weight)
        ffn_out = self._ffn(input1, infer_state, layer_weight)
        input1 = None
        if self.world_size_ > 1 and not self.enable_dp:
            if (
                not self.enable_flux
                or self.layer_num_ == self.network_config_["num_hidden_layers"] - 1
                or ffn_out.size(0) == 1
            ):
                dist.all_reduce(ffn_out, op=dist.ReduceOp.SUM, async_op=False)
            # else:
            #     split_M = ffn_out.size(0)
            #     tp_M_start_index = split_M * self.tp_rank_
            #     tp_M_end_index = split_M * (self.tp_rank_ + 1)
            #     if tp_M_end_index > input_embdings.size(0):
            #         tp_M_end_index = input_embdings.size(0)
            #     input_embdings[tp_M_start_index:tp_M_end_index, :] = ffn_out[:tp_M_end_index - tp_M_start_index, :]
            #     return
        input_embdings.add_(ffn_out.view(-1, self.embed_dim_))
        return

    def _token_attention(self, input_embding, infer_state: InferStateInfo, layer_weight):
        input1 = self._att_norm(input_embding, infer_state, layer_weight)
        cache_kv = self._pre_cache_kv(infer_state, layer_weight)
        q, cache_kv = self._get_qkv(input1, cache_kv, infer_state, layer_weight)
        input1 = None
        self._post_cache_kv(cache_kv, infer_state, layer_weight)
        o = self._token_attention_kernel(q, infer_state, layer_weight)
        q = None
        o = self._get_o(o, infer_state, layer_weight)
        if self.world_size_ > 1 and not self.enable_dp:
            dist.all_reduce(o, op=dist.ReduceOp.SUM, async_op=False)
        input_embding.add_(o.view(-1, self.embed_dim_))
        return

    def _token_ffn(self, input_embdings, infer_state: InferStateInfo, layer_weight):
        input1 = self._ffn_norm(input_embdings, infer_state, layer_weight)
        ffn_out = self._ffn(input1, infer_state, layer_weight)
        input1 = None
        if self.world_size_ > 1 and not self.enable_dp:
            if (
                not self.enable_flux
                or self.layer_num_ == self.network_config_["num_hidden_layers"] - 1
                or ffn_out.size(0) == 1
            ):
                dist.all_reduce(ffn_out, op=dist.ReduceOp.SUM, async_op=False)
            # else:
            #     split_M = ffn_out.size(0)
            #     tp_M_start_index = split_M * self.tp_rank_
            #     tp_M_end_index = split_M * (self.tp_rank_ + 1)
            #     if tp_M_end_index > input_embdings.size(0):
            #         tp_M_end_index = input_embdings.size(0)
            #     input_embdings[tp_M_start_index:tp_M_end_index, :] = ffn_out[:tp_M_end_index - tp_M_start_index, :]
            #     return
        input_embdings.add_(ffn_out.view(-1, self.embed_dim_))
        return

    def context_forward(self, input_embdings, infer_state: InferStateInfo, layer_weight):
        self._context_attention(input_embdings, infer_state, layer_weight=layer_weight)
        if self.enable_flux and self.layer_num_ != 0 and input_embdings.size(0) > 1:
            padded_input = None
            if input_embdings.size(0) % self.world_size_ != 0:
                pad_size = (self.world_size_ - input_embdings.size(0) % self.world_size_) % self.world_size_
                pad_tensor = torch.zeros(
                    pad_size, input_embdings.size(1), dtype=input_embdings.dtype, device=input_embdings.device
                )
                padded_input = torch.cat([input_embdings, pad_tensor], dim=0)
            else:
                padded_input = input_embdings

            full_input = torch.empty_like(padded_input)
            local_M_size = padded_input.size(0) // self.world_size_
            local_M_start_index = local_M_size * self.tp_rank_
            local_M_end_index = local_M_size * (self.tp_rank_ + 1)
            torch.distributed.all_gather_into_tensor(
                full_input, padded_input[local_M_start_index:local_M_end_index], group=torch.distributed.group.WORLD
            )
            input_embdings = full_input[: input_embdings.size(0)]
        # if self.layer_num_ <= 1:
        #     torch.save(input_embdings, f"tmp/output_te_kernel_{self.tp_rank_}_{self.layer_num_}.pt")
        self._context_ffn(input_embdings, infer_state, layer_weight)
        return input_embdings

    def token_forward(self, input_embdings, infer_state: InferStateInfo, layer_weight):
        self._token_attention(input_embdings, infer_state, layer_weight=layer_weight)
        if self.enable_flux and self.layer_num_ != 0 and input_embdings.size(0) > 1:
            padded_input = None
            if input_embdings.size(0) % self.world_size_ != 0:
                pad_size = (self.world_size_ - input_embdings.size(0) % self.world_size_) % self.world_size_
                pad_tensor = torch.zeros(
                    pad_size, input_embdings.size(1), dtype=input_embdings.dtype, device=input_embdings.device
                )
                padded_input = torch.cat([input_embdings, pad_tensor], dim=0)
            else:
                padded_input = input_embdings

            full_input = torch.empty_like(padded_input)
            local_M_size = padded_input.size(0) // self.world_size_
            local_M_start_index = local_M_size * self.tp_rank_
            local_M_end_index = local_M_size * (self.tp_rank_ + 1)
            torch.distributed.all_gather_into_tensor(
                full_input, padded_input[local_M_start_index:local_M_end_index], group=torch.distributed.group.WORLD
            )
            input_embdings = full_input[: input_embdings.size(0)]
        self._token_ffn(input_embdings, infer_state, layer_weight)
        return input_embdings
