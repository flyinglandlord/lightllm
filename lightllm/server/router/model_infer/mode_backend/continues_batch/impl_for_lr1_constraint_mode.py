import os
import shutil
import time
import torch

from .impl import ContinuesBatchBackend
from lightllm.utils.infer_utils import calculate_time, mark_start, mark_end
from lightllm.server.io_struct import FinishStatus
from lightllm.server.router.model_infer.infer_batch import (
    DPDAStructure,
    InferBatch,
    InferReq,
    InferSamplingParams,
)
from .pre_process import prepare_prefill_inputs, prepare_decode_inputs
from .post_process import sample
from lightllm.server.tokenizer import get_tokenizer
from typing import List
from lightllm.utils.log_utils import init_logger

from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.core import (
    compute_first,
    compute_graph,
    Graph,
    NT,
    T,
)
from lightllm.server.router.model_infer.mode_backend.continues_batch.format_out.grammar.dpda import LRGraph, DPDA
from lightllm_constraint_decode_kernel import check_dpda

logger = init_logger(__name__)


class LR1GrammarConstraintBackend(ContinuesBatchBackend):
    def __init__(self) -> None:
        super().__init__()
        self.dpda_cache = {}

    def init_custom(self):
        from outlines.models.transformers import TransformerTokenizer

        self.tokenizer = TransformerTokenizer(
            get_tokenizer(self.args.model_dir, self.args.tokenizer_mode, trust_remote_code=self.args.trust_remote_code)
        )

        self.eos_token_ids = []
        self.eos_token_ids.append(self.tokenizer.eos_token_id)
        self.eos_token_ids.extend(self.args.eos_id)
        pass

    @calculate_time(show=True, min_cost_ms=300)
    def preprocess_dpda(self, sample_params):
        dpda_struct = DPDAStructure()
        start_time = time.time()
        dpda_struct.graph = compute_graph(
            sample_params.lr1_grammar, start_symbol=sample_params.lr1_grammar_start_symbol
        )
        # graph.check_lr1()
        dpda_struct.lr1_graph = LRGraph(dpda_struct.graph)
        dpda_struct.dpda = DPDA(lr_graph=dpda_struct.lr1_graph)
        (
            dpda_struct.shift_table,
            dpda_struct.edge_num_table,
            dpda_struct.push_table,
            dpda_struct.pop_table,
            dpda_struct.dest_table,
            dpda_struct.symbol_to_id,
        ) = dpda_struct.dpda.dump_to_tensor()
        print(f"preprocess dpda cost: {time.time() - start_time}")

        start_time = time.time()
        dpda_struct.check_str = list(self.tokenizer.tokenizer.get_vocab().keys())
        other_token_id = len(dpda_struct.symbol_to_id)
        print(dpda_struct.symbol_to_id)
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

        sample_params.dpda = dpda_struct
        return sample_params

    @calculate_time(show=False, min_cost_ms=300)
    def prefill_batch(self, batch_id):
        output_dict = {}
        batch: InferBatch = self.cache.pop(batch_id)
        kwargs, run_reqs = prepare_prefill_inputs(batch, self.radix_cache, self.model.mem_manager)
        run_reqs: List[InferReq] = run_reqs

        logics = self.model.forward(**kwargs)
        mask = torch.ones_like(logics, dtype=torch.bool)

        for i, run_obj in enumerate(run_reqs):
            sample_params = run_obj.sampling_param
            if sample_params.lr1_grammar is not None:
                if self.dpda_cache.get(sample_params.lr1_grammar_name) is None:
                    sample_params = self.preprocess_dpda(sample_params)
                    self.dpda_cache[sample_params.lr1_grammar_name] = sample_params.dpda
                else:
                    print("dpda cache hit")
                    sample_params.dpda = self.dpda_cache[sample_params.lr1_grammar_name]
                    sample_params.dpda.lr1_stack = [0]
                    sample_params.dpda.lr1_current_node_id = 0
                self._mask_req_out_token(i, run_obj, mask, prefill=True)

        logics[mask] = -1000000.0

        next_token_ids, next_token_probs = sample(logics, run_reqs, self.eos_id)
        next_token_ids = next_token_ids.detach().cpu().numpy()
        print(f"selected token: {self.tokenizer.tokenizer.convert_ids_to_tokens([int(next_token_ids[0])])[0]}")
        next_token_logprobs = torch.log(next_token_probs).detach().cpu().numpy()

        for req_obj, next_token_id, next_token_logprob in zip(run_reqs, next_token_ids, next_token_logprobs):
            req_obj.cur_kv_len = len(req_obj.input_token_ids)
            req_obj.input_token_ids.append(next_token_id)
            req_obj.out_token_id_count[next_token_id] += 1
            req_obj.update_finish_status(self.eos_id)

            self._handle_req_ans(req_obj, next_token_id, next_token_logprob, output_dict)

        self.cache[batch.batch_id] = batch
        return output_dict

    @calculate_time(show=True, min_cost_ms=200)
    def decode_batch(self, batch_id):
        output_dict = {}
        batch: InferBatch = self.cache.pop(batch_id)
        kwargs, run_reqs = prepare_decode_inputs(batch, self.radix_cache)
        run_reqs: List[InferReq] = run_reqs

        logits = self.model.forward(**kwargs)
        # print(f"decode logits: {logits}")
        all_has_no_constraint = all([e.sampling_param.lr1_grammar is None for e in run_reqs])
        if not all_has_no_constraint:
            mask = torch.ones_like(logits, dtype=torch.bool)
            for i, run_obj in enumerate(run_reqs):
                self._mask_req_out_token(i, run_obj, mask)
            logits[mask] = -1000000.0

        next_token_ids, next_token_probs = sample(logits, run_reqs, self.eos_id)
        next_token_ids = next_token_ids.detach().cpu().numpy()
        # print(f"selected token: {self.tokenizer.tokenizer.convert_ids_to_tokens([int(next_token_ids[0])])[0]}")
        next_token_logprobs = torch.log(next_token_probs).detach().cpu().numpy()

        for req_obj, next_token_id, next_token_logprob in zip(run_reqs, next_token_ids, next_token_logprobs):
            req_obj: InferReq = req_obj
            req_obj.cur_kv_len = len(req_obj.input_token_ids)
            req_obj.input_token_ids.append(next_token_id)
            req_obj.out_token_id_count[next_token_id] += 1
            req_obj.update_finish_status(self.eos_id)

            self._handle_req_ans(req_obj, next_token_id, next_token_logprob, output_dict)

        self.cache[batch.batch_id] = batch
        return output_dict

    def _handle_req_ans(self, req_obj: InferReq, next_token_id, next_token_logprob, output_dict):
        next_token_id = int(next_token_id)
        next_token = self.tokenizer.tokenizer.convert_ids_to_tokens([next_token_id])[0]
        if req_obj.sampling_param.lr1_grammar is not None and next_token_id not in self.eos_token_ids:
            (
                ok,
                req_obj.sampling_param.dpda.lr1_stack,
                req_obj.sampling_param.dpda.lr1_current_node_id,
            ) = req_obj.sampling_param.dpda.dpda.try_shift(
                input_str=next_token,
                current_stack=req_obj.sampling_param.dpda.lr1_stack,
                current_node_id=req_obj.sampling_param.dpda.lr1_current_node_id,
            )
            if not ok:
                assert False, f"shift failed: {next_token}"
                # req_obj.finish_status = FinishStatus.FINISHED_STOP

        if next_token_id in self.eos_token_ids:
            req_obj.finish_status = FinishStatus.FINISHED_STOP

        metadata = {
            "id": next_token_id,
            "logprob": float(next_token_logprob),
        }
        output_dict[req_obj.r_id] = (
            req_obj.req_status,
            req_obj.cur_kv_len,
            req_obj.get_output_len(),
            [(next_token_id, metadata)],
            req_obj.finish_status.value,
            None,
        )
        return

    def _mask_req_out_token(self, i, run_obj: InferReq, mask, prefill=False):
        sample_params = run_obj.sampling_param
        if sample_params.lr1_grammar is not None:
            vocab_size = sample_params.dpda.input_sequences.shape[0]
            current_state = torch.tensor(
                [sample_params.dpda.lr1_current_node_id] * vocab_size, dtype=torch.int32, device="cuda"
            )
            current_stack = torch.tensor(sample_params.dpda.lr1_stack, dtype=torch.int32, device="cuda")
            check_dpda(
                sample_params.dpda.input_sequences,
                sample_params.dpda.sequence_len,
                sample_params.dpda.shift_table,
                sample_params.dpda.edge_num_table,
                sample_params.dpda.push_table,
                sample_params.dpda.pop_table,
                sample_params.dpda.dest_table,
                current_stack,
                current_state,
                50,
            )
            # if torch.sum(current_state != -1) <= 500:
            #     for j in range(len(current_state)):
            #         if current_state[j] != -1:
            #             print(f"accepted: {sample_params.dpda.check_str[j]}")
            mask[i][:vocab_size] = current_state == -1
            mask[i][self.eos_token_ids] = False
