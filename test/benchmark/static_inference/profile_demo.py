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
    a = torch.cat([draft_probs_tensor for _ in range(100)], dim=0)  # Simulating a workload by concatenating the tensor multiple times
    b = torch.stack([draft_probs_tensor for _ in range(100)], dim=0)  # Simulating another workload by stacking the tensor multiple times
    pass

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=100))
