from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.core import (
    compute_first,
    compute_graph,
)
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.dpda import (
    NT,
    LRGraph,
    Graph,
    DPDA,
)
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.dpda import T
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.example_grammar import (
    expr_grammar,
    json_grammar,
    string_grammar,
)


def create_grammer():
    # grammar = [
    #     (NT("S'"), [NT("S")]),
    #     (NT("S"), [T("a"), T("b")]),
    #     (NT("S"), [T("a"), NT("S"), T("b")]),
    # ]
    return json_grammar


grammar = create_grammer()

ans = compute_first(grammar)
print(ans)

graph = compute_graph(grammar=grammar, start_symbol="JSON")

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
    '{"\\"dfsf":"dfdf"}',
    '{"}":"{"}'
    # """{"name":"Alice","age":30,"address":{"city":"Wonderland"},"isStudent":false,"scores":[85,92,88]}""",
    # """[{"name":"Alice","age":30,"address":{"city":"Wonderland"},"isStudent":false,"scores":[85,92,88]}]"""
    # "1*(1/(2*2))",
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
# for in_str in [
#     """{"\\n\\\"name\\\":\\\"BillClinton\\\",\\n\\\"age\\\":25,\\n\\\"location\\\":\\\"NewYorkCity\\\",\\n\\\"political_preference\\\":\\\"SupportsDonaldTrump\\\",\\n\\\"phone_number\\\":\\\"1443244334\\\"\":\"a\"}""",
# ]:
#     try:
#         dpda.accept(in_str)
#         print(f"{in_str} accepted")
#         assert False
#     except:
#         print(f"{in_str} not accepted")
#         assert True

# print(dpda.direct_jump_node_id_to_dpda_edges)
