import torch
import torch.functional as F
import torch.distributed as dist
import numpy as np
from typing import Tuple
import triton
from lightllm.models.llama.infer_struct import LlamaInferStateInfo

from lightllm.models.llama.layer_infer.transformer_layer_infer import LlamaTransformerLayerInfer, rotary_emb_fwd
from lightllm.models.qwen2.infer_struct import Qwen2InferStateInfo

from lightllm.models.mistral.triton_kernel.context_flashattention_nopad import context_attention_fwd
from lightllm.models.mistral.triton_kernel.token_attention_nopad_att1 import token_att_fwd
from lightllm.models.mistral.triton_kernel.token_attention_nopad_reduceV import token_att_fwd2
from lightllm.models.llama.triton_kernel.token_attention_nopad_softmax import token_softmax_fwd

from lightllm.common.basemodel.triton_kernel.destindex_copy_kv import destindex_copy_kv
from lightllm.models.qwen2.layer_weights.transformer_layer_weight import Qwen2TransformerLayerWeight


class Qwen2TransformerLayerInfer(LlamaTransformerLayerInfer):
    def __init__(self, layer_num, tp_rank, world_size, network_config, mode=[]):
        super().__init__(layer_num, tp_rank, world_size, network_config, mode)
        return

    def _get_qkv(
        self, input, cache_kv, infer_state: Qwen2InferStateInfo, layer_weight: Qwen2TransformerLayerWeight
    ) -> torch.Tensor:
        q = torch.addmm(
            layer_weight.q_bias_,
            input.view(-1, self.embed_dim_),
            layer_weight.q_weight_,
            beta=1.0,
            alpha=1.0,
        )
        torch.addmm(
            layer_weight.kv_bias_,
            input.view(-1, self.embed_dim_),
            layer_weight.kv_weight_,
            beta=1.0,
            alpha=1.0,
            out=cache_kv.view(-1, (self.tp_k_head_num_ + self.tp_v_head_num_) * self.head_dim_),
        )
        rotary_emb_fwd(
            q.view(-1, self.tp_q_head_num_, self.head_dim_),
            cache_kv[:, 0 : self.tp_k_head_num_, :],
            infer_state.position_cos,
            infer_state.position_sin,
        )
        return q, cache_kv

    def _bind_func(self):
        self._token_attention_kernel = self._token_decode_attention_normal
        self._copy_kv_to_mem_cache = self._copy_kv_to_mem_cache_normal
        return

    def _context_attention_kernel(
        self, q, kv, infer_state: Qwen2InferStateInfo, layer_weight, out=None
    ) -> torch.Tensor:
        o_tensor = torch.empty_like(q) if out is None else out
        context_attention_fwd(
            q.view(-1, self.tp_q_head_num_, self.head_dim_),
            kv[:, 0 : self.tp_k_head_num_, :],
            kv[:, self.tp_k_head_num_ : self.tp_k_head_num_ + self.tp_v_head_num_, :],
            o_tensor.view(-1, self.tp_q_head_num_, self.head_dim_),
            infer_state.b_start_loc,
            infer_state.b_seq_len,
            infer_state.max_len_in_batch,
            infer_state.sliding_window,
        )
        return o_tensor

    def _token_decode_attention_normal(self, q, infer_state: Qwen2InferStateInfo, layer_weight, out=None):
        total_token_num = infer_state.total_cache_num
        batch_size = infer_state.batch_size
        calcu_shape1 = (batch_size, self.tp_q_head_num_, self.head_dim_)

        att_m_tensor = torch.empty((self.tp_q_head_num_, total_token_num), dtype=q.dtype, device="cuda")

        token_att_fwd(
            q.view(calcu_shape1),
            infer_state.mem_manager.kv_buffer[self.layer_num_][:, 0 : self.tp_k_head_num_, :],
            att_m_tensor,
            infer_state.req_manager.req_to_token_indexs,
            infer_state.b_req_idx,
            infer_state.b_start_loc,
            infer_state.b_seq_len,
            infer_state.b_att_start_loc,
            infer_state.b_att_seq_len,
            infer_state.sliding_window,
        )

        o_tensor = torch.empty_like(q) if out is None else out

        from lightllm.models.mistral.triton_kernel.token_attention_softmax_and_reducev import (
            token_softmax_reducev_fwd,
        )

        token_softmax_reducev_fwd(
            att_m_tensor,
            infer_state.mem_manager.kv_buffer[self.layer_num_][
                :, self.tp_k_head_num_ : self.tp_k_head_num_ + self.tp_v_head_num_, :
            ],
            o_tensor.view(calcu_shape1),
            infer_state.req_manager.req_to_token_indexs,
            infer_state.b_req_idx,
            infer_state.b_start_loc,
            infer_state.b_seq_len,
            infer_state.b_att_start_loc,
            infer_state.b_att_seq_len,
            infer_state.other_kv_index,
            infer_state.sliding_window,
        )
        return o_tensor
