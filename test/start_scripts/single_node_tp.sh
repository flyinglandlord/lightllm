# H200 single node deepseek R1 tp mode
LOADWORKER=18 python -m lightllm.server.api_server --port 8088 \
--model_dir /data/nvme0/models/qwen25-7b-instruct \
--tp 1 \
--enable_fa3 \
--tool_call_parser qwen25
# if you want to enable microbatch overlap, you can uncomment the following lines
#--enable_prefill_microbatch_overlap \
#--enable_decode_microbatch_overlap \
