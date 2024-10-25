import torch
import triton
import triton.language as tl

# PDA Kernel: 每个线程处理一个输入序列
@triton.jit
def pda_kernel(
    states_ptr,
    stack_ptr,
    stack_top_ptr,
    input_ptr,
    start_state_ptr,
    final_states_ptr,
    output_ptr,
    num_states,
    num_symbols,
    sequence_len,
    stack_depth,
):
    seq_idx = tl.program_id(0)  # 每个线程处理不同的输入序列
    cur_state = tl.load(start_state_ptr)  # 初始状态

    stack_ptr_local = stack_ptr + seq_idx * stack_depth  # 每个序列对应一个栈
    stack_top_local = tl.load(stack_top_ptr + seq_idx)  # 栈顶指针

    # 遍历输入序列
    for i in range(sequence_len):
        # 获取当前输入符号
        input_symbol = tl.load(input_ptr + seq_idx * sequence_len + i)

        # 假设根据状态表获取下一个状态和栈操作 (简化示例)
        # 实际实现中可以通过查找表获取状态转移和栈操作
        if cur_state == 0 and input_symbol == 0:
            next_state = 1  # 状态 0 + 输入 0 -> 转移到状态 1
            stack_op = 1  # 栈操作，入栈
        elif cur_state == 1 and input_symbol == 1:
            next_state = 2  # 状态 1 + 输入 1 -> 转移到状态 2
            stack_op = -1  # 栈操作，出栈
        else:
            next_state = cur_state  # 否则状态保持不变
            stack_op = 0  # 栈保持不变

        # 栈操作
        if stack_op == 1 and stack_top_local < stack_depth - 1:
            # 入栈操作
            stack_top_local += 1
            tl.store(stack_ptr_local + stack_top_local, input_symbol)
        elif stack_op == -1 and stack_top_local >= 0:
            # 出栈操作
            stack_top_local -= 1

        cur_state = next_state

    # 存储最后的状态和栈指针
    tl.store(stack_top_ptr + seq_idx, stack_top_local)
    tl.store(output_ptr + seq_idx, cur_state)


@triton.jit
def check_final_state_kernel(output_ptr, final_states_ptr, result_ptr, num_final_states, num_sequences):
    seq_idx = tl.program_id(0)  # 每个线程处理不同的序列
    cur_state = tl.load(output_ptr + seq_idx)
    accepted = 0

    # 检查当前状态是否为接受状态
    for i in range(num_final_states):
        if cur_state == tl.load(final_states_ptr + i):
            accepted = 1

    tl.store(result_ptr + seq_idx, accepted)


def pda_sequence_processing(states, start_state, final_states, input_sequences, stack_depth=10):
    num_states, num_symbols = states.shape
    num_sequences, sequence_len = input_sequences.shape

    # 初始化输入输出
    input_tensor = torch.tensor(input_sequences, dtype=torch.int32, device="cuda")
    start_state_tensor = torch.tensor([start_state], dtype=torch.int32, device="cuda")
    output_tensor = torch.zeros(num_sequences, dtype=torch.int32, device="cuda")
    final_states_tensor = torch.tensor(final_states, dtype=torch.int32, device="cuda")
    result_tensor = torch.zeros(num_sequences, dtype=torch.int32, device="cuda")

    # 初始化栈
    stack_tensor = torch.zeros((num_sequences, stack_depth), dtype=torch.int32, device="cuda")  # 每个序列一个栈
    stack_top_tensor = torch.zeros(num_sequences, dtype=torch.int32, device="cuda")  # 栈顶指针

    # 启动 Triton kernel 并行处理多个序列的状态转换
    grid = (num_sequences,)  # 每个线程处理一个输入序列
    pda_kernel[grid](
        states,
        stack_tensor,
        stack_top_tensor,
        input_tensor,
        start_state_tensor,
        final_states_tensor,
        output_tensor,
        num_states,
        num_symbols,
        sequence_len,
        stack_depth,
    )

    # 检查是否在终止状态
    check_final_state_kernel[grid](output_tensor, final_states_tensor, result_tensor, len(final_states), num_sequences)

    return result_tensor.cpu().numpy()


# 测试：构建下推自动机并并行处理多个输入序列
if __name__ == "__main__":
    num_states = 3
    num_symbols = 2  # 假设输入符号为 0 和 1

    # PDA 状态转移表 (例子简化，不包含栈操作)
    states = torch.tensor(
        [[1, 2], [0, 2], [1, 2]],  # 状态 0: (0 -> 1, 1 -> 2)  # 状态 1: (0 -> 0, 1 -> 2)  # 状态 2: (0 -> 1, 1 -> 2)
        dtype=torch.int32,
        device="cuda",
    )

    start_state = 0  # 初始状态
    final_states = [2]  # 接受状态

    # 输入序列：多个序列
    input_sequences = torch.tensor(
        [[0, 1, 1, 0, 1], [1, 0, 0, 1, 0], [0, 0, 1, 1, 0]], dtype=torch.int32  # 序列1  # 序列2  # 序列3
    )

    # 检查输入序列是否被接受
    result = pda_sequence_processing(states, start_state, final_states, input_sequences)
    print("Results for input sequences:", result)
