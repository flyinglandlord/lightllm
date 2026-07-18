# LightLLM Pre3 交付项目

本项目基于 LightLLM，集成了 `pre3` 与 `xgrammar` 两种结构化解码后端，并提供固定 benchmark 脚本用于比较 JSON EBNF 文法约束下的 `mean per token latency`。

## 环境准备

如果需要从头安装依赖：

```bash
pip install vllm==0.8.5 --no-deps
pip install -r requirements.txt
```

安装 LightLLM constraint decode kernel：

```bash
cd kernel
LIGHTLLM_INSTALL_ONLY_CONSTRAINT_DECODE_KERNEL=1 pip install -e .
cd ..
```

运行前请确认模型目录可访问，例如：

```bash
ls /mtc/chenjunyi1/models/deepseek-v2-lite
```

## Benchmark

使用脚本：

```bash
scripts/benchmark_jsonschemabench.py
```

脚本提供模型路径和并发规模两个配置选项：

- `--batch_size`: 每轮积攒并同时运行的请求数。
- `--model_dir`: LightLLM 模型路径。

运行命令示例：

```bash
/data/nvme0/chenjunyi/miniconda3/envs/pre3/bin/python scripts/benchmark_jsonschemabench.py \
  --batch_size 128 \
  --model_dir /mtc/chenjunyi1/models/deepseek-v2-lite
```

脚本会自动完成以下流程：

1. 使用固定 JSONSchemaBench prompt。
2. 将同一个请求重复 `batch_size` 次，避免不同请求长度导致 batch 不齐。
3. 使用 `test/format_out/test_xgrammar_constraint.py` 中的 EBNF JSON 文法作为 `guided_grammar` 约束。
4. 设置 `LIGHTLLM_RUN_BATCH=batch_size`，等待攒够请求后再调度。
5. 依次启动并测试 `xgrammar` 和 `pre3`。
6. 从服务端日志中解析 `mean_per_token_cost_time`。
7. 输出两种后端的平均 `mean per token latency`、pre3 相比 xgrammar 的降低百分比，以及两次运行的日志保存路径。

为加快启动速度，脚本中已固定关闭：

- `--disable_cudagraph`
- `DISABLE_CHECK_MAX_LEN_INFER=1`

## 输出示例

一次 batch size 128 的输出示例：

```text
Benchmark result
xgrammar mean per token latency: 45.4062 ms/token
pre3 mean per token latency: 20.2777 ms/token
pre3 latency reduction vs xgrammar: 55.34%
xgrammar log dir: experiment_results/jsonschemabench_ebnf_batch128_20260719_015022/xgrammar/lightllm_logs
xgrammar stdout log: experiment_results/jsonschemabench_ebnf_batch128_20260719_015022/xgrammar/server_stdout.log
pre3 log dir: experiment_results/jsonschemabench_ebnf_batch128_20260719_015022/pre3/lightllm_logs
pre3 stdout log: experiment_results/jsonschemabench_ebnf_batch128_20260719_015022/pre3/server_stdout.log
summary: experiment_results/jsonschemabench_ebnf_batch128_20260719_015022/summary.json
```

其中：

- `xgrammar mean per token latency`: xgrammar 后端的平均单 token 延迟。
- `pre3 mean per token latency`: pre3 后端的平均单 token 延迟。
- `pre3 latency reduction vs xgrammar`: pre3 相比 xgrammar 的延迟降低比例，计算方式为 `(xgrammar - pre3) / xgrammar * 100%`。
- `summary`: 本次测试的完整结构化结果文件。

## 结果文件

每次运行会生成独立目录：

```text
experiment_results/jsonschemabench_ebnf_batch{batch_size}_{timestamp}/
```

目录结构示例：

```text
experiment_results/jsonschemabench_ebnf_batch128_20260719_015022/
  summary.json
  xgrammar/
    server_stdout.log
    lightllm_logs/
  pre3/
    server_stdout.log
    lightllm_logs/
```

如需查看原始统计来源，可在对应 `server_stdout.log` 中搜索：

```bash
grep "mean_per_token_cost_time" experiment_results/jsonschemabench_ebnf_batch128_*/xgrammar/server_stdout.log
grep "mean_per_token_cost_time" experiment_results/jsonschemabench_ebnf_batch128_*/pre3/server_stdout.log
```

## 注意事项

- 脚本会自动选择空闲 GPU，默认使用 `tp=2`。
- 测试完成后脚本会停止对应 LightLLM 服务进程。
- `batch_size=128` 是当前推荐测试配置；更大的 batch 可能导致部分请求等待时间明显变长。
