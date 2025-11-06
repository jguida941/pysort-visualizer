#!/usr/bin/env python3
"""
Offline metrics verification helper.

Runs every registered algorithm against one or more generated datasets and
reports step counts (comparisons, swaps, confirm steps), inversion counts, and
duplicates so we can spot mismatches between theoretical expectations and what
the generators emit.

Example:
    python scripts/verify_metrics.py --preset reverse_run --seed 34554345 34554346
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from pathlib import Path
from typing import Iterable

from app.algos.registry import REGISTRY, load_all_algorithms
from app.core.step import Step
from app.presets import DEFAULT_PRESET_KEY, generate_dataset, get_presets


# Mirror the benchmark header so CSV output aligns with the UI export.
BENCHMARK_COLUMNS = [
    "algo",
    "context",
    "run",
    "preset",
    "seed",
    "n",
    "steps",
    "comparisons",
    "swaps",
    "duration_cpu_ms",
    "duration_visual_ms",
    "duration_wall_ms",
    "sorted",
    "error",
]


def count_inversions(data: list[int]) -> int:
    """Return the inversion count using a mergesort accumulator."""

    def merge_sort(arr: list[int]) -> tuple[list[int], int]:
        if len(arr) <= 1:
            return arr[:], 0
        mid = len(arr) // 2
        left, inv_left = merge_sort(arr[:mid])
        right, inv_right = merge_sort(arr[mid:])
        merged: list[int] = []
        i = j = 0
        inversions = inv_left + inv_right
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                inversions += len(left) - i
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inversions

    return merge_sort(list(data))[1]


def measure_algorithm(steps: Iterable[Step]) -> dict[str, int]:
    """Count comparisons, swaps, write operations, etc., from a step sequence."""
    comparisons = swaps = confirms = writes = non_adjacent_swaps = 0
    op_counts: Counter[str] = Counter()
    total = 0
    for step in steps:
        total += 1
        op_counts[step.op] += 1
        if step.op in {"compare", "merge_compare"}:
            comparisons += 1
        elif step.op == "swap":
            swaps += 1
            if len(step.indices) >= 2:
                i, j = step.indices[:2]
                if abs(i - j) != 1:
                    non_adjacent_swaps += 1
        elif step.op in {"set", "shift"}:
            writes += 1
        elif step.op == "confirm":
            confirms += 1
    return {
        "total": total,
        "comparisons": comparisons,
        "swaps": swaps,
        "non_adjacent_swaps": non_adjacent_swaps,
        "writes": writes,
        "confirms": confirms,
        "op_counts": op_counts,
    }


def run_verification(
    preset: str,
    seeds: list[int],
    n: int,
    min_val: int,
    max_val: int,
    algorithms: list[str] | None = None,
) -> list[dict[str, object]]:
    load_all_algorithms()
    algo_names = algorithms or sorted(REGISTRY.keys())
    results: list[dict[str, object]] = []

    for run_idx, seed in enumerate(seeds):
        rng = random.Random(seed)
        dataset = generate_dataset(preset, n, min_val, max_val, rng)
        expected = sorted(dataset)
        duplicates = n - len(set(dataset))
        inversions = count_inversions(dataset)

        for algo_name in algo_names:
            algo = REGISTRY.get(algo_name)
            if algo is None:
                raise ValueError(f"Unknown algorithm: {algo_name}")
            working = list(dataset)
            rows: list[Step] = []
            error: str | None = None
            try:
                for step in algo(working):
                    rows.append(step)
            except Exception as exc:  # pragma: no cover - defensive
                error = str(exc)
            metrics = measure_algorithm(rows)
            results.append(
                {
                    "algo": algo_name,
                    "context": "verify",
                    "run": run_idx,
                    "preset": preset,
                    "seed": seed,
                    "n": n,
                    "steps": metrics["total"],
                    "comparisons": metrics["comparisons"],
                    "swaps": metrics["swaps"],
                    "duration_cpu_ms": 0.0,  # Not measured here
                    "duration_visual_ms": 0.0,
                    "duration_wall_ms": 0.0,
                    "sorted": int(working == expected),
                    "error": error or "",
                    "duplicates": duplicates,
                    "inversions": inversions,
                    "confirms": metrics["confirms"],
                    "writes": metrics["writes"],
                    "non_adjacent_swaps": metrics["non_adjacent_swaps"],
                    "op_counts": dict(metrics["op_counts"]),
                }
            )
    return results


def format_table(rows: list[dict[str, object]]) -> str:
    headers = [
        "algo",
        "preset",
        "seed",
        "comparisons",
        "swaps",
        "non_adjacent_swaps",
        "confirms",
        "writes",
        "steps",
        "duplicates",
        "inversions",
        "sorted",
    ]
    col_widths = {hdr: max(len(hdr), *(len(str(row.get(hdr, ""))) for row in rows)) for hdr in headers}
    line = " | ".join(hdr.ljust(col_widths[hdr]) for hdr in headers)
    parts = [line, "-+-".join("-" * col_widths[hdr] for hdr in headers)]
    for row in rows:
        parts.append(
            " | ".join(str(row.get(hdr, "")).ljust(col_widths[hdr]) for hdr in headers)
        )
    return "\n".join(parts)


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    extended_columns = BENCHMARK_COLUMNS + [
        "duplicates",
        "inversions",
        "confirms",
        "writes",
        "non_adjacent_swaps",
        "op_counts",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=extended_columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify algorithm metrics across presets/seeds.")
    parser.add_argument(
        "--preset",
        nargs="+",
        default=[DEFAULT_PRESET_KEY],
        help="Preset key(s) to evaluate",
    )
    parser.add_argument("--seed", type=int, nargs="+", help="Seed(s) to evaluate")
    parser.add_argument("--runs", type=int, default=1, help="Number of sequential seeds to run")
    parser.add_argument("--start-seed", type=int, default=123456, help="Base seed when --seed omitted")
    parser.add_argument("--n", type=int, default=32, help="Dataset length")
    parser.add_argument("--min", dest="min_val", type=int, default=0, help="Preset lower bound")
    parser.add_argument("--max", dest="max_val", type=int, default=200, help="Preset upper bound")
    parser.add_argument("--algo", action="append", help="Algorithm name(s) to include")
    parser.add_argument("--csv", type=Path, help="Optional path to write CSV results")
    parser.add_argument("--list-presets", action="store_true", help="List available presets and exit")
    parser.add_argument("--list-algos", action="store_true", help="List algorithm names and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_presets:
        for preset in get_presets():
            print(f"{preset.key:15} {preset.label}")
        return
    if args.list_algos:
        load_all_algorithms()
        for name in sorted(REGISTRY.keys()):
            print(name)
        return

    presets = args.preset
    if args.seed:
        seeds = args.seed
    else:
        seeds = [args.start_seed + i for i in range(args.runs)]

    all_rows: list[dict[str, object]] = []
    for preset in presets:
        rows = run_verification(
            preset=preset,
            seeds=seeds,
            n=args.n,
            min_val=args.min_val,
            max_val=args.max_val,
            algorithms=args.algo,
        )
        all_rows.extend(rows)
        print(f"Preset={preset} seeds={seeds}")
        print(format_table(rows))
        print()

    if args.csv:
        write_csv(all_rows, args.csv)
        print(f"Wrote {len(all_rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
