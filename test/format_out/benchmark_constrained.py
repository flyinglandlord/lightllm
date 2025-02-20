# Adapted from benchmarks/benchmark_serving.py
# of the vllm-project/vllm GitHub repository.
#
# Copyright 2023 ModelTC Team
# Copyright 2023 vLLM Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import asyncio
import json
import random
import time
from typing import AsyncGenerator, List, Tuple, Union

import aiohttp
import numpy as np
from transformers import PreTrainedTokenizerBase
from transformers import AutoModelForCausalLM, PreTrainedTokenizerBase

from transformers import (AutoTokenizer, PreTrainedTokenizer,
                          PreTrainedTokenizerFast)
from datasets import load_dataset

json_ebnf_file = "/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/grammar/json_grammar.ebnf"
cot_ebnf_file = "/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/grammar/chain_of_thought.ebnf"

json_grammar = r"""
root ::= object
object ::= "{" ws ( string ":" ws value ("," ws string ":" ws value)* )? "}"
value ::= object | array | string | number | ("true" | "false" | "null") ws
array  ::= "[" ws ( value ("," ws value)* )? "]" ws
string ::= "\"" [a-zA-Z\x20\x21\x23\x24\x25\x26\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30-\x39\x41-\x5a\x5e\x5f\x60\x61-\x7a\x7e]* "\"" ws
number ::= ("0" | "-"? [1-9] [0-9]*) ("." [0-9]+)? ([eE] [+-]? [0-9]+)? ws
ws ::= ([ĊĠ     ] ws)?
"""

cot_grammar = r"""
root ::= "{" reasoning "," conclusion "}"
reasoning ::= "\"" "reasoning" "\"" ":" "[" reasoning_steps "]"
reasoning_steps ::= reasoning_step | reasoning_step "," reasoning_steps
reasoning_step ::= "{" "\"" "reasoning_step" "\"" ":" string "}"
conclusion ::= "\"" "conclusion" "\"" ":" string
string ::= "\"" [a-zA-Z\x20\x21\x23\x24\x25\x26\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30-\x39\x41-\x5a\x5e\x5f\x60\x61-\x7a\x7e]* "\"" ws
ws ::= ([ĊĠ     ] ws)?
"""

def get_tokenizer(
    tokenizer_name: str,
    tokenizer_mode: str = "auto",
    *args,
    **kwargs,
) -> Union[PreTrainedTokenizer, PreTrainedTokenizerFast]:
    """Gets a tokenizer for the given model name via Huggingface."""
    if tokenizer_mode == "slow":
        if kwargs.get("use_fast", False):
            raise ValueError(
                "Cannot use the fast tokenizer in slow tokenizer mode.")
        kwargs["use_fast"] = False

    if "llama" in tokenizer_name.lower() and kwargs.get("use_fast", True):
        pass
    try:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, *args,
                                                  **kwargs)
    except TypeError as e:
        err_msg = (
            "Failed to load the tokenizer. If you are using a LLaMA-based "
            f"model, use '{_FAST_LLAMA_TOKENIZER}' instead of the original "
            "tokenizer.")
        raise RuntimeError(err_msg) from e

    if not isinstance(tokenizer, PreTrainedTokenizerFast):
        pass
    return tokenizer

# (prompt len, output len, latency)
REQUEST_LATENCY: List[Tuple[int, int, float]] = []


def sample_requests(
    dataset_type: str,
    num_requests: int,
    tokenizer: PreTrainedTokenizerBase,
    random: bool,
) -> List[Tuple[str, int, int]]:
    # JSON dataset
    ds = load_dataset("/home/chenjunyi/.cache/huggingface/datasets/NousResearch___json-mode-eval/default/0.0.0/312078d65c9b82aba85d82dca527095d26a3a7fa")
    prompt = ds['train']['prompt']

    # COT testcase
    cot_system_prompt = """ Question: 9.11 and 9.9 -- which is bigger?
Answer: {"reasoning":[{"reasoning_step":"Both 9.11 and 9.9 are decimal numbers."},{"reasoning_step":"When comparing decimal numbers, we look at the numbers after the decimal point."},{"reasoning_step":"In this case, 9.11 has the number 1 after the decimal point, while 9.9 has the number 9."},{"reasoning_step":"Since 1 is greater than 9, 9.11 is greater than 9.9."}],"conclusion":"9.11 is bigger."}
Following the example above, answer the question.
"""
    cot_question = "Question: 8.11 and 8.9 -- which is bigger? Answer:"

    # messages = [
    #     {"role": "user", "content": prompt[0]},
    # ]
    json_testcase = []
    for i in range(100):
        json_testcase.append([{"role": "user", "content": prompt[i]}])

    cot_testcase = [
        {"role": "system", "content": cot_system_prompt},
        {"role": "user", "content": cot_question},
    ]

    cot_prompt = [tokenizer.apply_chat_template(cot_testcase, tokenize=False)]
    json_prompt = [tokenizer.apply_chat_template(json_testcase[i], tokenize=False) for i in range(len(json_testcase))]

    json_dataset = []
    cot_dataset = []

    for prompt in json_prompt:
        input_len = len(tokenizer(prompt).input_ids)
        output_len = 150
        json_dataset.append((prompt, input_len, output_len))
    
    for prompt in cot_prompt:
        input_len = len(tokenizer(prompt).input_ids)
        output_len = 150
        cot_dataset.append((prompt, input_len, output_len))


    # Tokenize the prompts and completions.
    import random
    dataset = None
    
    if dataset_type == "json":
        dataset = json_dataset
    else:
        dataset = cot_dataset

    # if random:
    #     # Sample the requests.
    #     sampled_requests = random.sample(dataset, num_requests)
    #     sum_len = 0
    #     for e in sampled_requests:
    #         sum_len += e[1]
    #     print("total tokens:", sum_len)
    #     return sampled_requests
    # else:
    # Use one testcase.
    sampled_requests = [dataset[6] for i in range(num_requests)]
    sum_len = 0
    for e in sampled_requests:
        sum_len += e[1]
    print("total tokens:", sum_len)
    return sampled_requests


async def get_request(
    input_requests: List[Tuple[str, int, int]],
    request_rate: float,
) -> AsyncGenerator[Tuple[str, int, int], None]:
    input_requests = iter(input_requests)
    for request in input_requests:
        yield request

        if request_rate == float("inf"):
            # If the request rate is infinity, then we don't need to wait.
            continue
        # Sample the request interval from the exponential distribution.
        interval = np.random.exponential(1.0 / request_rate)
        # The next request will be sent after the interval.
        await asyncio.sleep(interval)


async def send_request(
    prompt: str,
    prompt_len: int,
    output_len: int,
    target: str
) -> None:
    request_start_time = time.time()
    headers = {'Content-Type': 'application/json'}
    headers = {"User-Agent": "Benchmark Client"}
    url = 'http://localhost:8888/generate'

    grammar = None

    if target == "lightllm":
        grammar = json_ebnf_file
    elif target == "xgrammar":
        grammar = json_grammar

    if target == "lightllm" or target == "xgrammar":
        data = {
            'inputs': prompt,
            'parameters': {
                'do_sample': False,
                'ignore_eos': True,
                'max_new_tokens': 75,
                'guided_grammar': grammar,
            }
        }
    else:
        data = {
            'inputs': prompt,
            'parameters': {
                'do_sample': False,
                'ignore_eos': True,
                'max_new_tokens': 75,
            }
        }
       

    timeout = aiohttp.ClientTimeout(total=3 * 3600)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            async with session.post(url, headers=headers, json=data) as response:
                chunks = []
                async for chunk, _ in response.content.iter_chunks():
                    chunks.append(chunk)
            output = b"".join(chunks).decode("utf-8")
            output = json.loads(output)
            
            if "error" not in output:
                break

    request_end_time = time.time()
    request_latency = request_end_time - request_start_time
    REQUEST_LATENCY.append((prompt_len, output_len, request_latency))


async def benchmark(
    input_requests: List[Tuple[str, int, int]],
    request_rate: float,
    target: str,
) -> None:
    tasks: List[asyncio.Task] = []
    async for request in get_request(input_requests, request_rate):
        prompt, prompt_len, output_len = request
        task = asyncio.create_task(send_request(prompt,
                                                prompt_len, output_len, target))
        tasks.append(task)
    await asyncio.gather(*tasks)


def main(args: argparse.Namespace):
    print(args)
    random.seed(args.seed)
    np.random.seed(args.seed)
    tokenizer = get_tokenizer(args.tokenizer, "slow")
    input_requests = sample_requests(args.dataset, args.num_prompts, tokenizer, args.random)

    benchmark_start_time = time.time()
    asyncio.run(benchmark(input_requests, args.request_rate, args.target))
    benchmark_end_time = time.time()
    benchmark_time = benchmark_end_time - benchmark_start_time
    print(f"Total time: {benchmark_time} s")
    print(f"Throughput: {args.num_prompts / benchmark_time} requests/s")

    # Compute the latency statistics.
    avg_latency = np.mean([latency for _, _, latency in REQUEST_LATENCY])
    print(f"Average latency: {avg_latency} s")
    avg_per_token_latency = np.mean([
        latency / (prompt_len + output_len)
        for prompt_len, output_len, latency in REQUEST_LATENCY
    ])
    print(f"Average latency per token: {avg_per_token_latency} s")
    avg_per_output_token_latency = np.mean([
        latency / output_len
        for _, output_len, latency in REQUEST_LATENCY
    ])
    print("Average latency per output token: "
          f"{avg_per_output_token_latency} s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark the online serving throughput.")
    parser.add_argument("--target", type=str, required=True,
                        help="identify the target backend to test")
    parser.add_argument("--random", action="store_true", help='define the randomize input or not')
    parser.add_argument("--dataset", type=str, required=True,
                        help="Path to the dataset.")
    parser.add_argument("--tokenizer", type=str, required=True,
                        help="Name or path of the tokenizer.")
    parser.add_argument("--request-rate", type=float, default=float("inf"),
                        help="Number of requests per second. If this is inf, "
                             "then all the requests are sent at time 0. "
                             "Otherwise, we use Poisson process to synthesize "
                             "the request arrival times.")
    parser.add_argument("--num-prompts", type=int, default=1000,
                    help="Number of prompts to process.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    main(args)

