"""Select reproducible wins, losses, and ties from normalization reports."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sqlite3
from pathlib import Path

FIELDS = [
    "run_id",
    "comparison",
    "qid",
    "query_original",
    "query_normalized",
    "category",
    "baseline_ndcg10",
    "candidate_ndcg10",
    "delta_ndcg10",
    "relevant_passage_id",
    "baseline_rank",
    "candidate_rank",
    "competing_passage_id",
    "mechanism",
    "evidence",
    "annotation_timing",
    "reviewer",
    "notes",
]


def clean(value: str, limit: int = 420) -> str:
    return " ".join(value.split())[:limit]


def load_qrels(path: Path) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            qid, _iteration, pid, grade = line.rstrip("\n").split("\t")
            result.setdefault(qid, {})[pid] = int(grade)
    return result


def ranks(row: dict) -> dict[str, int]:
    return {item["passage_id"]: rank for rank, item in enumerate(row["ranking"], start=1)}


def shown_rank(value: int | None) -> str:
    return str(value) if value is not None else ">100"


def choose_relevant(
    grades: dict[str, int],
    raw_ranks: dict[str, int],
    candidate_ranks: dict[str, int],
    category: str,
) -> str:
    positives = [pid for pid, grade in grades.items() if grade > 0]
    if category == "win":
        return max(
            positives,
            key=lambda pid: (
                raw_ranks.get(pid, 101) - candidate_ranks.get(pid, 101),
                grades[pid],
                -candidate_ranks.get(pid, 101),
            ),
        )
    if category == "loss":
        return max(
            positives,
            key=lambda pid: (
                candidate_ranks.get(pid, 101) - raw_ranks.get(pid, 101),
                grades[pid],
                -raw_ranks.get(pid, 101),
            ),
        )
    return max(
        positives,
        key=lambda pid: (
            -min(raw_ranks.get(pid, 101), candidate_ranks.get(pid, 101)),
            grades[pid],
        ),
    )


def passage(conn: sqlite3.Connection, pid: str | None) -> tuple[str, str]:
    if not pid:
        return "", ""
    row = conn.execute("SELECT title, text FROM corpus WHERE passage_id=?", (pid,)).fetchone()
    return (row[0], row[1]) if row else ("", "")


def selected_rows(
    report: dict, qrels: dict[str, dict[str, int]], seed: int
) -> list[tuple[str, dict, dict]]:
    raw = next(row for row in report["conditions"] if row["preset"] == "raw")
    candidate = next(row for row in report["conditions"] if row["preset"] == "conservative")
    raw_by_qid = {row["qid"]: row for row in raw["per_query"]}
    candidates = []
    for row in candidate["per_query"]:
        base = raw_by_qid[row["qid"]]
        delta = row["metrics"]["ndcg@10"] - base["metrics"]["ndcg@10"]
        candidates.append((delta, row["qid"], base, row))
    wins = sorted((r for r in candidates if r[0] > 1e-12), reverse=True)[:5]
    losses = sorted(r for r in candidates if r[0] < -1e-12)[:5]
    ties = sorted((r for r in candidates if abs(r[0]) <= 1e-12), key=lambda r: r[1])
    sampled_ties = random.Random(seed).sample(ties, min(10, len(ties)))
    return [
        *(("win", base, row) for _delta, _qid, base, row in wins),
        *(("loss", base, row) for _delta, _qid, base, row in losses),
        *(("tie", base, row) for _delta, _qid, base, row in sampled_ties),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", nargs="+", type=Path, required=True)
    parser.add_argument("--normalization-root", type=Path, required=True)
    parser.add_argument("--output-tsv", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    dataset_ids = {report["dataset_id"] for report in reports}
    if len(dataset_ids) != 1:
        raise ValueError("reports must use one identical dataset")
    dataset_id = next(iter(dataset_ids))
    dataset_dir = args.normalization_root / "datasets" / dataset_id
    qrels = load_qrels(dataset_dir / "qrels.tsv")
    conn = sqlite3.connect(dataset_dir / "corpus.sqlite")
    output_rows = []
    sections = []

    try:
        for report in reports:
            candidate = next(row for row in report["conditions"] if row["preset"] == "conservative")
            retriever = candidate["retriever"]
            comparison = candidate["comparison_to_raw"]["ndcg@10"]
            cases = selected_rows(report, qrels, args.seed)
            sections.extend(
                [
                    f"## {retriever.upper()}: conservative versus raw",
                    "",
                    f"Mean nDCG@10 delta: {comparison['delta']:.6f}; paired 95% interval "
                    f"[{comparison['ci_low']:.6f}, {comparison['ci_high']:.6f}]; "
                    "wins/losses/ties: "
                    f"{comparison['wins']}/{comparison['losses']}/{comparison['ties']}.",
                    "",
                    "| Category | Query ID | Query | Delta | Relevant rank raw → conservative |",
                    "|---|---|---|---:|---:|",
                ]
            )
            for category, base, row in cases:
                raw_ranks, candidate_ranks = ranks(base), ranks(row)
                relevant_pid = choose_relevant(
                    qrels[row["qid"]], raw_ranks, candidate_ranks, category
                )
                worse_ranking = base["ranking"] if category == "win" else row["ranking"]
                competing_pid = next(
                    (
                        item["passage_id"]
                        for item in worse_ranking
                        if item["passage_id"] != relevant_pid
                    ),
                    None,
                )
                relevant_title, relevant_text = passage(conn, relevant_pid)
                competing_title, competing_text = passage(conn, competing_pid)
                baseline_score = base["metrics"]["ndcg@10"]
                candidate_score = row["metrics"]["ndcg@10"]
                delta = candidate_score - baseline_score
                if category == "win":
                    mechanism = (
                        "Relevant-passage ranking improved after conservative normalization."
                    )
                elif category == "loss":
                    mechanism = (
                        "Relevant-passage ranking worsened after conservative normalization."
                    )
                elif row["query_changed"]:
                    mechanism = "The query changed, but graded nDCG@10 remained tied."
                else:
                    mechanism = (
                        "The query was unchanged; document normalization left graded nDCG@10 tied."
                    )
                evidence = (
                    f"Relevant [{relevant_pid}] {clean(relevant_title, 100)}: "
                    f"{clean(relevant_text)} | Competing [{competing_pid}] "
                    f"{clean(competing_title, 100)}: {clean(competing_text)}"
                )
                output_rows.append(
                    {
                        "run_id": report["run_id"],
                        "comparison": f"{retriever} conservative-vs-raw",
                        "qid": row["qid"],
                        "query_original": row["query"],
                        "query_normalized": row["normalized_query"],
                        "category": category,
                        "baseline_ndcg10": f"{baseline_score:.12f}",
                        "candidate_ndcg10": f"{candidate_score:.12f}",
                        "delta_ndcg10": f"{delta:.12f}",
                        "relevant_passage_id": relevant_pid,
                        "baseline_rank": shown_rank(raw_ranks.get(relevant_pid)),
                        "candidate_rank": shown_rank(candidate_ranks.get(relevant_pid)),
                        "competing_passage_id": competing_pid,
                        "mechanism": mechanism,
                        "evidence": evidence,
                        "annotation_timing": "Post-outcome exploratory analysis",
                        "reviewer": "Codex-assisted factual trace review",
                        "notes": (
                            f"query_changed={row['query_changed']}; relevance_grade="
                            f"{qrels[row['qid']][relevant_pid]}; causal interpretation requires "
                            "manual review"
                        ),
                    }
                )
                sections.append(
                    f"| {category} | {row['qid']} | {clean(row['query'], 80)} | "
                    f"{delta:.6f} | {shown_rank(raw_ranks.get(relevant_pid))} → "
                    f"{shown_rank(candidate_ranks.get(relevant_pid))} |"
                )
            sections.append("")
    finally:
        conn.close()

    args.output_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_tsv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(output_rows)

    markdown = [
        "# Step 11 — Paired effects and failure cases",
        "",
        "This exploratory trace review uses the complete 2,896-query MIRACL Arabic dev set. "
        "For each retriever it selects the five largest graded nDCG@10 wins, five largest "
        "losses, and ten ties sampled deterministically with seed 42.",
        "",
        "The rank movements are factual associations, not proof that normalization caused a "
        "particular linguistic mechanism. Unjudged passages receive zero benchmark credit but "
        "are not human-confirmed negatives.",
        "",
        *sections,
    ]
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"rows": len(output_rows), "tsv": str(args.output_tsv), "markdown": str(args.output_md)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
