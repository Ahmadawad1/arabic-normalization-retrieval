# Hugging Face release plan

GitHub is the main source-code repository. A Hugging Face dataset repository can provide easier access to the larger result artifacts.

Recommended Hugging Face contents:

- `metrics-summary.csv`
- `per-query-metrics.csv`
- `final-metrics.json`
- `failure-analysis.tsv`
- the four TREC ranking files
- the exact query, qrel, and provenance files
- the compressed original run reports

Do not upload model caches or a copied MIRACL corpus. Link to the official MIRACL source and preserve its attribution.

Add the Hugging Face dataset URL to the main README after that repository is created.
