from datasets import load_dataset
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("/mnt/nvme0/models/Meta-Llama-3.1-8B-Instruct/")

ds = load_dataset("NousResearch/json-mode-eval")
print(tokenizer.apply_chat_template(ds['train'][0]['prompt'], tokenize=False))
print(ds['train'][0]['completion'])