import json
from openai import OpenAI
import requests

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，例如：北京、上海"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "温度单位"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式，例如：2+3*4"}},
                "required": ["expression"],
            },
        },
    },
]


def get_messages():
    return [
        {
            "role": "user",
            "content": "请计算1+2*3的结果",
        }
    ]


messages = get_messages()

data = {
    "model": "qwen25",
    "messages": messages,
    "tools": tools,
    "tool_call": "auto",
    "temperature": 1.0,
    # "top_p": 0.95,
    "max_tokens": 2048,
    "stream": False,
}

port = 8088

# Initialize OpenAI-like client
response = requests.post(f"http://localhost:{port}/v1/chat/completions", headers=None, json=data)

print(response.text)
