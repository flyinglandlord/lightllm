import os
import torch
import math
import numpy as np
from lightllm.common.basemodel import TransformerLayerWeight
from lightllm.models.llama.layer_weights.transformer_layer_weight import LlamaTransformerLayerWeight
from lightllm.utils.envs_utils import enable_env_vars
from lightllm.common.basemodel.layer_weights.meta_weights import (
    ROWMMWeight,
    MultiROWMMWeight,
    COLMMWeight,
    NormWeight,
    FusedMoeWeightTP,
    FusedMoeWeightEP,
    ROWBMMWeight,
)
from functools import partial


class Qwen3MOETransformerLayerWeight(LlamaTransformerLayerWeight):
    def __init__(self, layer_num, data_type, network_config, mode=[], quant_cfg=None):
        self.n_routed_experts = network_config["num_experts"]
        self.is_moe = (
            network_config["num_experts"] > 0
            and layer_num not in network_config["mlp_only_layers"]
            and (layer_num + 1) % network_config["decoder_sparse_step"] == 0
        )
        super().__init__(layer_num, data_type, network_config, mode, quant_cfg)
        return

    def _init_weight_names(self):
        self._q_weight_name = f"model.layers.{self.layer_num_}.self_attn.q_proj.weight"
        self._q_norm_name = f"model.layers.{self.layer_num_}.self_attn.q_norm.weight"
        self._q_bias_name = None
        self._k_weight_name = f"model.layers.{self.layer_num_}.self_attn.k_proj.weight"
        self._k_norm_name = f"model.layers.{self.layer_num_}.self_attn.k_norm.weight"
        self._k_bias_name = None
        self._v_weight_name = f"model.layers.{self.layer_num_}.self_attn.v_proj.weight"
        self._v_bias_name = None
        self._kv_weight_name = f"model.layers.{self.layer_num_}.self_attn.kv_proj.weight"
        self._kv_bias_name = None
        self._o_weight_name = f"model.layers.{self.layer_num_}.self_attn.o_proj.weight"
        self._o_bias_name = None
        self._att_norm_weight_name = f"model.layers.{self.layer_num_}.input_layernorm.weight"
        self._att_norm_bias_name = None
        self._ffn_norm_weight_name = f"model.layers.{self.layer_num_}.post_attention_layernorm.weight"
        self._ffn_norm_bias_name = None

    def _parse_config(self):
        self.tp_q_head_num_ = self.network_config_["num_attention_heads"] // self.tp_world_size_
        self.tp_k_head_num_ = max(self.network_config_["num_key_value_heads"] // self.tp_world_size_, 1)
        self.tp_v_head_num_ = self.tp_k_head_num_
        self.tp_o_head_num_ = self.tp_q_head_num_
        self.head_dim = self.network_config_["head_dim"]
        assert self.tp_k_head_num_ * self.tp_world_size_ % self.network_config_["num_key_value_heads"] == 0

    def _repeat_weight(self, name, weights):
        repeat_size = self.tp_k_head_num_ * self.tp_world_size_ // self.network_config_["num_key_value_heads"]
        repeat_params = (1, repeat_size, 1, 1)
        if name in weights:
            weights[name] = (
                weights[name]
                .reshape(self.network_config_["num_key_value_heads"], -1, weights[name].shape[1])
                .unsqueeze(1)
                .repeat(repeat_params)
                .reshape(-1, weights[name].shape[1])
            )

    def load_hf_weights(self, weights):
        self._repeat_weight(self._k_weight_name, weights)
        self._repeat_weight(self._v_weight_name, weights)
        kv_b_quant_method = self.quant_cfg.get_quant_method(self.layer_num_, "kv_b_proj")
        if self.quant_cfg.quantized_weight:
            _k_scale_weight_name = self._k_weight_name.replace("weight", kv_b_quant_method.weight_scale_suffix)
            self._repeat_weight(_k_scale_weight_name, weights)
            _v_scale_weight_name = self._v_weight_name.replace("weight", kv_b_quant_method.weight_scale_suffix)
            self._repeat_weight(_v_scale_weight_name, weights)
        return super().load_hf_weights(weights)

    def _init_weight(self):
        self._init_qkv()
        self._init_o()
        if self.is_moe:
            self._init_moe()
        else:
            self._init_ffn()
        self._init_norm()

    def _init_moe(self):
        moe_intermediate_size = self.network_config_["moe_intermediate_size"]
        self.moe_gate = ROWMMWeight(
            weight_name=f"model.layers.{self.layer_num_}.mlp.gate.weight",
            data_type=self.data_type_,
            layer_num=self.layer_num_,
            name="moe_gate",
            tp_rank=0,
            tp_world_size=1,
        )
        moe_mode = os.getenv("MOE_MODE", "TP")
        assert moe_mode in ["EP", "TP"]
        if moe_mode == "TP":
            self.experts = FusedMoeWeightTP(
                gate_proj_name="gate_proj",
                down_proj_name="down_proj",
                up_proj_name="up_proj",
                e_score_correction_bias_name="",
                weight_prefix=f"model.layers.{self.layer_num_}.mlp.experts",
                n_routed_experts=self.n_routed_experts,
                split_inter_size=moe_intermediate_size // self.tp_world_size_,
                data_type=self.data_type_,
                network_config=self.network_config_,
                layer_num=self.layer_num_,
                quant_cfg=self.quant_cfg,
            )
        elif moe_mode == "EP":
            self.experts = FusedMoeWeightEP(
                gate_proj_name="gate_proj",
                down_proj_name="down_proj",
                up_proj_name="up_proj",
                e_score_correction_bias_name="",
                weight_prefix=f"model.layers.{self.layer_num_}.mlp.experts",
                n_routed_experts=self.n_routed_experts,
                data_type=self.data_type_,
                network_config=self.network_config_,
                layer_num=self.layer_num_,
                quant_cfg=self.quant_cfg,
            )
        else:
            raise ValueError(f"Unsupported moe mode: {moe_mode}")

    def _init_norm(self):
        super()._init_norm()
        self.q_norm_weight_ = NormWeight(weight_name=self._q_norm_name, data_type=self.data_type_)
        self.k_norm_weight_ = NormWeight(weight_name=self._k_norm_name, data_type=self.data_type_)
