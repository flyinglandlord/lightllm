import time
import requests
import json

port = 8000
url = 'http://localhost:%d/generate' % port
headers = {'Content-Type': 'application/json'}

prompt = "The grass is green. The sky is blue. " * 400 + "The pass key is 71432. Remember it. 71432 is the pass key. " + "The sky is blue. The grass is green. " * 400 + \
             "The pass key is also 12086. Remember it. 12086 is also the pass key. " + "The grass is green. The sky is blue. " * 400
qa = """Question: What are the pass keys?\nAnswer:"""

data = {
    'inputs': prompt+qa,
    "parameters": {
        'do_sample': False,
        'ignore_eos': False,
        'max_new_tokens': 18,
    }
}
response = requests.post(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    print(response.json())
else:
    print('Error:', response.status_code, response.text)