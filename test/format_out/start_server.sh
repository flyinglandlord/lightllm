CUDA_LAUNCH_BLOCKING=1 CUDA_VISIBLE_DEVICES=1,3,4,5,6 QUANT_TYPE=vllm-w8a8 ENABLE_VLLM_REDUCE=1 \
MAX_INPUT_ADD_OUTPUT_LEN=32768 DATA_TYPE=bfloat16 \
ENABLE_PROMPTCACHE=1 SKIP_SPECIAL=1 \
python -m lightllm.server.api_server --model_dir /mnt/nvme0/chenjunyi/models/nb10_w8 \
    --host 0.0.0.0 \
    --port 9999    \
    --tp 4         \
    --nccl_port 65535            \
    --running_max_req_size 256 \
	--max_req_total_len 400000   \
    --max_total_token_num 800000 \
    --tokenizer_mode fast \
	--data_type bf16    \
	--trust_remote_code \
    --output_constraint_mode lightllm