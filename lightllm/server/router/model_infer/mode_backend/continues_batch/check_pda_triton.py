import time
import torch
import triton
import triton.language as tl

from format_out.grammar.core import compute_first, compute_graph
from format_out.grammar.dpda import NT, LRGraph, Graph, DPDA
from format_out.grammar.dpda import T
from format_out.grammar.example_grammar import json_grammar

from transformers import AutoTokenizer

import pdb

# PDA Kernel: 每个线程处理一个输入序列
@triton.jit
def pda_kernel(
    input_ptr,  # [num_vocab, max_sequence_len]
    sequence_len_ptr,  # [num_vocab]
    state_ptr,  # [num_vocab]
    shift_table,  # [node_num, symbol_num, max_edge_num_for_same_t]
    shift_table_stride_0,
    shift_table_stride_1,
    shift_table_stride_2,
    edge_num_table,  # [node_num, symbol_num]
    edge_num_stride_0,
    edge_num_stride_1,
    push_table,  # [edge_num, max_push_len]
    push_table_stride_0,
    push_table_stride_1,
    pop_table,  # [edge_num, max_pop_len]
    pop_table_stride_0,
    pop_table_stride_1,
    dest_table,  # [edge_num]
    stack_ptr,  # [num_vocab, stack_depth]
    stack_top_ptr,  # [num_vocab]
    stack_depth: tl.constexpr,  # 最大的栈深度
    max_pop_len: tl.constexpr,
    max_push_len: tl.constexpr,
):
    seq_idx = tl.program_id(0)  # 每个线程处理不同的输入序列
    cur_state = tl.load(state_ptr + seq_idx).to(tl.int32)  # 初始状态

    stack_ptr_local = stack_ptr + seq_idx * stack_depth  # 每个序列对应一个栈
    stack_top_ptr = stack_top_ptr + seq_idx
    stack_top_local = tl.load(stack_top_ptr)  # 栈顶指针
    sequence_len = tl.load(sequence_len_ptr + seq_idx)  # 输入序列长度

    # 遍历输入序列
    for i in range(sequence_len):
        # 获取当前输入符号
        input_symbol = tl.load(input_ptr + seq_idx * sequence_len + i)
        # pdb.set_trace()
        # loop_end = tl.where(cur_state == -1, 0, 1)
        if cur_state != -1:
            # 获取当前状态在当前输入符号下的转移边list
            edge_num = tl.load(edge_num_table + cur_state * edge_num_stride_0 + input_symbol * edge_num_stride_1)
            edge_list_ptr = shift_table + cur_state * shift_table_stride_0 + input_symbol * shift_table_stride_1
            # pdb.set_trace()
            # 遍历当前状态下的所有转移边，匹配pop与当前栈顶元素
            match = False
            # pdb.set_trace()
            for edge_idx in range(edge_num):
                # pdb.set_trace()
                edge = tl.load(edge_list_ptr + edge_idx * shift_table_stride_2)
                push_list_ptr = push_table + edge * push_table_stride_0
                pop_list_ptr = pop_table + edge * pop_table_stride_0
                dest_state = tl.load(dest_table + edge).to(tl.int32)

                # 从栈顶开始匹配pop_list
                pop_list_idx = tl.arange(0, max_pop_len)
                pop_list = tl.load(pop_list_ptr + pop_list_idx, mask=pop_list_idx <= pop_table_stride_0, other=-1)
                stack_idx = stack_top_local - 1 - pop_list_idx
                stack_slice = tl.load(stack_ptr_local + stack_idx, mask=stack_idx > -stack_top_local, other=-1)

                check = tl.sum(tl.where((pop_list == stack_slice) | (pop_list == -1), 0, 1))
                if check == 0 and match is False:
                    # 匹配成功，更新状态和栈
                    cur_state = dest_state
                    # pdb.set_trace()
                    # pop the stack
                    valid_pop = tl.where(pop_list != -1, 1, 0)
                    pop_len = tl.sum(valid_pop, axis=0)
                    stack_top_local -= pop_len
                    # pdb.set_trace()
                    # push the stack
                    push_list_idx = tl.arange(0, max_push_len)
                    push_list = tl.load(
                        push_list_ptr + push_list_idx, mask=push_list_idx <= push_table_stride_1, other=-1
                    )
                    valid_push = tl.where(push_list != -1, 1, 0)
                    tl.store(stack_ptr_local + stack_top_local + push_list_idx, push_list, mask=push_list != -1)
                    push_len = tl.sum(valid_push, axis=0)
                    stack_top_local += push_len
                    # pdb.set_trace()
                    match = True

            cur_state = tl.where(match is False, -1, cur_state)

    # 存储最后的状态和栈指针
    tl.store(stack_top_ptr + seq_idx, stack_top_local)
    tl.store(state_ptr + seq_idx, cur_state)


def pda_sequence_processing(
    input_sequences,  # a tensor of [num_vocab, max_sequence_len]
    sequence_len,  # a tensor of [num_vocab]
    shift_table,
    edge_num_table,
    push_table,
    pop_table,
    dest_table,
    current_stack,  # a list for current stack
    start_state,  # a number for current state
    stack_depth=100,
):
    num_sequences = input_sequences.shape[0]
    # 初始化输入输出
    input_tensor = torch.tensor(input_sequences, dtype=torch.int32, device="cuda")
    state_tensor = torch.tensor([start_state] * input_tensor.shape[0], dtype=torch.int32, device="cuda")

    # 初始化栈
    stack_depth = max(triton.next_power_of_2(stack_depth), triton.next_power_of_2(len(current_stack)))
    stack_tensor = torch.zeros((num_sequences, stack_depth), dtype=torch.int32, device="cuda")  # 每个序列一个栈
    stack_top_tensor = torch.zeros(num_sequences, dtype=torch.int32, device="cuda")  # 栈顶指针

    # 将curent_stack中的元素放入栈中
    for i in range(len(current_stack)):
        stack_tensor[:, i] = current_stack[i]
        stack_top_tensor += 1

    max_pop_len = triton.next_power_of_2(pop_table.shape[1])
    max_push_len = triton.next_power_of_2(push_table.shape[1])
    start_time = time.time()
    # 启动 Triton kernel 并行处理多个序列的状态转换
    grid = (num_sequences,)  # 每个线程处理一个输入序列
    pda_kernel[grid](
        input_tensor,  # [num_vocab, max_sequence_len]
        sequence_len,  # [num_vocab]
        state_tensor,  # [num_vocab]
        shift_table,  # [node_num, symbol_num, max_edge_num_for_same_t]
        shift_table.stride(0),
        shift_table.stride(1),
        shift_table.stride(2),
        edge_num_table,  # [node_num, symbol_num]
        edge_num_table.stride(0),
        edge_num_table.stride(1),
        push_table,  # [edge_num, max_push_len]
        push_table.stride(0),
        push_table.stride(1),
        pop_table,  # [edge_num, max_pop_len]
        pop_table.stride(0),
        pop_table.stride(1),
        dest_table,  # [edge_num]
        stack_tensor,  # [num_vocab, stack_depth]
        stack_top_tensor,  # [num_vocab]
        stack_depth,  # 最大的栈深度
        max_pop_len,
        max_push_len,
    )
    end_time = time.time()
    print(f"Triton Elapsed time: {end_time - start_time:.4f}s")

    return state_tensor.cpu().numpy()


# 测试：构建下推自动机并并行处理多个输入序列
if __name__ == "__main__":
    # 先构建一个文法，测试dump_to_tensor是否正确
    grammar = json_grammar
    # ans = compute_first(grammar)
    graph = compute_graph(grammar=grammar, start_symbol="JSON")
    graph.check_lr1()
    lr_graph = LRGraph(graph)
    dpda = DPDA(lr_graph=lr_graph)

    shift_table, edge_num_table, push_table, pop_table, dest_table, symbol_to_id = dpda.dump_to_tensor()
    print(shift_table.shape)
    print(shift_table, edge_num_table, push_table, pop_table, dest_table, symbol_to_id, sep="\n")

    tokenizer = AutoTokenizer.from_pretrained("/data/chenjunyi/models/qwen2-7b-chat")

    check_str = tokenizer.get_vocab().keys()
    # print(check_str)

    other_token_id = max(symbol_to_id.values()) + 1

    char_sequences = []
    sequence_len = []
    for s in check_str:
        char_sequences.append([symbol_to_id[c] if c in symbol_to_id else other_token_id for c in s])
        sequence_len.append(len(s))
    sequence_len = torch.tensor(sequence_len, dtype=torch.int32, device="cuda")
    input_sequences = torch.empty((len(char_sequences), torch.max(sequence_len)), dtype=torch.int32, device="cuda")
    for i, s in enumerate(char_sequences):
        input_sequences[i, : len(s)] = torch.tensor(s, dtype=torch.int32, device="cuda")
    print(input_sequences)
    current_state = 0
    current_stack = [0]

    result = pda_sequence_processing(
        input_sequences,
        sequence_len,
        shift_table,
        edge_num_table,
        push_table,
        pop_table,
        dest_table,
        current_stack,
        current_state,
        stack_depth=50,
    )

    start_time = time.time()
    for i, str in enumerate(check_str):
        dpda.try_shift(str, [0], 0)
    end_time = time.time()
    print(f"Python Elapsed time: {end_time - start_time:.4f}s")

    for i, str in enumerate(check_str):
        if result[i] != -1:
            print(f"Accepted: {str}")
