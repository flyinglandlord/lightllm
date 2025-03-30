import torch
import time
from transformers import AutoTokenizer

from lightllm.server.router.model_infer.infer_batch import DPDAStructure
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.core import compute_graph
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.dpda import DPDA, LRGraph
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.grammar_parser import (
    fix_grammar,
    parse_ebnf,
)

test_case_id = 9

tokenizer = AutoTokenizer.from_pretrained("/mnt/nvme0/models/Meta-Llama-3.1-8B-Instruct")
lr1_grammar_text = open(f"/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/json_schema/grammar/grammar{test_case_id}.ebnf").read()
#lr1_grammar_text = open(f"/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/grammar/json_grammar.ebnf").read()
parsed_grammar = parse_ebnf(lr1_grammar_text)
grammar = parsed_grammar.get_grammar()
lr1_grammar = fix_grammar(grammar)
lr1_grammar_start_symbol = "root"
in_str = open(f"/mnt/nvme0/chenjunyi/project/lightllm/lightllm/server/router/model_infer/mode_backend/continues_batch/format_out/json_schema/sample/{test_case_id}.txt").read()

torch.set_deterministic_debug_mode(True)
torch.manual_seed(0)

if __name__ == '__main__':
    dpda_struct = DPDAStructure()
    start_time = time.time()
    dpda_struct.graph = compute_graph(
        lr1_grammar, start_symbol=lr1_grammar_start_symbol
    )
    # print(dpda_struct.graph)
    # graph.check_lr1()
    dpda_struct.lr1_graph = LRGraph(dpda_struct.graph)
    dpda_struct.dpda = DPDA(lr_graph=dpda_struct.lr1_graph)
    dpda_struct.dpda.remove_no_input_node_to_edges()
    print(f"preprocess dpda cost: {time.time() - start_time}")

    start_time = time.time()
    (
        dpda_struct.shift_table,
        dpda_struct.edge_num_table,
        dpda_struct.push_table,
        dpda_struct.pop_table,
        dpda_struct.dest_table,
        dpda_struct.symbol_to_id,
    ) = dpda_struct.dpda.dump_to_tensor()
    print(f"save dpda to tensor cost: {time.time() - start_time}")

    start_time = time.time()
    vocab = tokenizer.get_vocab()
    sorted_vocab = dict(sorted(vocab.items(), key=lambda item: item[1]))
    dpda_struct.check_str = list(sorted_vocab.keys())
    other_token_id = len(dpda_struct.symbol_to_id)
    # print(dpda_struct.symbol_to_id)
    _input_sequences = []
    _sequence_len = []
    for s in dpda_struct.check_str:
        _input_sequences.append(
            [dpda_struct.symbol_to_id[c] if c in dpda_struct.symbol_to_id else other_token_id for c in s]
        )
        _sequence_len.append(len(s))
    dpda_struct.sequence_len = torch.tensor(_sequence_len, dtype=torch.int32, device="cuda")
    dpda_struct.input_sequences = torch.empty(
        (len(_input_sequences), torch.max(dpda_struct.sequence_len)), dtype=torch.int32, device="cuda"
    )
    for i, s in enumerate(_input_sequences):
        dpda_struct.input_sequences[i, : len(s)] = torch.tensor(s, dtype=torch.int32, device="cuda")
    print(f"preprocess vocabulary cost: {time.time() - start_time}")

    dpda_struct.dpda.accept(in_str)
    print('')