import torch
import math
import numpy as np
from lightllm.common.basemodel import TransformerLayerWeight


class Qwen2TransformerLayerWeight(TransformerLayerWeight):
    def __init__(self, layer_num, tp_rank, world_size, data_type, network_config, mode=[]):
        super().__init__(layer_num, tp_rank, world_size, data_type, network_config, mode)

    def _load_qkvo_weights(self, weights):
        # input norm
        if f"model.layers.{self.layer_num_}.input_layernorm.weight" in weights:
            self.att_norm_weight_ = self._cuda(weights[f"model.layers.{self.layer_num_}.input_layernorm.weight"])

        n_embed = self.network_config_["hidden_size"]
        q_split_n_embed = n_embed // self.world_size_
        kv_split_n_embed = (
            n_embed
            // self.network_config_["num_attention_heads"]
            * self.network_config_["num_key_value_heads"]
            // self.world_size_
        )
        # q k v weights for llama
        if f"model.layers.{self.layer_num_}.self_attn.q_proj.weight" in weights:
            self.q_weight_ = weights[f"model.layers.{self.layer_num_}.self_attn.q_proj.weight"]
            self.q_weight_ = self.q_weight_[q_split_n_embed * self.tp_rank_ : q_split_n_embed * (self.tp_rank_ + 1), :]
            self.q_weight_ = self._cuda(self.q_weight_.transpose(0, 1))

        if f"model.layers.{self.layer_num_}.self_attn.k_proj.weight" in weights:
            k_weight_ = weights[f"model.layers.{self.layer_num_}.self_attn.k_proj.weight"]
            k_weight_ = k_weight_[kv_split_n_embed * self.tp_rank_ : kv_split_n_embed * (self.tp_rank_ + 1), :]
            self.k_weight_ = k_weight_.transpose(0, 1)

        if f"model.layers.{self.layer_num_}.self_attn.v_proj.weight" in weights:
            v_weight_ = weights[f"model.layers.{self.layer_num_}.self_attn.v_proj.weight"]
            v_weight_ = v_weight_[kv_split_n_embed * self.tp_rank_ : kv_split_n_embed * (self.tp_rank_ + 1), :]
            self.v_weight_ = v_weight_.transpose(0, 1)

        # attention output dense params
        if f"model.layers.{self.layer_num_}.self_attn.o_proj.weight" in weights:
            self.o_weight_ = weights[f"model.layers.{self.layer_num_}.self_attn.o_proj.weight"]
            self.o_weight_ = self.o_weight_[:, q_split_n_embed * self.tp_rank_ : q_split_n_embed * (self.tp_rank_ + 1)]
            self.o_weight_ = self._cuda(self.o_weight_.transpose(0, 1))

        if f"model.layers.{self.layer_num_}.self_attn.q_proj.bias" in weights:
            q_bias_ = self._cuda(weights[f"model.layers.{self.layer_num_}.self_attn.q_proj.bias"])
            self.q_bias_ = q_bias_[q_split_n_embed * self.tp_rank_ : q_split_n_embed * (self.tp_rank_ + 1)]

        if f"model.layers.{self.layer_num_}.self_attn.k_proj.bias" in weights:
            k_bias = weights[f"model.layers.{self.layer_num_}.self_attn.k_proj.bias"]
            self.k_bias_ = k_bias[kv_split_n_embed * self.tp_rank_ : kv_split_n_embed * (self.tp_rank_ + 1)]

        if f"model.layers.{self.layer_num_}.self_attn.v_proj.bias" in weights:
            v_bias = weights[f"model.layers.{self.layer_num_}.self_attn.v_proj.bias"]
            self.v_bias_ = v_bias[kv_split_n_embed * self.tp_rank_ : kv_split_n_embed * (self.tp_rank_ + 1)]

        self._try_cat_to(["k_weight_", "v_weight_"], "kv_weight_", cat_dim=1)
        self._try_cat_to(["k_bias_", "v_bias_"], "kv_bias_", cat_dim=0)

    def _load_ffn_weights(self, weights):
        if f"model.layers.{self.layer_num_}.post_attention_layernorm.weight" in weights:
            self.ffn_norm_weight_ = self._cuda(
                weights[f"model.layers.{self.layer_num_}.post_attention_layernorm.weight"]
            )

        inter_size = self.network_config_["intermediate_size"]
        split_inter_size = inter_size // self.world_size_

        if f"model.layers.{self.layer_num_}.mlp.up_proj.weight" in weights:
            up_proj = weights[f"model.layers.{self.layer_num_}.mlp.up_proj.weight"][
                split_inter_size * self.tp_rank_ : split_inter_size * (self.tp_rank_ + 1), :
            ]
            self.up_proj = up_proj.transpose(0, 1)

        if f"model.layers.{self.layer_num_}.mlp.gate_proj.weight" in weights:
            gate_proj = weights[f"model.layers.{self.layer_num_}.mlp.gate_proj.weight"][
                split_inter_size * self.tp_rank_ : split_inter_size * (self.tp_rank_ + 1), :
            ]
            self.gate_proj = gate_proj.transpose(0, 1)

        self._try_cat_to(["gate_proj", "up_proj"], "gate_up_proj", cat_dim=1)

        if f"model.layers.{self.layer_num_}.mlp.down_proj.weight" in weights:
            self.down_proj = weights[f"model.layers.{self.layer_num_}.mlp.down_proj.weight"][
                :, split_inter_size * self.tp_rank_ : split_inter_size * (self.tp_rank_ + 1)
            ]
            self.down_proj = self._cuda(self.down_proj.transpose(0, 1))
        return

    def load_hf_weights(self, weights):
        self._load_qkvo_weights(weights)
        self._load_ffn_weights(weights)
        return

    def verify_load(self):
        errors = "weights load not ok"
        weights = [
            self.att_norm_weight_,
            self.q_weight_,
            self.kv_weight_,
            self.q_bias_,
            self.kv_bias_,
            self.o_weight_,
            self.ffn_norm_weight_,
            self.gate_up_proj,
            self.down_proj,
        ]
        for i in range(len(weights)):
            assert weights[i] is not None, "index:" + str(i) + " " + errors
        return
