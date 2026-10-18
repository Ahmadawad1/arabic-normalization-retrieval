# Reproducibility record

## Evaluation scope

- Corpus: 2,061,414 MIRACL Arabic passages.
- Queries: all 2,896 queries from the public MIRACL Arabic development set.
- Retrieval depth: 100.
- Conditions: raw and conservative normalization on both queries and passages.
- Bootstrap: paired query resampling, 10,000 samples, seed 42.

## Pinned revisions

- MIRACL topics and qrels: `5be20db9509754dadad47689368639fcec739c00`.
- MIRACL corpus: `d921ec7e349ce0d28daf30b2da9da5ee698bef0d`.
- Dense model: `facebook/mcontriever-msmarco` at `9ff6abed2c2fdf32bbbd8b4e98fb10160e317375`.

## Hardware and software

- Windows 11 host with Docker and WSL2.
- Intel Core 9 270H, 14 cores and 20 logical processors.
- 32 GB RAM.
- NVIDIA GeForce RTX 5070 Laptop GPU with approximately 8 GB VRAM.
- Python 3.12.13 and SQLite 3.46.1 in Linux 6.6.87.2 under WSL2.
- Dense run: SentenceTransformers 6.1.0, Transformers 5.19.0, Torch 2.14.1, NumPy 2.5.4, device `cuda:0`.

## Final run identifiers

| Retriever | Run ID | Dataset ID | Elapsed time |
|---|---|---|---:|
| BM25 | `74f3916ede7f439193e543d6d4ab6f85` | `1ca281efcc8c411f97a527f6ee744e60` | 1,499 seconds |
| Dense | `41925aad6d7042d5a044eb85b3107923` | `1ca281efcc8c411f97a527f6ee744e60` | 4,037 seconds |

BM25 used eight query workers. The dense run recorded `cuda:0`. It reused cached passage embeddings and performed exact top-100 ranking with NumPy block scans.

## Independent verification

NIST `trec_eval` 10.0-rc3 at commit `35cf096ba6d5ae08ca4803c056b31ed61a56a6d4` checked 40 aggregate values. All values agreed within `0.00005`, which matches the four-decimal output precision of `trec_eval`.

See `results/trec/STEP-12-VERIFICATION.md` and `results/trec/verification.json`.

## Interpretation limits

MIRACL relevance judgments are incomplete. An unjudged passage receives zero credit in this evaluation, but this does not prove that a human judged it irrelevant.

The public development labels were visible. The protocol was frozen after diagnostic and train-pilot work but before the full development-set run. Later failure analysis is exploratory.
