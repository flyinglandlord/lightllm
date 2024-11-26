import time
import requests
import json
import threading


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
paper0 = ""
paper1 = ""
paper2 = ""
paper3 = ""
input = (
    "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. \
        You are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
    + paper0
    + paper1
    + paper2
    + paper3
    + "Sumarize the information above in JSON format."
    + "<|im_end|>\n<|im_start|>assistant\n"
)
for i in range(1):
    data = {
        "inputs": input,
        # 'temperature': 0.1,
        "parameters": {
            "min_new_tokens": 1024,
            "max_new_tokens": 1024,
            "lr1_grammar": "/data/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/ \
                continues_batch/format_out/grammar/json_grammar.ebnf",
            "do_sample": False,
        },
    }
    thread = RequestThread(url, headers, data)
    thread.start()

# time.sleep(2)

# for i in range(20):
#     data = {
#         'inputs': 'San Francisco is a',
#         'parameters': {
#             'do_sample': False,
#             'ignore_eos': True,
#             'max_new_tokens': 200,
#         }
#     }
#     thread = RequestThread(url, headers, data)
#     thread.start()
