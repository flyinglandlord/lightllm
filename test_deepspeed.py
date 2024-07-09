
import torch
import deepspeed
from torch import Tensor
from deepspeed import comm as dist
from typing import Callable, Dict, TYPE_CHECKING, Any, Tuple

class _AllToAll(torch.autograd.Function):
    @staticmethod
    def forward(
            ctx: Any,
            # TODO: replace with DS process group
            group: torch.distributed.ProcessGroup,
            input: Tensor) -> Tensor:  # type: ignore
        ctx.group = group
        input = input.contiguous()
        output = torch.empty_like(input)
        dist.all_to_all_single(output, input)
        return output
 
    @staticmethod
    def backward(ctx: Any, *grad_output: Tensor) -> Tuple[None, Tensor]:
        return (None, _AllToAll.apply(ctx.group, *grad_output))
    
if __name__ == "__main__":
    deepspeed.init_distributed()
    from deepspeed.utils import groups
    expert_group_name = "ep_size_4"
    groups._create_expert_and_data_parallel(4)
    ep = groups._get_expert_parallel_group(expert_group_name)
    rank = torch.distributed.get_rank()
    device_id = rank % torch.cuda.device_count()
    device = torch.device(device_id)
    inputs = torch.randn((4,1,1)).to(device)
    
    for i in range(4):
        if rank==i:
            print("rank:%d,input:"%(rank),inputs)
        torch.distributed.barrier()
    output = _AllToAll.apply(ep,inputs)
    print("rank:%d,output:"%(rank),output)
    torch.distributed.barrier()