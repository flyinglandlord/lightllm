import time
import requests
import json
import argparse
from datasets import load_dataset, Dataset, DatasetDict
from typing import Dict, Any, List
from transformers import AutoTokenizer  # ✅ 新增：用于加载 tokenizer 和应用 chat template

# --- 配置参数 ---
URL = "http://localhost:8088/generate"
HEADERS = {"Content-Type": "application/json"}
MAX_NEW_TOKENS = 256 
CACHE_DIR = "./hf_datasets_cache"
DEFAULT_SPLIT = 'test'

# ✅ 加载 DeepSeek-R1 的 tokenizer（假设模型名为 "deepseek-ai/deepseek-r1"）
# 注意：你需要确保本地或 Hugging Face 上有这个模型的 tokenizer
TOKENIZER_NAME = "/data/nvme1/models/DeepSeek-R1"
print(f"📥 Loading tokenizer for '{TOKENIZER_NAME}'...")
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)

# --- 数据集映射配置 ---
DATASET_CONFIGS = {
    "mt-bench": {
        "hf_name": "HuggingFaceH4/mt_bench_prompts",
        "split": "train", 
        "prompt_key": "prompt",
        "combine_func": lambda item: item[0],
        "use_chat_template": True,
        "system_prompt": "You are a helpful AI assistant named DeepSeek."
    },

    "gsm8k": {
        "hf_name": "openai/gsm8k", 
        "hf_config": "main", 
        "split": DEFAULT_SPLIT,
        "prompt_key": "question",
        "use_chat_template": True,
        "system_prompt": "You are a helpful AI assistant named DeepSeek."
    },
    
    "humaneval": {
        "hf_name": "openai_humaneval", 
        "split": DEFAULT_SPLIT,
        "prompt_key": "prompt",
        "use_chat_template": True,
        "system_prompt": "You are a helpful AI assistant named DeepSeek. Please complete the Python function below."
    },
    
    "alpaca": {
        "hf_name": "yahma/alpaca-cleaned", 
        "split": "train",
        "prompt_keys": ["instruction", "input"],
        "combine_func": lambda item: (
            f"Instruction: {item['instruction']}\\nInput: {item['input']}"
            if item['input'] else item['instruction']
        ),
        "use_chat_template": True,
        "system_prompt": "You are a helpful AI assistant named DeepSeek."
    },
    
    "cnn_dm": {
        "hf_name": "abisee/cnn_dailymail", 
        "hf_config": "3.0.0", 
        "split": DEFAULT_SPLIT,
        "prompt_key": "article",
        "use_chat_template": True,
        "system_prompt": "You are a helpful AI assistant named DeepSeek. Summarize the following article."
    },
}

# --- 辅助函数：数据加载和提取 ---
def load_task_dataset(task_name: str) -> Dataset:
    """根据任务名称加载 Hugging Face Dataset 并返回用于测试的 Dataset 对象。"""
    if task_name not in DATASET_CONFIGS:
        raise ValueError(f"Unknown task name: {task_name}. Supported tasks: {list(DATASET_CONFIGS.keys())}")

    config = DATASET_CONFIGS[task_name]
    hf_name = config['hf_name']
    hf_config = config.get('hf_config')
    split = config['split']
    
    print(f"💡 Loading task '{task_name}' from '{hf_name}' (Split: {split})...")
    
    if task_name == "mt-bench":
        data = load_dataset(hf_name, split=None, cache_dir=CACHE_DIR)
        if isinstance(data, DatasetDict):
             return data[list(data.keys())[0]] 
        return data
        
    dataset = load_dataset(hf_name, hf_config, split=split, cache_dir=CACHE_DIR)
    return dataset

def extract_prompt(item: Dict[str, Any], config: Dict[str, Any]) -> str:
    """根据数据集配置从单个数据项中提取或构造最终的 Prompt 字符串，并应用 chat template（如启用）。"""
    prompt_key = config['prompt_key']
    if 'combine_func' in config:
        raw_prompt = config['combine_func'](item[prompt_key])
    else:
        raw_prompt = item[prompt_key]

    if config.get('use_chat_template', False):
        system_prompt = config.get('system_prompt', "")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": raw_prompt})

        # ✅ 使用 tokenizer.apply_chat_template 自动格式化
        templated_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,      # 返回字符串而非 token IDs
            add_generation_prompt=True  # 添加 Assistant: 前缀，准备生成
        )
        return templated_prompt

    return raw_prompt

# --- 主运行逻辑：顺序发送请求 ---
def run_benchmark(task_name: str):
    try:
        dataset = load_task_dataset(task_name)
        config = DATASET_CONFIGS[task_name]
    except Exception as e:
        print(f"🚨 Failed to load dataset for task {task_name}: {e}")
        return

    print(f"\n🚀 Starting sequential inference test on {task_name} with {len(dataset)} examples...")
    print("📢 Testing started. MTP metrics logging is assumed to be handled by the server.")

    for i, item in enumerate(dataset):
        try:
            prompt = extract_prompt(item, config)
        except Exception as e:
            print(f"⚠️ Skipping item {i} (QID: {item.get('question_id', 'N/A')}) due to prompt extraction error: {e}")
            continue
        print(prompt)

        api_data = {
            "inputs": prompt,
            "parameters": {
                "do_sample": False,
                "max_new_tokens": MAX_NEW_TOKENS,
            },
            # # 传递元数据到服务端，以便服务端将 MTP 指标与请求 ID 关联
            # "request_metadata": {
            #     "task_name": task_name,
            #     "item_index": i,
            #     "question_id": item.get('question_id', i),
            #     "prompt_length": len(prompt) # 粗略的字符长度
            # } 
        }
        
        start_time = time.time()
        try:
            # 发送请求并等待响应（同步）
            response = requests.post(URL, headers=HEADERS, data=json.dumps(api_data), timeout=180) 
            e2e_latency = time.time() - start_time
            
            if response.status_code == 200:
                print(f"[{i+1}/{len(dataset)}] ✅ Task: {task_name} | Latency: {e2e_latency:.2f}s")
            else:
                print(f"[{i+1}/{len(dataset)}] ❌ Task: {task_name} | Status: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"[{i+1}/{len(dataset)}] 🚨 Task: {task_name} | Request Failed: {e}")

    print("\n✅ All requests finished for the current task.")


# --- 命令行解析 ---
def main():
    parser = argparse.ArgumentParser(description="Run LLM MTP benchmark on specified HuggingFace dataset.")
    parser.add_argument(
        '--task_name',
        type=str,
        required=True,
        choices=list(DATASET_CONFIGS.keys()),
        help=f"The benchmark task name to run. Choices: {list(DATASET_CONFIGS.keys())}"
    )
    args = parser.parse_args()
    
    run_benchmark(args.task_name)


if __name__ == "__main__":
    main()