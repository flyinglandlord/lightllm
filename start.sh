#!/bin/bash
MODEL_PATH=/mnt/nvme0/models/llama2-7b-chat
CUDA_VISIBLE_DEVICES=1,4 python -m lightllm.server.api_server --model_dir $MODEL_PATH \
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
