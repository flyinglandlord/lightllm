import time
import requests
import json
import threading
from transformers import AutoTokenizer
from datasets import load_dataset

tokenizer = AutoTokenizer.from_pretrained("/mnt/nvme0/models/Meta-Llama-3-8B/")

ds = load_dataset("/home/chenjunyi/.cache/huggingface/datasets/NousResearch___json-mode-eval/default/0.0.0/312078d65c9b82aba85d82dca527095d26a3a7fa")
prompt = ds['train']['prompt']

class RequestThread(threading.Thread):
    def __init__(self, url, headers, data):
        threading.Thread.__init__(self)
        self.url = url
        self.headers = headers
        self.data = data

    def run(self):
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.data))
        if response.status_code == 200:
            print(response.json())
        else:
            print("Error:", response.status_code, response.text)


url = "http://localhost:9999/generate"
headers = {"Content-Type": "application/json"}
json_grammar_ebnf_str = r"""
root ::= basic_array | basic_object
basic_any ::= basic_number | basic_string | basic_boolean | basic_null | basic_array | basic_object
basic_integer ::= ("0" | "-"? [1-9] [0-9]*) ".0"?
basic_number ::= ("0" | "-"? [1-9] [0-9]*) ("." [0-9]+)? ([eE] [+-]? [0-9]+)?
basic_string ::= (([\"] basic_string_1 [\"]))
basic_string_1 ::= "" | [^"\\\x00-\x1F] basic_string_1 | "\\" escape basic_string_1
escape ::= ["\\/bfnrt] | "u" [A-Fa-f0-9] [A-Fa-f0-9] [A-Fa-f0-9] [A-Fa-f0-9]
basic_boolean ::= "true" | "false"
basic_null ::= "null"
basic_array ::= "[" ("" | ws basic_any (ws "," ws basic_any)*) ws "]"
basic_object ::= "{" ("" | ws basic_string ws ":" ws basic_any ( ws "," ws basic_string ws ":" ws basic_any)*) ws "}"
ws ::= [ \n\t]*
"""
json_grammar_ebnf_file = "/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/grammar/json_grammar.ebnf"
chain_of_thought_ebnf_file = "/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/grammar/chain_of_thought.ebnf"

json_schema_str = r"""
{
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "金额": {
                "type": "number"
            },
            "标题": {
                "type": "string"
            },
            "类型": {
                "type": "string"
            },
            "大类": {
                "type": "string"
            },
            "小类": {
                "type": "string"
            },
            "日期": {
                "type": "string"
            },
            "时间": {
                "type": "string"
            }
        },
        "required": [
            "金额",
            "标题",
            "类型",
            "大类",
            "小类",
            "时间"
        ]
    }
}
"""

person_schema = r"""{
  "title": "Person",
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "age": {
      "type": "integer",
    }
  },
  "required": ["name", "age"]
}
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
    # {"role": "system", "content": cot_system_prompt},
    {"role": "user", "content": "Question: 8.11 and 8.9 -- which is bigger? Answer:"}]

# inputs = tokenizer.apply_chat_template(cot_question, tokenize=False)
inputs = [tokenizer.apply_chat_template(cot_question, tokenize=False) for i in range(len(messages))]

for i in range(512):
    data = {
        "inputs": inputs[6],
        # 'temperature': 0.1,
        "parameters": {
            "do_sample": False,
            # "guided_grammar": json_grammar_ebnf_file,
            "max_new_tokens": 150,
        },
    }
    thread = RequestThread(url, headers, data)
    thread.start()

# time.sleep(2)

# for i in range(20):
#     data = {
#         "inputs": "12-(25+16)*7=",
#         "parameters": {
#             "do_sample": False,
#             "ignore_eos": True,
#             "max_new_tokens": 200,
#             "guided_grammar": r"""root ::= (expr "=" term)+
# expr  ::= term ([-+*/] term)*
# term  ::= num | "(" expr ")"
# num   ::= [0-9]+""",
#         },
#     }
#     thread = RequestThread(url, headers, data)
#     thread.start()
