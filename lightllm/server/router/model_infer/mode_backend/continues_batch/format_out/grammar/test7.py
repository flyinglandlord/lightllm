from core import compute_first, compute_graph
from dpda import NT, LRGraph, Graph, DPDA
from dpda import T
from example_grammar import expr_grammar, json_grammar, string_grammar


def create_grammer():
    grammar = [
        (NT("S'"), [NT("S")]),
        (NT("S"), [NT("L"), T("="), NT("R")]),
        (NT("S"), [NT("R")]),
        (NT("L"), [T("*"), NT("R")]),
        (NT("L"), [T("i")]),
        (NT("R"), [NT("L")]),
    ]
    return grammar


grammar = create_grammer()

ans = compute_first(grammar)
print(ans)

graph = compute_graph(grammar=grammar, start_symbol="S'")

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
    # """{"name":"Alice","age":30,"address":{"city":"Wonderland"},"isStudent":false,"scores":[85,92,88]}""",
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
