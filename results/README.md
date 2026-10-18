# Saved results

- `metrics/` contains the complete aggregate metric suite, per-query metrics, and exploratory failure analysis.
- `trec/` contains the four raw/conservative BM25/dense rankings, exact qrels, and independent `trec_eval` checks.
- `run-reports/` contains the four run summaries and a compressed archive of the original full JSON reports.

The four rankings are:

1. BM25 raw.
2. BM25 conservative.
3. Dense raw.
4. Dense conservative.

All final rankings use the same 2,896 queries, corpus, qrels, and top-100 depth.
