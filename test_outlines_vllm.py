import outlines
from vllm.sampling_params import SamplingParams
import time

# step_by_step_math_grammar = """
#     ?start: calculation
#     ?calculation: steps answer

#     ?steps: step | step steps
#     ?step: expression "=" result "\t"

#     ?expression: term (("+" | "-") term)*
#     ?term: factor (("*" | "/") factor)*
#     ?factor: NUMBER
#            | "-" factor
#            | "(" expression ")"

#     ?answer: "Answer:" result

#     ?result: NUMBER

#     %import common.NUMBER
# """

# arithmetic_grammar = """
#     ?start: expression
#     ?expression: term (("+" | "-") term)*
#     ?term: factor (("*" | "/") factor)*
#     ?factor: NUMBER
#            | "-" factor
#            | "(" expression ")"

#     %import common.NUMBER
# """

# json_grammar = """
#     ?start: object
#     ?object: "{" ws ( string ":" ws value ("," ws string ":" ws value)* )? "}"
#     ?value: object | array | string | number | ("true" | "false" | "null") ws
#     ?array:  "[" ws ( value ("," ws value)* )? "]" ws
#     ?string: /\"/ /[ \t!#-\[\]-~]/* /\"/ ws
#     ?number: ("-"? (/[0-9]/ | /[1-9]/ /[0-9]/*)) ("." /[0-9]/+)? (/[eE]/ /[-+]/? /[0-9]/+)? ws
#     ?ws: (/[ \t]/ ws)?
# """
arithmetic_grammar = ""

model = outlines.models.vllm("/data/chenjunyi/models/qwen2-7b-chat")
generator = outlines.generate.cfg(model, arithmetic_grammar)
# generator = outlines.generate.text(model)
# params = SamplingParams(n=1, temperature=0.0, min_tokens=2, max_tokens=5)
# sequence = generator("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud.
# You are a helpful assistant.<|im_end|>\n<|im_start|>user\nAlice had 4 apples and Bob ate 2.
# Write an expression to calculate how many apples does Alice have.
# <|im_end|>\n<|im_start|>assistant\n", sampling_params=params)

params = SamplingParams(n=1, temperature=0.0, min_tokens=2, max_tokens=128)
st = time.time()
# sequence = generator("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.
# <|im_end|>\n<|im_start|>user\nPlease follow the JSON format to give the answer of the following question.
# What is AI?<|im_end|>\n<|im_start|>assistant\n", sampling_params=params)
sequence = generator(
    "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n<|im_start|>user \
        \nAlice had 4 apples and Bob ate 2. Write only expressions to calculate how many apples does Alice have. \
        <|im_end|>\n<|im_start|>assistant\n",
    sampling_params=params,
)
ed = time.time()
print(ed - st)
print(sequence)
# (8-2)
# 3.9325404167175293
# 0.196915864944458
