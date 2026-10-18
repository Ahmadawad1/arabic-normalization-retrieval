# Step 12 — Independent TREC verification

**Status: PASSED.** The official NIST `trec_eval` program independently checked 40 aggregate values across the full BM25 and dense raw/conservative rankings. Every value agrees with the saved Brainwave metrics within 0.00005, the tolerance required by `trec_eval`'s four-decimal summary output.

Evaluator: NIST `trec_eval` 10.0-rc3, source commit `35cf096ba6d5ae08ca4803c056b31ed61a56a6d4`.

| Retriever | Condition | Metric | Brainwave | trec_eval | Difference |
|---|---|---|---:|---:|---:|
| bm25 | conservative | r_precision | 0.240449 | 0.2404 | -0.000049 |
| bm25 | conservative | precision@5 | 0.124309 | 0.1243 | -0.000009 |
| bm25 | conservative | precision@10 | 0.082113 | 0.0821 | -0.000013 |
| bm25 | conservative | precision@100 | 0.014130 | 0.0141 | -0.000030 |
| bm25 | conservative | recall@5 | 0.379878 | 0.3799 | +0.000022 |
| bm25 | conservative | recall@10 | 0.476873 | 0.4769 | +0.000027 |
| bm25 | conservative | recall@100 | 0.751656 | 0.7517 | +0.000044 |
| bm25 | conservative | ndcg_graded@10 | 0.360498 | 0.3605 | +0.000002 |
| bm25 | conservative | ap@100 | 0.310329 | 0.3103 | -0.000029 |
| bm25 | conservative | mrr@10 | 0.373373 | 0.3734 | +0.000027 |
| bm25 | raw | r_precision | 0.230275 | 0.2303 | +0.000025 |
| bm25 | raw | precision@5 | 0.117818 | 0.1178 | -0.000018 |
| bm25 | raw | precision@10 | 0.077970 | 0.0780 | +0.000030 |
| bm25 | raw | precision@100 | 0.013429 | 0.0134 | -0.000029 |
| bm25 | raw | recall@5 | 0.362793 | 0.3628 | +0.000007 |
| bm25 | raw | recall@10 | 0.454999 | 0.4550 | +0.000001 |
| bm25 | raw | recall@100 | 0.719024 | 0.7190 | -0.000024 |
| bm25 | raw | ndcg_graded@10 | 0.345234 | 0.3452 | -0.000034 |
| bm25 | raw | ap@100 | 0.297734 | 0.2977 | -0.000034 |
| bm25 | raw | mrr@10 | 0.358240 | 0.3582 | -0.000040 |
| dense | conservative | r_precision | 0.227985 | 0.2280 | +0.000015 |
| dense | conservative | precision@5 | 0.126105 | 0.1261 | -0.000005 |
| dense | conservative | precision@10 | 0.085739 | 0.0857 | -0.000039 |
| dense | conservative | precision@100 | 0.015114 | 0.0151 | -0.000014 |
| dense | conservative | recall@5 | 0.386259 | 0.3863 | +0.000041 |
| dense | conservative | recall@10 | 0.496792 | 0.4968 | +0.000008 |
| dense | conservative | recall@100 | 0.799136 | 0.7991 | -0.000036 |
| dense | conservative | ndcg_graded@10 | 0.360294 | 0.3603 | +0.000006 |
| dense | conservative | ap@100 | 0.306077 | 0.3061 | +0.000023 |
| dense | conservative | mrr@10 | 0.361857 | 0.3619 | +0.000043 |
| dense | raw | r_precision | 0.230057 | 0.2301 | +0.000043 |
| dense | raw | precision@5 | 0.128591 | 0.1286 | +0.000009 |
| dense | raw | precision@10 | 0.086395 | 0.0864 | +0.000005 |
| dense | raw | precision@100 | 0.015152 | 0.0152 | +0.000048 |
| dense | raw | recall@5 | 0.396235 | 0.3962 | -0.000035 |
| dense | raw | recall@10 | 0.504929 | 0.5049 | -0.000029 |
| dense | raw | recall@100 | 0.802570 | 0.8026 | +0.000030 |
| dense | raw | ndcg_graded@10 | 0.364622 | 0.3646 | -0.000022 |
| dense | raw | ap@100 | 0.308360 | 0.3084 | +0.000040 |
| dense | raw | mrr@10 | 0.365282 | 0.3653 | +0.000018 |

`recip_rank` was run on separate rank-10 files so it checks MRR@10 rather than reciprocal rank over the full depth-100 ranking. All queries were included with `trec_eval -c`, using the exact saved qrels.
