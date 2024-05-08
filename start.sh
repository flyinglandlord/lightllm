#!/bin/bash
MODEL_PATH=/home/chenjunyi/.cache/huggingface/hub/models--togethercomputer--LLaMA-2-7B-32K/snapshots/46c24bb5aef59722fa7aa6d75e832afd1d64b980
CUDA_VISIBLE_DEVICES=6,7 python -m lightllm.server.api_server --model_dir $MODEL_PATH \
        --tp 2 \
        --max_req_total_len 130000 \
        --tokenizer_mode auto \
        --port 8000 \
        --max_req_input_len 128000 \
        --max_total_token_num 130000 \
        --trust_remote_code \
        --splitfuse_mode \
        --splitfuse_block_size 4096 \
        --nccl_port 28785 \
        --mode triton_gqa_flashdecoding
