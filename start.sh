#!/bin/bash
MODEL_PATH=/home/chenjunyi/.cache/huggingface/hub/models--meta-llama--Llama-2-7b-hf/snapshots/8cca527612d856d7d32bd94f8103728d614eb852
CUDA_VISIBLE_DEVICES=6,7 python -m lightllm.server.api_server --model_dir $MODEL_PATH \
        --tp 2 \
        --max_req_total_len 130000 \
        --tokenizer_mode auto \
        --port 8000 \
        --max_req_input_len 128000 \
        --max_total_token_num 130000 \
        --trust_remote_code \
        --splitfuse_mode \
        --splitfuse_block_size 512 \
        --nccl_port 28785 \
        --mode triton_gqa_flashdecoding
