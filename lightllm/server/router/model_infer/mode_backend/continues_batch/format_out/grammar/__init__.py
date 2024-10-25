# 文法表达形式限制
# 1. 起始表示符一定是 S‘
# 2. 不支持 "ε" 表达式


grammar = [
    ("S'", ["S"]),
    ("S", ["A", "B"]),
    ("A", ["a", "A"]),
    ("A", ["ε"]),
    ("B", ["b", "B"]),
    ("B", ["ε"]),
]
