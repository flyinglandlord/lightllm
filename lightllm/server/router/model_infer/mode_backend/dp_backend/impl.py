import torch
import torch.distributed as dist
import numpy as np
from typing import List, Tuple
from lightllm.server.router.model_infer.mode_backend.base_backend import ModeBackend
from lightllm.utils.infer_utils import set_random_seed
from lightllm.utils.infer_utils import calculate_time, mark_start, mark_end
from lightllm.server.router.model_infer.infer_batch import g_infer_context, InferReq, InferSamplingParams
from lightllm.server.core.objs import FinishStatus
from lightllm.utils.log_utils import init_logger
from lightllm.server.router.model_infer.mode_backend.generic_post_process import sample
from lightllm.utils.envs_utils import get_env_start_args


class DPChunkedPrefillBackend(ModeBackend):
    def __init__(self) -> None:
        super().__init__()
        """
        DPChunkedPrefillBackend 是DP的chuncked prefill 的单机实现，并不是标准的chunked prefill
        实现，这个模式最佳使用方式需要和 PD 分离模式进行配合。
        """
        self.enable_decode_microbatch_overlap = get_env_start_args().enable_decode_microbatch_overlap
        self.enable_prefill_microbatch_overlap = get_env_start_args().enable_prefill_microbatch_overlap
        pass

    def init_custom(self):
        self.reduce_tensor = torch.tensor([0], dtype=torch.int32, device="cuda", requires_grad=False)
        # 这个地方预先进行一次 prefill 推理，主要是为了填充后续fake请求的第一个token位置，因为填充的decode请求
        # 在推理的时候至少是两个token，1个是已经有kv的token，一个是等待计算kv的token，然后生成第三个token，这几个
        # token 实际引用的都是 g_infer_context.req_manager.mem_manager.HOLD_TOKEN_MEMINDEX，但是需要初始化排除
        # nan 值，避免后续构建的fake请求在计算的过程中出现计算错误。
        from .pre_process import padded_prepare_prefill_inputs

        kwargs, run_reqs, padded_req_num = padded_prepare_prefill_inputs([], 1, is_multimodal=self.is_multimodal)
        self.model.forward(**kwargs)
        assert len(run_reqs) == 0 and padded_req_num == 1
        return

    def prefill(self, reqs: List[Tuple]):
        self._init_reqs(reqs, init_req_obj=False)
        return

    def decode(self):
        uninit_reqs, aborted_reqs, ok_finished_reqs, prefill_reqs, decode_reqs = self._get_classed_reqs(
            g_infer_context.infer_req_ids
        )

        if aborted_reqs:
            g_infer_context.filter_reqs(aborted_reqs)

        current_dp_prefill_num = len(prefill_reqs)
        self.reduce_tensor.fill_(current_dp_prefill_num)
        dist.all_reduce(self.reduce_tensor, op=dist.ReduceOp.MAX, group=None, async_op=False)
        max_prefill_num = self.reduce_tensor.item()
        if max_prefill_num != 0:
            if not self.enable_prefill_microbatch_overlap:
                self.normal_prefill_reqs(prefill_reqs, max_prefill_num, uninit_reqs, ok_finished_reqs)
            else:
                self.overlap_prefill_reqs(prefill_reqs, max_prefill_num, uninit_reqs, ok_finished_reqs)

        self.reduce_tensor.fill_(len(decode_reqs))
        dist.all_reduce(self.reduce_tensor, op=dist.ReduceOp.MAX, group=None, async_op=False)
        max_decode_num = self.reduce_tensor.item()
        if max_decode_num != 0:
            if not self.enable_decode_microbatch_overlap:
                self.normal_decode(decode_reqs, max_decode_num, uninit_reqs, ok_finished_reqs)
            else:
                self.overlap_decode(decode_reqs, max_decode_num, uninit_reqs, ok_finished_reqs)

        self._overlap_req_init_and_filter(uninit_reqs=uninit_reqs, ok_finished_reqs=ok_finished_reqs, clear_list=True)
        return

    def normal_prefill_reqs(self, prefill_reqs: List[InferReq], max_prefill_num: int, uninit_reqs, ok_finished_reqs):
        from .pre_process import padded_prepare_prefill_inputs

        kwargs, run_reqs, padded_req_num = padded_prepare_prefill_inputs(
            prefill_reqs, max_prefill_num, is_multimodal=self.is_multimodal
        )
        logits = self.model.forward(**kwargs)
        self._overlap_req_init_and_filter(uninit_reqs=uninit_reqs, ok_finished_reqs=ok_finished_reqs, clear_list=True)
        if len(run_reqs) != 0:
            logits = logits[0 : len(run_reqs), :]
            next_token_ids, next_token_probs = sample(logits, run_reqs, self.eos_id)
            next_token_ids = next_token_ids.detach().cpu().numpy()
            next_token_logprobs = torch.log(next_token_probs).detach().cpu().numpy()
            self._post_handle(
                run_reqs, next_token_ids, next_token_logprobs, is_chuncked_mode=True, do_filter_finished_reqs=False
            )
        return

    def normal_decode(self, decode_reqs: List[InferReq], max_decode_num: int, uninit_reqs, ok_finished_reqs):
        from .pre_process import padded_prepare_decode_inputs

        kwargs, run_reqs, padded_req_num = padded_prepare_decode_inputs(
            decode_reqs, max_decode_num, is_multimodal=False
        )
        logits = self.model.forward(**kwargs)

        self._overlap_req_init_and_filter(uninit_reqs=uninit_reqs, ok_finished_reqs=ok_finished_reqs, clear_list=True)

        if len(run_reqs) != 0:
            logits = logits[0 : len(run_reqs), :]
            next_token_ids, next_token_probs = sample(logits, run_reqs, self.eos_id)
            next_token_ids = next_token_ids.detach().cpu().numpy()
            next_token_logprobs = torch.log(next_token_probs).detach().cpu().numpy()
            self._post_handle(
                run_reqs, next_token_ids, next_token_logprobs, is_chuncked_mode=False, do_filter_finished_reqs=False
            )
        logits = None

    def overlap_decode(self, decode_reqs: List[InferReq], max_decode_num: int, uninit_reqs, ok_finished_reqs):
        from .pre_process import padded_overlap_prepare_decode_inputs

        (
            micro_batch,
            run_reqs,
            padded_req_num,
            micro_batch1,
            run_reqs1,
            padded_req_num1,
        ) = padded_overlap_prepare_decode_inputs(decode_reqs, max_decode_num, is_multimodal=False)
        logits, logits1 = self.model.microbatch_overlap_decode(micro_batch, micro_batch1)
        self._overlap_req_init_and_filter(uninit_reqs=uninit_reqs, ok_finished_reqs=ok_finished_reqs, clear_list=True)
        req_num, req_num1 = len(run_reqs), len(run_reqs1)
        all_logits = torch.empty((req_num + req_num1, logits.shape[1]), dtype=logits.dtype, device=logits.device)

        all_logits[0:req_num, :].copy_(logits[0:req_num, :], non_blocking=True)
        all_logits[req_num : (req_num + req_num1), :].copy_(logits1[0:req_num1, :], non_blocking=True)

        all_run_reqs = run_reqs + run_reqs1
        if all_run_reqs:
            next_token_ids, next_token_probs = sample(all_logits, all_run_reqs, self.eos_id)
            next_token_ids = next_token_ids.detach().cpu().numpy()
            next_token_logprobs = torch.log(next_token_probs).detach().cpu().numpy()
            self._post_handle(
                all_run_reqs, next_token_ids, next_token_logprobs, is_chuncked_mode=False, do_filter_finished_reqs=False
            )
        return

    def overlap_prefill_reqs(self, prefill_reqs: List[InferReq], max_prefill_num: int, uninit_reqs, ok_finished_reqs):
        from .pre_process import padded_overlap_prepare_prefill_inputs

        (
            micro_batch,
            run_reqs,
            padded_req_num,
            micro_batch1,
            run_reqs1,
            padded_req_num1,
        ) = padded_overlap_prepare_prefill_inputs(prefill_reqs, max_prefill_num, is_multimodal=False)
        logits, logits1 = self.model.microbatch_overlap_prefill(micro_batch, micro_batch1)
        self._overlap_req_init_and_filter(uninit_reqs=uninit_reqs, ok_finished_reqs=ok_finished_reqs, clear_list=True)
        req_num, req_num1 = len(run_reqs), len(run_reqs1)
        all_logits = torch.empty((req_num + req_num1, logits.shape[1]), dtype=logits.dtype, device=logits.device)

        all_logits[0:req_num, :].copy_(logits[0:req_num, :], non_blocking=True)
        all_logits[req_num : (req_num + req_num1), :].copy_(logits1[0:req_num1, :], non_blocking=True)

        all_run_reqs = run_reqs + run_reqs1
        if all_run_reqs:
            next_token_ids, next_token_probs = sample(all_logits, all_run_reqs, self.eos_id)
            next_token_ids = next_token_ids.detach().cpu().numpy()
            next_token_logprobs = torch.log(next_token_probs).detach().cpu().numpy()
            self._post_handle(
                all_run_reqs, next_token_ids, next_token_logprobs, is_chuncked_mode=True, do_filter_finished_reqs=False
            )
        return
