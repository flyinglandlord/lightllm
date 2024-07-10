import math
from typing import List
import torch
from torch import Tensor
from torch import distributed as dist
from torch.distributed import ProcessGroup, all_to_all_single
from deepspeed.accelerator import get_accelerator
from deepspeed.utils import instrument_w_nvtx
from deepspeed.ops import op_builder
from deepspeed.utils import logger


def _torch_reduce_scatter_fn(input_tensor: Tensor, output_tensor: Tensor, group=None, async_op=False, prof=False):
    return instrument_w_nvtx(dist.reduce_scatter_fn)(output_tensor, input_tensor, group=group, async_op=False)

quantizer_module = None

def all_to_all_quant_reduce(tensors: List[Tensor], groups: {}) -> List[Tensor]: # type: ignore
    global quantizer_module
    if quantizer_module is None:
        quantizer_module = op_builder.QuantizerBuilder().load()
    global_world_size = dist.get_world_size()
    num_nodes = 1
    this_rank = dist.get_rank()
    output_lst: List[Tensor] = [None] * len(tensors)
    for idx, tensor in enumerate(tensors):
        """
        current_size = tensor.shape[0]
        padding_size = (8 - current_size % 8) % 8
        padding_tensor = tensor[:padding_size, :]
        tensor = torch.cat((tensor, padding_tensor), dim=0)
        """
        old_shape = tensor.shape
        tensor = tensor.view(-1, 16)

        intra_quant_group = max(tensor.shape[0], tensor.shape[1], global_world_size)

        inter_quant_group = intra_quant_group // global_world_size
        intra_quant_int4, intra_q_scales = quantizer_module.swizzle_quant(tensor, intra_quant_group, 4,
                                                                            quantizer_module.Symmetric, 1, num_nodes,
                                                                            global_world_size)
        #if this_rank == 0: print(intra_quant_int4.shape, intra_q_scales.shape, tensor.shape)
        #print(f'{this_rank}: finish quant stage 1')
        #print(intra_quant_int4.dtype)
        local_output = torch.empty_like(intra_quant_int4)
        scale_output = torch.empty_like(intra_q_scales)
        all_to_all_single(local_output, intra_quant_int4)
        all_to_all_single(scale_output, intra_q_scales)
        #print(f'{this_rank}: finish all_to_all_single')
        
        global_input_tensor, global_scales = quantizer_module.quantized_reduction(
            local_output, scale_output, intra_quant_group, inter_quant_group, 4, quantizer_module.Symmetric,
            global_world_size)
        #print(f'{this_rank}: finish quant stage 2')

        #if this_rank == 0: print(global_input_tensor.shape, global_scales.shape, tensor.shape)
        final_output = quantizer_module.dequantize(global_input_tensor, global_scales, global_scales.numel(),
                                                    4, quantizer_module.Symmetric)
        #print(f'{this_rank}: finish quant stage 3')
        #if this_rank == 0: print(final_output.shape, tensor.shape)
        #print(final_output)

        output_lst[idx] = torch.zeros_like(tensor, dtype=final_output.dtype).view(-1)
        dist.all_gather_into_tensor(output_lst[idx], final_output)
        output_lst[idx] = output_lst[idx].reshape(old_shape)
        """
        global_output = torch.empty_like(global_input_tensor)
        global_scale_output = torch.empty_like(global_scales)
        all_to_all_single(global_output, global_input_tensor, group=None)
        all_to_all_single(global_scale_output, global_scales, group=None)
        final_output = quantizer_module.dequantize(global_output, global_scale_output, global_scale_output.numel(),
                                                    8, quantizer_module.Symmetric)
        print('finish quant stage 3')
        assert final_output.numel(
        ) % num_nodes == 0, f"final_output.numel()={final_output.numel()} is not divisible by num_nodes={num_nodes}"
        """
        #output_lst[idx] = final_output
    return output_lst


def reduce_scatter_coalesced(
    tensors: List[Tensor],
    group: ProcessGroup = None,
) -> List[Tensor]:
    """simultaneously reduce-scatter a list of tensors - this can be done more
    efficiently than individual reduce scatter calls
    TODO. see if PyTorch team wants a c++ version of this for ProcessGroupNCCL
    """
    this_rank = dist.get_rank(group)
    world_sz = dist.get_world_size(group)

    partition_lst_for_each_tensor = [None] * len(tensors)
    for tensor_idx, tensor in enumerate(tensors):
        flattened_tensor = tensor.view(-1)
        chunk_sz = math.ceil(tensor.numel() / world_sz)
        partition_lst_for_each_tensor[tensor_idx] = [
            flattened_tensor[rank * chunk_sz:rank * chunk_sz + chunk_sz] for rank in range(0, world_sz)
        ]

    padded_partition_sz_for_each_tensor = tuple(math.ceil(t.numel() / world_sz) for t in tensors)

    if len(tensors) == 1 and tensors[0].numel() % world_sz == 0:
        # if there's only one tensor being reduced and we don't need to pad
        # we have an opportunity to avoid a memory allocation
        tensor_partition_flat_buffer = tensors[0].view(-1)
    else:
        # interleave tensor partitions such that the correct reduced partitions of each tensor
        # end up at each rank
        tensor_partitions_lst_with_padding = []
        for rank in range(world_sz):
            for tensor_idx in range(len(tensors)):
                # add tensor content
                tensor_chunk = partition_lst_for_each_tensor[tensor_idx][rank]
                tensor_partitions_lst_with_padding.append(tensor_chunk)

                # add padding if necessary
                padding_sz = padded_partition_sz_for_each_tensor[tensor_idx] - tensor_chunk.numel()
                if padding_sz > 0:
                    tensor_partitions_lst_with_padding.append(
                        torch.empty(padding_sz, dtype=tensor_chunk.dtype, device=tensor_chunk.device))

        tensor_partition_flat_buffer = instrument_w_nvtx(torch.cat)(tensor_partitions_lst_with_padding)

    tensor_partition_flat_buffer.div_(world_sz)  # pre-divide
    tensor_partition_buffer_for_each_rank: List[Tensor] = torch.chunk(tensor_partition_flat_buffer, world_sz)

    # batched reduce-scatter call
    _torch_reduce_scatter_fn(tensor_partition_flat_buffer,
                             tensor_partition_buffer_for_each_rank[this_rank],
                             group=group)

    # reverse procedure of the interleaving done previously, done on the
    # result of the batched reduce-scatter
    output_lst: List[Tensor] = [None] * len(tensors)
    offset = 0
    for tensor_idx in range(len(tensors)):
        output_lst[tensor_idx] = tensor_partition_buffer_for_each_rank[this_rank].narrow(
            0, offset, partition_lst_for_each_tensor[tensor_idx][this_rank].numel())

        offset += padded_partition_sz_for_each_tensor[tensor_idx]
    return output_lst