import os
import shutil
import threading
import time
import torch

from lightllm.utils.infer_utils import calculate_time, mark_start, mark_end
from lightllm.server.io_struct import FinishStatus
from lightllm.server.router.model_infer.infer_batch import (
    DPDAStructure,
    InferBatch,
    InferReq,
    InferSamplingParams,
)
from lightllm.server.tokenizer import get_tokenizer
from typing import List
from lightllm.utils.log_utils import init_logger

from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.core import (
    compute_first,
    compute_graph,
    Graph,
    NT,
    T,
)
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.dpda import LRGraph, DPDA
from lightllm_constraint_decode_kernel import check_dpda, batched_check_dpda

current_stack = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/current_stack.pt").cuda()
current_stack_top = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/current_stack_top.pt").cuda()
current_state = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/current_state.pt").cuda()
input_sequences = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/input_sequences.pt").cuda()
sequence_len = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/sequence_len.pt").cuda()
shift_table = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/shift_table.pt").cuda()
edge_num_table = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/edge_num_table.pt").cuda()
push_table = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/push_table.pt").cuda()
pop_table = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/pop_table.pt").cuda()
dest_table = torch.load("/mnt/nvme0/chenjunyi/project/lightllm/tmp/dest_table.pt").cuda()

vocab_size = input_sequences.shape[0]
output = torch.empty((16 * vocab_size), dtype=torch.int32, device="cuda")
# current_state = torch.tensor([current_state[0]] * 8, dtype=torch.int32, device="cuda")
max_stack_depth = current_stack.shape[1]

# print a list of all tensor shape
print(
    f"current_stack: {current_stack.shape}, current_stack_top: {current_stack_top.shape}, \
      current_state: {current_state.shape}, input_sequences: {input_sequences.shape}, sequence_len: {sequence_len.shape}, \
      shift_table: {shift_table.shape}, edge_num_table: {edge_num_table.shape}, push_table: {push_table.shape}, \
      pop_table: {pop_table.shape}, dest_table: {dest_table.shape}, output: {output.shape}"
)

batched_check_dpda(
    input_sequences,
    sequence_len,
    shift_table,
    edge_num_table,
    push_table,
    pop_table,
    dest_table,
    current_stack,
    current_stack_top,
    current_state,
    output,
    max_stack_depth,
)
print(current_stack)
print(current_state)
print(current_stack_top)
print(output)
