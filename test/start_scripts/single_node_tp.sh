# H200 single node deepseek R1 tp mode
LOADWORKER=18 python -m lightllm.server.api_server --port 8088 \
--model_dir /data/nvme1/models/DeepSeek-R1 \
--tp 8 \
--enable_fa3 \
--mtp_mode deepseekv3_eagle \
--mtp_draft_model_dir /mtc/DeepSeek-R1-NextN \
--mtp_step 2 \
--disable_cudagraph
# if you want to enable microbatch overlap, you can uncomment the following lines
#--enable_prefill_microbatch_overlap \
#--enable_decode_microbatch_overlap \
