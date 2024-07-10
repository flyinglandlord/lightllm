import os
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
    
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

if __name__ == "__main__":
    quantizer_module = op_builder.QuantizerBuilder().load()
    
    tensor = torch.randn(8, 4096).cuda()
    print(tensor)
    intra_quant_int4, intra_q_scales = quantizer_module.swizzle_quant(tensor, 4096, 4,
                                quantizer_module.Symmetric, 1, 1,
                                8)
    x = intra_quant_int4[0]
    print(x)
    print(intra_quant_int4)
    print(intra_q_scales)
    #torch.cuda.synchronize()

    local_output = intra_quant_int4
    scale_output = intra_q_scales

    global_input_tensor, global_scales = quantizer_module.quantized_reduction(
                local_output, scale_output, 4096, 4096//8, 4, quantizer_module.Symmetric,
                8)

    print(global_input_tensor)
    print(global_scales)
    #torch.cuda.synchronize()

    final_output = quantizer_module.dequantize(global_input_tensor, global_scales, global_scales.numel(),
                                                       4, quantizer_module.Symmetric)
    print(final_output)
    #torch.cuda.synchronize()