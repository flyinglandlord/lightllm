export EXP_BATCH_SIZE=16

python -m lightllm.server.api_server --model_dir /mnt/nvme0/models/Meta-Llama-3.1-8B-Instruct  \
                                     --host 0.0.0.0                 \
                                     --port 9999                   \
                                     --tp 2                        \
                                     --nccl_port 65535                \
				                     --max_req_total_len 200000 \
                                     --max_total_token_num 400000 \
				                     --data_type bf16   \
				                     --trust_remote_code  \
				                     --output_constraint_mode none