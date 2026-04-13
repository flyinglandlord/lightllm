import torch
import numpy as np
from torch.profiler import profile, record_function, ProfilerActivity

draft_probs_tensor = torch.rand(10, 4).cuda()  # Simulating draft probabilities for 10 steps and batch size of 4
torch.cuda.synchronize()
with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    record_shapes=False,
    profile_memory=False,
    on_trace_ready=torch.profiler.tensorboard_trace_handler("./log/"),
) as prof:
    rand_vals = torch.rand_like(draft_probs_tensor)
    accepted_mask = draft_probs_tensor > rand_vals
    valid_steps = torch.cumprod(accepted_mask.to(torch.int32), dim=0)
    dynamic_mtp_sizes = valid_steps.sum(dim=0)
    pass

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))
