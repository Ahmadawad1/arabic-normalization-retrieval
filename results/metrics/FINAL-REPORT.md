# Full MIRACL Arabic retrieval metrics

These metrics were derived from the immutable top-100 rankings of the completed 2,896-query BM25 and dense runs. No normalization, indexing, embedding, or retrieval was repeated.

## Key metrics

| Retriever | Metric | Raw | Conservative | Delta | Paired 95% CI |
|---|---|---:|---:|---:|---:|
| BM25 | ndcg_graded@10 | 0.345234 | 0.360498 | 0.015264 | [0.010742, 0.019882] |
| BM25 | precision@10 | 0.077970 | 0.082113 | 0.004144 | [0.003004, 0.005318] |
| BM25 | recall@10 | 0.454999 | 0.476873 | 0.021874 | [0.015144, 0.028767] |
| BM25 | mrr@10 | 0.358240 | 0.373373 | 0.015133 | [0.009586, 0.020830] |
| BM25 | ap@100 | 0.297734 | 0.310329 | 0.012595 | [0.008467, 0.016769] |
| BM25 | recall@100 | 0.719024 | 0.751656 | 0.032633 | [0.026479, 0.038959] |
| BM25 | hit_rate@10 | 0.577693 | 0.604627 | 0.026934 | [0.018992, 0.035221] |
| BM25 | r_precision | 0.230275 | 0.240449 | 0.010173 | [0.005601, 0.014808] |
| DENSE | ndcg_graded@10 | 0.364622 | 0.360294 | -0.004328 | [-0.009548, 0.000777] |
| DENSE | precision@10 | 0.086395 | 0.085739 | -0.000656 | [-0.002106, 0.000794] |
| DENSE | recall@10 | 0.504929 | 0.496792 | -0.008137 | [-0.016228, -0.000275] |
| DENSE | mrr@10 | 0.365282 | 0.361857 | -0.003425 | [-0.009806, 0.002978] |
| DENSE | ap@100 | 0.308360 | 0.306077 | -0.002283 | [-0.007252, 0.002803] |
| DENSE | recall@100 | 0.802570 | 0.799136 | -0.003434 | [-0.010493, 0.003552] |
| DENSE | hit_rate@10 | 0.645028 | 0.635704 | -0.009323 | [-0.019682, 0.000691] |
| DENSE | r_precision | 0.230057 | 0.227985 | -0.002072 | [-0.009770, 0.005664] |

## Complete aggregate metric suite

The machine-readable `metrics-summary.csv` and `final-metrics.json` include Precision, Recall, F1, Hit Rate, MRR, binary nDCG, graded nDCG, and AP at cutoffs 1, 3, 5, 10, 20, 50, and 100, plus R-Precision. Every conservative metric includes a paired 10,000-sample percentile interval and win/loss/tie counts.

## Interpretation warning

MIRACL relevance judgments are incomplete. This evaluation gives unjudged passages zero credit, but that does not establish that humans judged those passages irrelevant. Precision values are therefore conservative and should be interpreted alongside recall, graded nDCG, MRR, and AP.

The data are the complete public MIRACL Arabic development set, not a private blind test.

## Files

- `final-metrics.json`: provenance, definitions, aggregate metrics, paired intervals
- `metrics-summary.csv`: tidy aggregate table
- `per-query-metrics.csv`: all derived metrics for each query and condition
