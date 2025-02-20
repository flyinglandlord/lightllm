# CUDA_LAUNCH_BLOCKING=1  QUANT_TYPE=vllm-w8a8 ENABLE_VLLM_REDUCE=1 \
# MAX_INPUT_ADD_OUTPUT_LEN=32768 DATA_TYPE=bfloat16 \
# ENABLE_PROMPTCACHE=1 SKIP_SPECIAL=1 \
CUDA_VISIBLE_DEVICES=0,1,2,3,4,6,7 EXP_BATCH_SIZE=32 \
python -m lightllm.server.api_server --model_dir /mnt/nvme0/models/deepseek-v2\
    --host 0.0.0.0 \
    --port 8888    \
    --tp 2         \
    --nccl_port 65535            \
    --running_max_req_size 32 \
	--max_req_total_len 150000   \
    --max_total_token_num 300000 \
    --tokenizer_mode fast \
	--data_type bf16    \
	--trust_remote_code \
    --disable_cudagraph \
    --output_constraint_mode xgrammar