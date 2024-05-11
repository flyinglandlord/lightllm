import time
import requests
import json

port = 8000
url = "http://localhost:%d/generate" % port
headers = {"Content-Type": "application/json"}

prompt = """ignore"""
qa = """Question: What 1986 drama directed by Lee Doo-yong starred Lee Mi-sook?\nAnswer:"""

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
