"""Compare official trec_eval output with Brainwave's saved derived metrics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

METRIC_MAP = {
    "Rprec": "r_precision",
    "P_5": "precision@5",
    "P_10": "precision@10",
    "P_100": "precision@100",
    "recall_5": "recall@5",
    "recall_10": "recall@10",
    "recall_100": "recall@100",
    "ndcg_cut_10": "ndcg_graded@10",
    "map_cut_100": "ap@100",
    "recip_rank": "mrr@10",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trec-dir", type=Path, required=True)
    parser.add_argument("--metrics-summary", type=Path, required=True)
    parser.add_argument("--evaluator-commit", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    expected = {}
    with args.metrics_summary.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            expected[row["retriever"], row["preset"], row["metric"]] = float(row["mean"])

    comparisons = []
    sources = []
    tolerance = 0.0000500001
    for path in sorted(args.trec_dir.glob("*/*.trec_eval.txt")):
        retriever = path.parent.name
        preset = "conservative" if "conservative" in path.name else "raw"
        run_path = path.with_name(path.name.removesuffix(".trec_eval.txt") + ".trec")
        sources.append(
            {
                "retriever": retriever,
                "preset": preset,
                "run_file": str(run_path),
                "run_sha256": sha256(run_path),
                "trec_eval_output": str(path),
                "trec_eval_output_sha256": sha256(path),
            }
        )
        for line in path.read_text(encoding="utf-8").splitlines():
            name, scope, value = line.split()
            if scope != "all" or name not in METRIC_MAP:
                continue
            metric = METRIC_MAP[name]
            reference = expected[retriever, preset, metric]
            observed = float(value)
            difference = observed - reference
            comparisons.append(
                {
                    "retriever": retriever,
                    "preset": preset,
                    "metric": metric,
                    "brainwave": reference,
                    "trec_eval": observed,
                    "difference": difference,
                    "matches_four_decimal_output": abs(difference) <= tolerance,
                }
            )

    if len(comparisons) != 40:
        raise ValueError(f"expected 40 metric comparisons, found {len(comparisons)}")
    failures = [row for row in comparisons if not row["matches_four_decimal_output"]]
    if failures:
        raise ValueError(f"trec_eval mismatches: {failures}")

    result = {
        "status": "passed",
        "comparison_count": len(comparisons),
        "tolerance": tolerance,
        "tolerance_reason": "trec_eval summary output is rounded to four decimals",
        "evaluator": {
            "name": "NIST trec_eval",
            "version": "10.0-rc3",
            "source_commit": args.evaluator_commit,
        },
        "qrels": {
            "path": str(args.trec_dir / "qrels.tsv"),
            "sha256": sha256(args.trec_dir / "qrels.tsv"),
        },
        "sources": sources,
        "comparisons": comparisons,
        "notes": [
            "recip_rank was evaluated on separately truncated rank-10 files to match MRR@10.",
            "The -c option included every query in the supplied qrels.",
            "The exported rank-based scores preserve the evaluated ordering.",
        ],
    }
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Step 12 — Independent TREC verification",
        "",
        "**Status: PASSED.** The official NIST `trec_eval` program independently checked "
        "40 aggregate values across the full BM25 and dense raw/conservative rankings. "
        "Every value agrees with the saved Brainwave metrics within 0.00005, the tolerance "
        "required by `trec_eval`'s four-decimal summary output.",
        "",
        f"Evaluator: NIST `trec_eval` 10.0-rc3, source commit `{args.evaluator_commit}`.",
        "",
        "| Retriever | Condition | Metric | Brainwave | trec_eval | Difference |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in comparisons:
        lines.append(
            f"| {row['retriever']} | {row['preset']} | {row['metric']} | "
            f"{row['brainwave']:.6f} | {row['trec_eval']:.4f} | {row['difference']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "`recip_rank` was run on separate rank-10 files so it checks MRR@10 rather than "
            "reciprocal rank over the full depth-100 ranking. All queries were included with "
            "`trec_eval -c`, using the exact saved qrels.",
        ]
    )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "comparisons": len(comparisons)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
