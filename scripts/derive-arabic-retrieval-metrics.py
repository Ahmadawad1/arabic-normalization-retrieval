"""Derive standard depth-100 IR metrics from immutable normalization run reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from arabic_normalization_retrieval.metrics import (
    average_precision,
    graded_ndcg_at_k,
    hit_rate,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)

CUTOFFS = (1, 3, 5, 10, 20, 50, 100)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_qrels(path: Path) -> dict[str, dict[str, int]]:
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            qid, _iteration, passage_id, grade = line.rstrip("\n").split("\t")
            qrels[qid][passage_id] = int(grade)
    return dict(qrels)


def query_metrics(ranked: list[str], grades: dict[str, int]) -> dict[str, float]:
    relevant = {pid for pid, grade in grades.items() if grade > 0}
    result: dict[str, float] = {}
    for k in CUTOFFS:
        precision = precision_at_k(ranked, relevant, k)
        recall = recall_at_k(ranked, relevant, k)
        result[f"precision@{k}"] = precision
        result[f"recall@{k}"] = recall
        result[f"f1@{k}"] = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
        result[f"hit_rate@{k}"] = hit_rate(ranked, relevant, k)
        result[f"mrr@{k}"] = mrr(ranked, relevant, k)
        result[f"ndcg_binary@{k}"] = ndcg_at_k(ranked, relevant, k)
        result[f"ndcg_graded@{k}"] = graded_ndcg_at_k(ranked, grades, k)
        result[f"ap@{k}"] = average_precision(ranked, relevant, k)

    r = len(relevant)
    if not r:
        result["r_precision"] = 0.0
    elif r > len(ranked):
        result["r_precision"] = sum(pid in relevant for pid in ranked) / r
    else:
        result["r_precision"] = precision_at_k(ranked, relevant, r)
    return result


def paired_summaries(
    candidate: dict[str, list[float]],
    baseline: dict[str, list[float]],
    metric_names: list[str],
    bootstrap_samples: int,
    seed: int,
) -> dict[str, dict[str, float | int]]:
    differences = np.column_stack(
        [
            np.asarray(candidate[name], dtype=np.float64)
            - np.asarray(baseline[name], dtype=np.float64)
            for name in metric_names
        ]
    )
    rng = random.Random(seed)
    means = np.empty((bootstrap_samples, len(metric_names)), dtype=np.float64)
    batch_size = 64
    for start in range(0, bootstrap_samples, batch_size):
        size = min(batch_size, bootstrap_samples - start)
        indices = np.fromiter(
            (rng.randrange(len(differences)) for _ in range(size * len(differences))),
            dtype=np.int32,
            count=size * len(differences),
        ).reshape(size, len(differences))
        means[start : start + size] = differences[indices].mean(axis=1)
    lows = np.quantile(means, 0.025, axis=0)
    highs = np.quantile(means, 0.975, axis=0)
    return {
        name: {
            "delta": float(differences[:, i].mean()),
            "ci_low": float(lows[i]),
            "ci_high": float(highs[i]),
            "wins": int(np.sum(differences[:, i] > 1e-12)),
            "losses": int(np.sum(differences[:, i] < -1e-12)),
            "ties": int(np.sum(np.abs(differences[:, i]) <= 1e-12)),
        }
        for i, name in enumerate(metric_names)
    }


def fmt(value: float) -> str:
    return f"{value:.6f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", nargs="+", type=Path, required=True)
    parser.add_argument("--normalization-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    dataset_ids = {report["dataset_id"] for report in reports}
    if len(dataset_ids) != 1:
        raise ValueError("all reports must use the same dataset ID")
    dataset_id = next(iter(dataset_ids))
    manifests = [report["dataset"] for report in reports]
    hashes = {json.dumps(manifest["hashes"], sort_keys=True) for manifest in manifests}
    if len(hashes) != 1:
        raise ValueError("all reports must use identical dataset hashes")

    dataset_dir = args.normalization_root / "datasets" / dataset_id
    qrels = load_qrels(dataset_dir / "qrels.tsv")
    output = args.output
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    vectors: dict[tuple[str, str], dict[str, list[float]]] = {}
    source_runs = []
    for path, report in zip(args.reports, reports, strict=True):
        source_runs.append(
            {
                "run_id": report["run_id"],
                "retrievers": report["config"]["retrievers"],
                "path": str(path),
                "sha256": sha256(path),
            }
        )
        for condition in report["conditions"]:
            key = (condition["retriever"], condition["preset"])
            if key in vectors:
                raise ValueError(f"duplicate condition: {key}")
            vectors[key] = defaultdict(list)
            for query in condition["per_query"]:
                qid = query["qid"]
                ranked = [item["passage_id"] for item in query["ranking"]]
                metrics = query_metrics(ranked, qrels[qid])
                for name, value in metrics.items():
                    vectors[key][name].append(value)
                rows.append(
                    {
                        "retriever": key[0],
                        "preset": key[1],
                        "qid": qid,
                        "query": query["query"],
                        "normalized_query": query["normalized_query"],
                        "query_changed": query["query_changed"],
                        **metrics,
                    }
                )

            checks = {
                "ndcg_graded@10": condition["metrics"]["ndcg@10"],
                "recall@5": condition["metrics"]["recall@5"],
                "recall@10": condition["metrics"]["recall@10"],
                "recall@100": condition["metrics"]["recall@100"],
                "mrr@10": condition["metrics"]["mrr@10"],
            }
            for metric, expected in checks.items():
                observed = float(np.mean(vectors[key][metric]))
                if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-12):
                    raise ValueError(
                        f"validation failed for {key} {metric}: {observed} != {expected}"
                    )

    metric_names = list(next(iter(vectors.values())).keys())
    summaries = []
    for (retriever, preset), metric_vectors in sorted(vectors.items()):
        baseline = vectors[(retriever, "raw")]
        if preset == "raw":
            comparisons = {
                metric: {
                    "delta": 0.0,
                    "ci_low": 0.0,
                    "ci_high": 0.0,
                    "wins": 0,
                    "losses": 0,
                    "ties": len(metric_vectors[metric]),
                }
                for metric in metric_names
            }
        else:
            comparisons = paired_summaries(
                metric_vectors,
                baseline,
                metric_names,
                args.bootstrap_samples,
                args.seed,
            )
        for metric in metric_names:
            candidate_values = np.asarray(metric_vectors[metric], dtype=np.float64)
            summaries.append(
                {
                    "retriever": retriever,
                    "preset": preset,
                    "metric": metric,
                    "mean": float(candidate_values.mean()),
                    **comparisons[metric],
                }
            )

    summary_fields = [
        "retriever",
        "preset",
        "metric",
        "mean",
        "delta",
        "ci_low",
        "ci_high",
        "wins",
        "losses",
        "ties",
    ]
    with (output / "metrics-summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(summaries)

    per_query_fields = [
        "retriever",
        "preset",
        "qid",
        "query",
        "normalized_query",
        "query_changed",
        *metric_names,
    ]
    with (output / "per-query-metrics.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=per_query_fields)
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "schema_version": 1,
        "description": "Derived depth-100 metrics; original run artifacts remain unchanged.",
        "dataset": manifests[0],
        "source_runs": source_runs,
        "cutoffs": list(CUTOFFS),
        "bootstrap": {
            "samples": args.bootstrap_samples,
            "seed": args.seed,
            "unit": "query",
            "paired": True,
            "method": "percentile",
            "confidence": 0.95,
        },
        "relevance_policy": (
            "qrel grade > 0 is relevant; graded nDCG uses 2^grade-1; "
            "unjudged passages receive zero credit and are not proven irrelevant"
        ),
        "depth_limit": 100,
        "metrics": summaries,
        "warnings": [
            "Precision is conservative because MIRACL qrels are incomplete.",
            "Metrics above rank 100 cannot be derived from these saved rankings.",
            "This is the public MIRACL Arabic dev set, not a private blind test.",
        ],
    }
    (output / "final-metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    by_key = {(r["retriever"], r["preset"], r["metric"]): r for r in summaries}
    selected = (
        "ndcg_graded@10",
        "precision@10",
        "recall@10",
        "mrr@10",
        "ap@100",
        "recall@100",
        "hit_rate@10",
        "r_precision",
    )
    markdown = [
        "# Full MIRACL Arabic retrieval metrics",
        "",
        "These metrics were derived from the immutable top-100 rankings of the completed "
        "2,896-query BM25 and dense runs. No normalization, indexing, embedding, or retrieval "
        "was repeated.",
        "",
        "## Key metrics",
        "",
        "| Retriever | Metric | Raw | Conservative | Delta | Paired 95% CI |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for retriever in ("bm25", "dense"):
        for metric in selected:
            raw = by_key[(retriever, "raw", metric)]
            candidate = by_key[(retriever, "conservative", metric)]
            markdown.append(
                f"| {retriever.upper()} | {metric} | {fmt(raw['mean'])} | "
                f"{fmt(candidate['mean'])} | {fmt(candidate['delta'])} | "
                f"[{fmt(candidate['ci_low'])}, {fmt(candidate['ci_high'])}] |"
            )

    markdown.extend(
        [
            "",
            "## Complete aggregate metric suite",
            "",
            "The machine-readable `metrics-summary.csv` and `final-metrics.json` include "
            "Precision, Recall, F1, Hit Rate, MRR, binary nDCG, graded nDCG, and AP at "
            "cutoffs 1, 3, 5, 10, 20, 50, and 100, plus R-Precision. Every conservative "
            "metric includes a paired 10,000-sample percentile interval and win/loss/tie counts.",
            "",
            "## Interpretation warning",
            "",
            "MIRACL relevance judgments are incomplete. This evaluation gives unjudged passages "
            "zero credit, but that does not establish that humans judged those passages "
            "irrelevant. Precision values are therefore conservative and should be interpreted "
            "alongside recall, "
            "graded nDCG, MRR, and AP.",
            "",
            "The data are the complete public MIRACL Arabic development set, not a private "
            "blind test.",
            "",
            "## Files",
            "",
            "- `final-metrics.json`: provenance, definitions, aggregate metrics, paired intervals",
            "- `metrics-summary.csv`: tidy aggregate table",
            "- `per-query-metrics.csv`: all derived metrics for each query and condition",
        ]
    )
    (output / "FINAL-REPORT.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "metrics": len(metric_names), "rows": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
