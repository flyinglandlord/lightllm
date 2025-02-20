from outlines import models, generate
from transformers import AutoTokenizer
import time
from vllm.sampling_params import SamplingParams
# from vllm.decoding_config import DecodingConfig
from datasets import load_dataset

tokenizer = AutoTokenizer.from_pretrained("/mnt/nvme0/models/Meta-Llama-3-8B/")

ds = load_dataset("/home/chenjunyi/.cache/huggingface/datasets/NousResearch___json-mode-eval/default/0.0.0/312078d65c9b82aba85d82dca527095d26a3a7fa")
prompt = ds['train']['prompt']


json_grammar = r"""
    ?start: value

    ?value: object
    | array
    | string
    | SIGNED_NUMBER      -> number
    | "true"             -> true
    | "false"            -> false
    | "null"             -> null

    array  : "[" [value ("," value)*] "]"
    object : "{" [pair ("," pair)*] "}"
    pair   : string ":" value

    string : "\"" /([a-zA-Z\x20\x21\x23\x24\x25\x26\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30-\x39\x41-\x5a\x5e\x5f\x60\x61-\x7a\x7e])/* "\"" WS

    %import common.SIGNED_NUMBER
    %import common.WS

    %ignore WS
"""

cot_grammar = r"""
    ?start: root

    ?root: "{" reasoning "," conclusion "}"

    ?reasoning: "\"" "reasoning" "\"" ":" "[" reasoning_steps "]"

    ?reasoning_steps: reasoning_step ("," reasoning_step)*

    ?reasoning_step: "{" "\"" "reasoning_step" "\"" ":" string "}"

    ?conclusion: "\"" "conclusion" "\"" ":" string

    ?string: "\"" /[a-zA-Z\x20\x21\x23\x24\x25\x26\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30-\x39\x41-\x5a\x5e\x5f\x60\x61-\x7a\x7e]+/ "\""

    ?ws: (" " | "\t" | "\n" | "\r")+
"""

arithmetic_grammar = """
    ?start: expression

    ?expression: term (("+" | "-") term)*

    ?term: factor (("*" | "/") factor)*

    ?factor: NUMBER
           | "-" factor
           | "(" expression ")"

    %import common.NUMBER
"""

system_prompt = open("/mnt/nvme0/chenjunyi/project/lightllm/test/format_out/system.md", "r").read()
user_input = open("/mnt/nvme0/chenjunyi/project/lightllm/test/format_out/user.md", "r").read()

cot_system_prompt = """ Question: 9.11 and 9.9 -- which is bigger?
Answer: {"reasoning":[{"reasoning_step":"Both 9.11 and 9.9 are decimal numbers."},{"reasoning_step":"When comparing decimal numbers, we look at the numbers after the decimal point."},{"reasoning_step":"In this case, 9.11 has the number 1 after the decimal point, while 9.9 has the number 9."},{"reasoning_step":"Since 1 is greater than 9, 9.11 is greater than 9.9."}],"conclusion":"9.11 is bigger."}
Following the example above, answer the question.
"""

# messages = [
#     {"role": "user", "content": prompt[0]},
# ]
messages = []
for i in range(80):
    messages.append([{"role": "user", "content": prompt[i]}])

cot_question = [
    {"role": "system", "content": cot_system_prompt},
    {"role": "user", "content": "Question: 8.11 and 8.9 -- which is bigger? Answer:"}]

inputs = tokenizer.apply_chat_template(cot_question, tokenize=False)
# inputs = [tokenizer.apply_chat_template(messages[i], tokenize=False) for i in range(len(messages))]


# model = models.vllm("/mnt/nvme0/models/Meta-Llama-3-8B/", device='cuda', gpu_memory_utilization=0.5)
# generator = generate.cfg(model, cot_grammar)

# params = SamplingParams(n=1, frequency_penalty=1., min_tokens=2)
# st = time.time()
# answer = generator(inputs, sampling_params=params)
# ed = time.time()
# print('Output: ', answer)
# output_len = len(tokenizer(answer).input_ids)
# print('Output Length: ', output_len)
# print('Mean Per token time: ', (ed - st) / output_len)
# model = models.transformers("/mnt/nvme0/models/Meta-Llama-3-8B/", device="cuda")
# generator = generate.cfg(model, cot_grammar)

# input_ids = tokenizer.tokenize(inputs)

# st = time.time()
# sequence = model(inputs)
# ed = time.time()
# print(ed - st)
# print(sequence)
# output_len = len(tokenizer(sequence).input_ids)
# print('Output Length: ', output_len)
# print('Mean Per token time: ', (ed - st) / output_len)

from vllm import LLM
from vllm.sampling_params import GuidedDecodingParams

llm = LLM(model="/mnt/nvme0/models/llama2-70b-chat", device='cuda', gpu_memory_utilization=0.5, guided_decoding_backend='outlines', tensor_parallel_size=4)

guided_decoding_params = GuidedDecodingParams(grammar=cot_grammar)
sampling_params = SamplingParams(guided_decoding=guided_decoding_params, temperature=0.0, max_tokens=1)
# sampling_params = SamplingParams(temperature=0.0)
st = time.time()
outputs = llm.generate(
    prompts=[inputs],
    sampling_params=sampling_params
)
# 8b model
# cot grammar
# 1009.3176057338715 114
# 11.013428688049316 1

#ebnf grammar
# 24.802886486053467 2
# 16.137094020843506 1

# 70b model
# cot grammar
# 4.591622829437256 2
# 3.0249314308166504 1

#ebnf grammar
# 6.332478046417236 2
# 4.135905504226685 1
ed = time.time()
print(outputs[0].outputs[0].text)
output_len = len(tokenizer(outputs[0].outputs[0].text).input_ids)
print(ed - st, output_len)
print((ed-st) / output_len)