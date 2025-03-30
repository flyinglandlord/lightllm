from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.core import (
    compute_first,
    compute_graph,
    Graph,
    NT,
    T,
)
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.dpda import LRGraph, DPDA
from example_grammar import expr_grammar, json_grammar, string_grammar
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.grammar_parser import (
    fix_grammar,
    parse_ebnf,
)

def create_grammer():
    with open("/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/grammar/chain_of_thought.ebnf", "r") as f:
        input_text = f.read()
        parsed_grammar = parse_ebnf(input_text)
        grammar = parsed_grammar.get_grammar()
        grammar = fix_grammar(grammar)
        return grammar

grammar = create_grammer()
for l in grammar:
    print(l)
ans = compute_first(grammar)
print(ans)

graph = compute_graph(grammar=grammar, start_symbol="root")

print(graph)

graph_str = graph.to_mermaid()
with open("mermaid.md", mode="+w") as file:
    file.write(graph_str)
    file.flush()

graph.visit_print()
graph.check_lr1()

lr_graph = LRGraph(graph)
dpda = DPDA(lr_graph=lr_graph)
print(dpda)

dpda.remove_no_input_node_to_edges()

with open("mermaid1.md", mode="+w") as file:
    file.write(dpda.to_mermaid())

# accept test
for in_str in [
    """{"reasoning":[{"reasoning_step":"Both 9.11 and 9.9 are decimal numbers."},{"reasoning_step":"When comparing decimal numbers, we look at the numbers after the decimal point."}],"conclusion":"9.11 is bigger."}""",
    # """[{"name":"Alice","age":30,"address":{"city":"Wonderland"},"isStudent":false,"scores":[85,92,88]}]"""
    #"1*(1/(2*2))",
    # "1*(1.34/2*(2))",
]:
    try:
        dpda.accept(in_str)
        print(f"{in_str} accepted")
        assert True
    except:
        print(f"{in_str} not accepted")
        assert False

print("####################")
# not accept test
for in_str in [".untracked", "2*(2/2*2))"]:
    try:
        dpda.accept(in_str)
        print(f"{in_str} accepted")
        assert False
    except:
        print(f"{in_str} not accepted")
        assert True


# print(dpda.direct_jump_node_id_to_dpda_edges)
