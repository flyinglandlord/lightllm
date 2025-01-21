QUANT_TYPE=vllm-w8a8 ENABLE_VLLM_REDUCE=1 \
MAX_INPUT_ADD_OUTPUT_LEN=32768 DATA_TYPE=bfloat16 \
ENABLE_PROMPTCACHE=1 SKIP_SPECIAL=1 \
python -m lightllm.server.api_server --model_dir /mnt/nvme0/models/Meta-Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 9999    \
    --tp 1         \
    --nccl_port 65535            \
	--max_req_total_len 20000   \
    --max_total_token_num 40000 \
	--data_type bf16    \
	--trust_remote_code \
    --output_constraint_mode lightllm