# The kernels in this file are adapted from LightLLM's context_attention_fwd:
# https://github.com/ModelTC/lightllm/blob/main/lightllm/models/llama/triton_kernel/context_flashattention_nopad.py
# about vshape refer to https://triton-lang.org/main/getting-started/tutorials/06-fused-attention.html

import torch
import triton
import triton.language as tl

import torch.nn.functional as F


@triton.jit
def _fwd_kernel_fp16(
    Q,
    K,
    V,
    B_Loc,
    sm_scale,
    B_Start_Loc,
    B_Seqlen,
    B_Ctxlen,
    Out,
    stride_b_loc_b,
    stride_b_loc_s,
    stride_qbs,
    stride_qh,
    stride_qd,
    stride_kbs,
    stride_kh,
    stride_kd,
    stride_vbs,
    stride_vh,
    stride_vd,
    stride_obs,
    stride_oh,
    stride_od,
    num_queries_per_kv: int,
    BLOCK_M: tl.constexpr,
    BLOCK_DMODEL: tl.constexpr,  # head size
    BLOCK_DMODEL_PADDED: tl.constexpr,  # head size padded to a power of 2
    BLOCK_N: tl.constexpr,
    SLIDING_WINDOW: tl.constexpr,
):
    cur_batch = tl.program_id(0)
    cur_head = tl.program_id(1)
    start_m = tl.program_id(2)

    cur_kv_head = cur_head // num_queries_per_kv

    cur_batch_ctx_len = tl.load(B_Ctxlen + cur_batch)
    cur_batch_seq_len = tl.load(B_Seqlen + cur_batch)  # 当前batch的seq len
    cur_batch_in_all_start_index = tl.load(B_Start_Loc + cur_batch)  # 当前batch的start index
    cur_batch_query_len = cur_batch_seq_len - cur_batch_ctx_len

    # start position inside of the query
    # generally, N goes over kv, while M goes over query_len
    block_start_loc = BLOCK_M * start_m

    # initialize offsets
    # [N]; starts at 0
    offs_n = tl.arange(0, BLOCK_N)
    # [D]; starts at 0
    offs_d = tl.arange(0, BLOCK_DMODEL_PADDED)
    # [M]; starts at current position in query
    offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
    # [M,D]
    off_q = (
        (cur_batch_in_all_start_index + offs_m[:, None]) * stride_qbs
        + cur_head * stride_qh
        + offs_d[None, :] * stride_qd
    )

    dim_mask = tl.where(offs_d < BLOCK_DMODEL, 1, 0).to(tl.int1)  # [D]

    q = tl.load(Q + off_q, mask=dim_mask[None, :] & (offs_m[:, None] < cur_batch_query_len), other=0.0)  # [M,D]

    # initialize pointer to m and l
    m_i = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")  # [M]
    l_i = tl.zeros([BLOCK_M], dtype=tl.float32)  # [M]
    acc = tl.zeros([BLOCK_M, BLOCK_DMODEL_PADDED], dtype=tl.float32)  # [M,D]

    off_k = offs_n[None, :] * stride_kbs + cur_kv_head * stride_kh + offs_d[:, None] * stride_kd
    off_v = offs_n[:, None] * stride_vbs + cur_kv_head * stride_vh + offs_d[None, :] * stride_vd
    k_ptrs = K + off_k
    v_ptrs = V + off_v

    # block_mask is 0 when we're already past the current query length
    block_mask = tl.where(block_start_loc < cur_batch_query_len, 1, 0)

    # compute query against itself (with causal mask)
    for start_n in range(0, block_mask * (start_m + 1) * BLOCK_M, BLOCK_N):
        start_n = tl.multiple_of(start_n, BLOCK_N)
        # -- compute qk ----
        k = tl.load(
            k_ptrs + (cur_batch_in_all_start_index + start_n) * stride_kbs,
            mask=dim_mask[:, None] & ((start_n + offs_n[None, :]) < cur_batch_query_len),
            other=0.0,
        )

        qk = tl.zeros([BLOCK_M, BLOCK_N], dtype=tl.float32)
        qk += tl.dot(q, k)
        qk *= sm_scale
        # apply causal mask
        qk = tl.where(offs_m[:, None] >= (start_n + offs_n[None, :]), qk, float("-inf"))
        if SLIDING_WINDOW > 0:
            qk = tl.where(offs_m[:, None] - (start_n + offs_n[None, :]) < SLIDING_WINDOW, qk, -10000)

        # -- compute m_ij, p, l_ij
        m_ij = tl.max(qk, 1)
        p = tl.exp(qk - m_ij[:, None])
        l_ij = tl.sum(p, 1)
        # -- update m_i and l_i
        m_i_new = tl.maximum(m_i, m_ij)
        alpha = tl.exp(m_i - m_i_new)
        beta = tl.exp(m_ij - m_i_new)
        l_i_new = alpha * l_i + beta * l_ij
        # -- update output accumulator --
        # scale p
        p_scale = beta / l_i_new
        p = p * p_scale[:, None]
        # scale acc
        acc_scale = l_i / l_i_new * alpha
        acc = acc * acc_scale[:, None]
        # update acc
        v = tl.load(
            v_ptrs + (cur_batch_in_all_start_index + start_n) * stride_vbs,
            mask=dim_mask[None, :] & ((start_n + offs_n[:, None]) < cur_batch_query_len),
            other=0.0,
        )

        p = p.to(v.dtype)
        acc += tl.dot(p, v)
        # update m_i and l_i
        l_i = l_i_new
        m_i = m_i_new
    # initialize pointers to output
    off_o = (
        (cur_batch_in_all_start_index + offs_m[:, None]) * stride_obs
        + cur_head * stride_oh
        + offs_d[None, :] * stride_od
    )
    out_ptrs = Out + off_o
    tl.store(out_ptrs, acc, mask=dim_mask[None, :] & (offs_m[:, None] < cur_batch_query_len))
    return


@triton.jit
def _fwd_kernel_fp8(
    Q,
    K,
    V,
    B_Loc,
    sm_scale,
    B_Start_Loc,
    B_Seqlen,
    B_Ctxlen,
    Out,
    stride_b_loc_b,
    stride_b_loc_s,
    stride_qbs,
    stride_qh,
    stride_qd,
    stride_kbs,
    stride_kh,
    stride_kd,
    stride_vbs,
    stride_vh,
    stride_vd,
    stride_obs,
    stride_oh,
    stride_od,
    num_queries_per_kv: int,
    BLOCK_M: tl.constexpr,
    BLOCK_DMODEL: tl.constexpr,  # head size
    BLOCK_DMODEL_PADDED: tl.constexpr,  # head size padded to a power of 2
    BLOCK_N: tl.constexpr,
    SLIDING_WINDOW: tl.constexpr,
):
    cur_batch = tl.program_id(0)
    cur_head = tl.program_id(1)
    start_m = tl.program_id(2)

    cur_kv_head = cur_head // num_queries_per_kv

    cur_batch_ctx_len = tl.load(B_Ctxlen + cur_batch)
    cur_batch_seq_len = tl.load(B_Seqlen + cur_batch)  # 当前batch的seq len
    cur_batch_in_all_start_index = tl.load(B_Start_Loc + cur_batch)  # 当前batch的start index
    cur_batch_query_len = cur_batch_seq_len - cur_batch_ctx_len

    # start position inside of the query
    # generally, N goes over kv, while M goes over query_len
    block_start_loc = BLOCK_M * start_m

    # initialize offsets
    # [N]; starts at 0
    offs_n = tl.arange(0, BLOCK_N)
    # [D]; starts at 0
    offs_d = tl.arange(0, BLOCK_DMODEL_PADDED)
    # [M]; starts at current position in query
    offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
    # [M,D]
    off_q = (
        (cur_batch_in_all_start_index + offs_m[:, None]) * stride_qbs
        + cur_head * stride_qh
        + offs_d[None, :] * stride_qd
    )

    dim_mask = tl.where(offs_d < BLOCK_DMODEL, 1, 0).to(tl.int1)  # [D]

    # ??? mask=dim_mask[None, :] &
    q = tl.load(Q + off_q, mask=dim_mask[None, :] & (offs_m[:, None] < cur_batch_query_len), other=0.0)  # [M,D]

    # initialize pointer to m and l
    m_i = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")  # [M]
    l_i = tl.zeros([BLOCK_M], dtype=tl.float32)  # [M]
    acc = tl.zeros([BLOCK_M, BLOCK_DMODEL_PADDED], dtype=tl.float32)  # [M,D]

    v_fp8 = True if V.dtype.element_ty == tl.float8e5 else False

    off_k = offs_n[None, :] * stride_kbs + cur_kv_head * stride_kh + offs_d[:, None] * stride_kd

    if v_fp8:
        off_v = offs_n[None, :] * stride_vbs + cur_kv_head * stride_vh + offs_d[:, None] * stride_vd
    else:
        off_v = offs_n[:, None] * stride_vbs + cur_kv_head * stride_vh + offs_d[None, :] * stride_vd

    k_ptrs = K + off_k
    v_ptrs = V + off_v

    # block_mask is 0 when we're already past the current query length
    block_mask = tl.where(block_start_loc < cur_batch_query_len, 1, 0)
    block_end_loc = tl.minimum((start_m + 1) * BLOCK_M, cur_batch_seq_len)

    # compute query against itself (with causal mask)
    for start_n in range(0, block_mask * block_end_loc, BLOCK_N):
        start_n = tl.multiple_of(start_n, BLOCK_N)
        # -- compute qk ----
        k = tl.load(
            k_ptrs + (cur_batch_in_all_start_index + start_n) * stride_kbs,
            mask=((start_n + offs_n[None, :]) < block_end_loc),
            other=0.0,
        )

        qk = tl.zeros([BLOCK_M, BLOCK_N], dtype=tl.float32)
        qk += tl.dot(q, k)
        qk *= sm_scale
        # apply causal mask
        qk = tl.where(offs_m[:, None] >= (start_n + offs_n[None, :]), qk, float("-inf"))
        if SLIDING_WINDOW > 0:
            qk = tl.where(offs_m[:, None] - (start_n + offs_n[None, :]) < SLIDING_WINDOW, qk, -10000)

        # -- compute m_ij, p, l_ij
        m_ij = tl.max(qk, 1)
        p = tl.exp(qk - m_ij[:, None])
        l_ij = tl.sum(p, 1)
        # -- update m_i and l_i
        m_i_new = tl.maximum(m_i, m_ij)
        alpha = tl.exp(m_i - m_i_new)
        beta = tl.exp(m_ij - m_i_new)
        l_i_new = alpha * l_i + beta * l_ij
        # -- update output accumulator --
        # scale p
        p_scale = beta / l_i_new
        p = p * p_scale[:, None]
        # scale acc
        acc_scale = l_i / l_i_new * alpha
        acc_scale = tl.where(offs_m >= start_n, acc_scale, 1.0)
        acc = acc * acc_scale[:, None]
        # update acc
        if v_fp8:
            v = tl.load(
                v_ptrs + (cur_batch_in_all_start_index + start_n) * stride_vbs,
                mask=dim_mask[None, :] & ((start_n + offs_n[None, :]) < block_end_loc),
                other=0.0,
            )
        else:
            v = tl.load(
                v_ptrs + (cur_batch_in_all_start_index + start_n) * stride_vbs,
                mask=dim_mask[None, :] & ((start_n + offs_n[:, None]) < block_end_loc),
                other=0.0,
            )

        p = p.to(v.dtype)
        acc += tl.dot(p, v)
        # update m_i and l_i
        l_i = l_i_new
        m_i = m_i_new
    # initialize pointers to output
    off_o = (
        (cur_batch_in_all_start_index + offs_m[:, None]) * stride_obs
        + cur_head * stride_oh
        + offs_d[None, :] * stride_od
    )
    out_ptrs = Out + off_o
    tl.store(out_ptrs, acc.to(tl.float16), mask=(offs_m[:, None] < cur_batch_query_len))

    return


@torch.inference_mode()
def context_attention_fwd_fp16(
    q, k, v, o, b_loc, b_start_loc, b_seq_len, b_ctx_len, max_input_len, alibi_slopes=None, sliding_window=None
):

    # cap = current_platform.get_device_capability()
    BLOCK = 128  # if cap[0] >= 8 else 64

    # need to reduce num. blocks when using fp32
    # due to increased use of GPU shared memory
    if q.dtype is torch.float32:
        BLOCK = BLOCK // 2

    # shape constraints head_size
    Lq, Lk, Lv = q.shape[-1], k.shape[-1], v.shape[-1]
    assert Lq == Lk and Lk == Lv
    # round up Lk to a power of 2 - this is required for Triton block size
    Lk_padded = triton.next_power_of_2(Lk)

    sm_scale = 1.0 / (Lq ** 0.5)
    # batch and num_query_head num_queries_per_kv
    batch, head = b_seq_len.shape[0], q.shape[1]
    num_queries_per_kv = q.shape[1] // k.shape[1]

    grid = (batch, head, triton.cdiv(max_input_len, BLOCK))  # batch, num_query_head,

    # print("v.shape", v.shape)
    # print("v.stride", v.stride(0), v.stride(1), v.stride(2))

    # 0 means "disable"
    if sliding_window is None or sliding_window <= 0:
        sliding_window = 0

    num_warps = 8 if Lk <= 64 else 8

    _fwd_kernel_fp16[grid](
        q,
        k,
        v,
        b_loc,
        sm_scale,
        b_start_loc,
        b_seq_len,
        b_ctx_len,
        o,
        b_loc.stride(0),
        b_loc.stride(1),
        q.stride(0),
        q.stride(1),
        q.stride(2),
        k.stride(0),
        k.stride(1),
        k.stride(2),
        v.stride(0),
        v.stride(1),
        v.stride(2),
        o.stride(0),
        o.stride(1),
        o.stride(2),
        num_queries_per_kv=num_queries_per_kv,
        BLOCK_M=BLOCK,
        BLOCK_DMODEL=Lk,
        BLOCK_DMODEL_PADDED=Lk_padded,
        BLOCK_N=BLOCK,
        SLIDING_WINDOW=sliding_window,
        num_warps=num_warps,
        num_stages=1,
    )
    return


@torch.inference_mode()
def context_attention_fwd_fp8(
    q, k, v, o, b_loc, b_start_loc, b_seq_len, b_ctx_len, max_input_len, alibi_slopes=None, sliding_window=None
):

    # cap = current_platform.get_device_capability()
    BLOCK = 128  # if cap[0] >= 8 else 64

    # need to reduce num. blocks when using fp32
    # due to increased use of GPU shared memory
    if q.dtype is torch.float32:
        BLOCK = BLOCK // 2

    # shape constraints head_size
    Lq, Lk, Lv = q.shape[-1], k.shape[-1], v.shape[-1]
    assert Lq == Lk and Lk == Lv
    # round up Lk to a power of 2 - this is required for Triton block size
    Lk_padded = triton.next_power_of_2(Lk)
    # print("Lk Lk_padded", Lk, Lk_padded)

    sm_scale = 1.0 / (Lq ** 0.5)
    # batch and num_query_head num_queries_per_kv
    batch, head = b_seq_len.shape[0], q.shape[1]
    num_queries_per_kv = q.shape[1] // k.shape[1]

    grid = (batch, head, triton.cdiv(max_input_len, BLOCK))  # batch, num_query_head,

    # 0 means "disable"
    if sliding_window is None or sliding_window <= 0:
        sliding_window = 0

    num_warps = 8 if Lk <= 64 else 8

    # qkv to  fp8
    q = q.to(torch.float8_e5m2)  # e5m2
    k = k.to(torch.float8_e5m2)
    # [num_tokens, num_heads, head_size] to [num_tokens, num_heads, head_size]
    # v = v.permute(2, 1, 0).contiguous()
    # v = v.permute(2, 1, 0)
    # v = v.to(torch.float8_e5m2)

    # print("v.shape", v.shape)
    # print("v.stride", v.stride(0), v.stride(1), v.stride(2))

    _fwd_kernel_fp8[grid](
        q,
        k,
        v,
        b_loc,
        sm_scale,
        b_start_loc,
        b_seq_len,
        b_ctx_len,
        o,
        b_loc.stride(0),
        b_loc.stride(1),
        q.stride(0),
        q.stride(1),
        q.stride(2),
        k.stride(0),
        k.stride(1),
        k.stride(2),
        v.stride(0),
        v.stride(1),
        v.stride(2),
        o.stride(0),
        o.stride(1),
        o.stride(2),
        num_queries_per_kv=num_queries_per_kv,
        BLOCK_M=BLOCK,
        BLOCK_DMODEL=Lk,
        BLOCK_DMODEL_PADDED=Lk_padded,
        BLOCK_N=BLOCK,
        SLIDING_WINDOW=sliding_window,
        num_warps=num_warps,
        num_stages=1,
    )
    return


def torch_att(xq, xk, xv, bs, seqlen, num_head_q, head_dim):
    xq = xq.view(bs, seqlen, num_head_q, head_dim)
    xk = xk.view(bs, seqlen, num_head_q, head_dim)
    xv = xv.view(bs, seqlen, num_head_q, head_dim)
    mask = torch.tril(torch.ones(seqlen, seqlen), diagonal=0).unsqueeze(0).unsqueeze(0).cuda()
    mask[mask == 0.0] = -100000000.0
    mask = mask.repeat(bs, num_head_q, 1, 1)
    keys = xk
    values = xv
    xq = xq.transpose(1, 2)
    keys = keys.transpose(1, 2)
    values = values.transpose(1, 2)
    import math

    scores = torch.matmul(xq, keys.transpose(2, 3)) / math.sqrt(head_dim)
    scores = F.softmax(scores.float() + mask, dim=-1).type_as(xq)
    output = torch.matmul(scores, values).transpose(1, 2).contiguous().reshape(-1, num_head_q, head_dim)
    return output


def test():
    import torch
    import numpy as np

    # batch, HQ, HKV, D_HEAD = 5, 32, 8, 128 #llama 8B
    batch, HQ, HKV, D_HEAD = 5, 64, 8, 128  # qwen 72B
    SEQ = 2533
    dtype = torch.float16
    q = torch.empty((SEQ, HQ, D_HEAD), dtype=dtype, device="cuda:0").normal_(mean=0.1, std=0.2)
    k = torch.empty((SEQ, HKV, D_HEAD), dtype=dtype, device="cuda:0").normal_(mean=0.4, std=0.2)
    v = torch.empty((SEQ, HKV, D_HEAD), dtype=dtype, device="cuda:0").normal_(mean=0.3, std=0.2)
    o = torch.empty_like(q, dtype=dtype)
    max_input_len = 2502
    # max_query_len = 2502

    b_loc = torch.zeros((5, 0), device="cuda:0", dtype=torch.int32)
    b_start_loc = torch.tensor([0, 6, 19, 25, 31, 2533], device="cuda:0", dtype=torch.int32)
    b_seq_len = torch.tensor([6, 13, 6, 6, 2502], device="cuda:0", dtype=torch.int32)
    b_ctx_len = torch.tensor([0, 0, 0, 0, 0], device="cuda:0", dtype=torch.int32)

    import time

    step = 10
    start_events = [torch.cuda.Event(enable_timing=True) for _ in range(step)]
    end_events = [torch.cuda.Event(enable_timing=True) for _ in range(step)]

    torch.cuda.synchronize()
    # a = time.time()
    for i in range(step):
        # fp16
        # fp8
        start_events[i].record()
        # context_attention_fwd_fp16(
        context_attention_fwd_fp8(q, k, v, o, b_loc, b_start_loc, b_seq_len, b_ctx_len, max_input_len)
        end_events[i].record()
    torch.cuda.synchronize()

    time_all = [s.elapsed_time(e) for s, e in zip(start_events, end_events)]
    t = sorted(time_all)[step // 2]

    # b = time.time()
    # print(o.shape, torch_out.shape)
    print("time: ", t)

    torch_out = []
    start = 0
    from einops import repeat

    k = repeat(k, "bs h d -> bs (h g) d", g=q.shape[1] // k.shape[1])
    v = repeat(v, "bs h d -> bs (h g) d", g=q.shape[1] // v.shape[1])
    for i in range(batch):
        end = start + b_seq_len[i]
        torch_o = torch_att(q[start:end], k[start:end], v[start:end], 1, b_seq_len[i], HQ, D_HEAD)
        start = end
        torch_out.append(torch_o)

    torch_out = torch.cat(torch_out, dim=0)

    o = o.to(torch.float16)
    print("max ", torch.max(torch.abs(torch_out - o)))
    print("mean ", torch.mean(torch.abs(torch_out - o)))
    print("torch_out, o", torch_out[0], o[0])
    assert torch.allclose(torch_out, o, atol=1e-2, rtol=0)


if __name__ == "__main__":
    test()
