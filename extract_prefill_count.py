#!/usr/bin/env python3
"""
从日志文件中提取 prefill 执行次数的最大值。

用法:
    python extract_prefill_count.py <log_file>

如果未指定 log_file，则默认从 stdin 读取。

日志格式示例:
    [Prefill Stats] prefill 执行次数：1
    [Prefill Stats] prefill 执行次数：2
    ...
"""

import re
import sys


def extract_prefill_count(log_content: str) -> int:
    """
    从日志内容中提取 prefill 执行次数的最大值。

    Args:
        log_content: 日志文件内容

    Returns:
        prefill 执行次数的最大值，如果未找到则返回 0
    """
    pattern = r"\[Prefill Stats\] prefill 执行次数：(\d+)"
    matches = re.findall(pattern, log_content)

    if not matches:
        return 0

    return max(int(m) for m in matches)


def extract_all_prefill_counts(log_content: str) -> list:
    """
    从日志内容中提取所有 prefill 执行次数。

    Args:
        log_content: 日志文件内容

    Returns:
        包含所有 prefill 执行次数的列表
    """
    pattern = r"\[Prefill Stats\] prefill 执行次数：(\d+)"
    matches = re.findall(pattern, log_content)

    return [int(m) for m in matches]


def main():
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
    else:
        log_content = sys.stdin.read()

    max_count = extract_prefill_count(log_content)
    all_counts = extract_all_prefill_counts(log_content)

    print(f"Prefill 执行次数最大值：{max_count}")
    print(f"Prefill 日志总条数：{len(all_counts)}")

    # 如果需要详细的执行序列，可以取消下面的注释
    # if all_counts:
    #     print(f"Prefill 执行序列：{all_counts}")


if __name__ == "__main__":
    main()
