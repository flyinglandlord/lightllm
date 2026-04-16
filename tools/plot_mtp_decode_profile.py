#!/usr/bin/env python3
"""
Extract MTP decode profile logs and summarize latency by batch size.

Example:
    python tools/plot_mtp_decode_profile.py /path/to/process.*.log \
        --csv mtp_decode_profile.csv \
        --plot mtp_decode_profile.png
"""
import argparse
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List


PROFILE_MARKER = "MTP_DECODE_PROFILE"
FIELD_RE = re.compile(r"(\w+)=([^\s]+)")

INT_FIELDS = {"batch_size", "run_reqs", "model_batch_size", "verify_ok_reqs"}
FLOAT_FIELDS = {
    "pre_process_ms",
    "inference_ms",
    "main_forward_ms",
    "post_stage2_ms",
    "post_stage3_ms",
    "post_process_ms",
    "total_ms",
}
TIME_FIELDS = [
    "pre_process_ms",
    "inference_ms",
    "main_forward_ms",
    "post_stage2_ms",
    "post_stage3_ms",
    "post_process_ms",
    "total_ms",
]


def parse_profile_line(line: str) -> Dict[str, float]:
    if PROFILE_MARKER not in line:
        return {}

    fields: Dict[str, float] = {}
    for key, value in FIELD_RE.findall(line):
        if key in INT_FIELDS:
            fields[key] = int(value)
        elif key in FLOAT_FIELDS:
            fields[key] = float(value)

    if "batch_size" not in fields:
        return {}
    if "post_process_ms" not in fields and "post_stage2_ms" in fields and "post_stage3_ms" in fields:
        fields["post_process_ms"] = fields["post_stage2_ms"] + fields["post_stage3_ms"]
    return fields


def read_profiles(log_paths: Iterable[Path]) -> List[Dict[str, float]]:
    rows = []
    for log_path in log_paths:
        with log_path.open("r", encoding="utf-8", errors="replace") as fp:
            for line_no, line in enumerate(fp, 1):
                row = parse_profile_line(line)
                if row:
                    row["source"] = str(log_path)
                    row["line_no"] = line_no
                    rows.append(row)
    return rows


def mean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def summarize_by_batch(rows: List[Dict[str, float]]) -> List[Dict[str, float]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[int(row["batch_size"])].append(row)

    summary = []
    for batch_size in sorted(grouped):
        batch_rows = grouped[batch_size]
        item: Dict[str, float] = {"batch_size": batch_size, "count": len(batch_rows)}
        for field in TIME_FIELDS:
            values = [row[field] for row in batch_rows if field in row]
            item[f"{field}_avg"] = mean(values)
            item[f"{field}_std"] = stdev(values)
            item[f"{field}_min"] = min(values) if values else 0.0
            item[f"{field}_max"] = max(values) if values else 0.0
        summary.append(item)
    return summary


def write_csv(path: Path, rows: List[Dict[str, float]]) -> None:
    if not rows:
        return
    fieldnames = [
        "source",
        "line_no",
        "batch_size",
        "run_reqs",
        "model_batch_size",
        "verify_ok_reqs",
        *TIME_FIELDS,
    ]
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(path: Path, summary: List[Dict[str, float]]) -> None:
    if not summary:
        return
    fieldnames = list(summary[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)


def print_markdown_summary(summary: List[Dict[str, float]]) -> None:
    if not summary:
        print("No MTP_DECODE_PROFILE records found.")
        return

    headers = [
        "batch_size",
        "count",
        "pre_avg_ms",
        "inference_avg_ms",
        "main_forward_avg_ms",
        "post_stage2_avg_ms",
        "post_stage3_avg_ms",
        "post_total_avg_ms",
        "total_avg_ms",
    ]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for item in summary:
        print(
            "| "
            + " | ".join(
                [
                    str(int(item["batch_size"])),
                    str(int(item["count"])),
                    f"{item['pre_process_ms_avg']:.3f}",
                    f"{item['inference_ms_avg']:.3f}",
                    f"{item['main_forward_ms_avg']:.3f}",
                    f"{item['post_stage2_ms_avg']:.3f}",
                    f"{item['post_stage3_ms_avg']:.3f}",
                    f"{item['post_process_ms_avg']:.3f}",
                    f"{item['total_ms_avg']:.3f}",
                ]
            )
            + " |"
        )


def plot_summary(path: Path, summary: List[Dict[str, float]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for --plot. Install it or omit --plot.") from exc

    batch_sizes = [int(item["batch_size"]) for item in summary]
    series = [
        ("pre process", "pre_process_ms_avg"),
        ("inference", "inference_ms_avg"),
        ("main forward", "main_forward_ms_avg"),
        ("post stage2", "post_stage2_ms_avg"),
        ("post stage3", "post_stage3_ms_avg"),
        ("post total", "post_process_ms_avg"),
        ("total", "total_ms_avg"),
    ]

    plt.figure(figsize=(10, 6))
    for label, field in series:
        plt.plot(batch_sizes, [item[field] for item in summary], marker="o", label=label)
    plt.xlabel("Batch size")
    plt.ylabel("Average latency (ms)")
    plt.title("MTP decode latency by batch size")
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path, help="Log files that contain MTP_DECODE_PROFILE lines.")
    parser.add_argument("--csv", type=Path, help="Write raw extracted records to this CSV path.")
    parser.add_argument("--summary-csv", type=Path, help="Write aggregated summary to this CSV path.")
    parser.add_argument("--plot", type=Path, help="Write a latency-vs-batch-size plot to this image path.")
    args = parser.parse_args()

    rows = read_profiles(args.logs)
    summary = summarize_by_batch(rows)
    print_markdown_summary(summary)

    if args.csv:
        write_csv(args.csv, rows)
    if args.summary_csv:
        write_summary_csv(args.summary_csv, summary)
    if args.plot:
        plot_summary(args.plot, summary)


if __name__ == "__main__":
    main()
