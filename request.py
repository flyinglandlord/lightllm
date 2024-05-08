import time
import requests
import json

port = 8000
url = "http://localhost:%d/generate" % port
headers = {"Content-Type": "application/json"}

prompt = """aaa"""
qa = """Question: Which city is under Jining, Kaiyuan, Liaoning or Yanzhou District?\nAnswer:"""

data = {
    "inputs": prompt + qa,
    "parameters": {
        "do_sample": False,
        "ignore_eos": False,
        "max_new_tokens": 18,
    },
}
response = requests.post(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json())
else:
    print("Error:", response.status_code, response.text)
