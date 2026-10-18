# Arabic normalization retrieval protocol

Status: **the declared primary full-corpus comparison was completed on 2026-10-15**. The authored diagnostic, train-split pilot, and 100-query development run are exploratory development exercises. The final study used the complete corpus and all 2,896 public development queries.

## Question and hypotheses

Question: Under a fixed retrieval pipeline, how does Arabic orthographic normalization affect retrieval quality, and which query/document characteristics explain gains and losses?

Primary hypothesis: applying the conservative preset to both queries and passages improves mean BM25 nDCG@10 compared with raw text on the declared evaluation population.

Secondary hypotheses: the dense retriever changes less than BM25; aggressive normalization causes more query-level regressions than conservative normalization; named-entity queries are vulnerable to character conflation. These are hypotheses, not promised findings. A zero or negative primary difference is a valid outcome.

## Freeze this decision record


| Decision                      | Initial specification / fill before running                                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Author, date, protocol commit | Ahmad; 2026-10-13; docs freeze commit `d853cdc`                                                                                      |
| Dataset scope                 | `full-corpus-all-dev-queries` for the main claim; `diagnostic` and `miracl-pilot` with `split: train` are development exercises    |
| Evaluation query split        | MIRACL Arabic dev; use train only for code debugging / any hyperparameter tuning                                                   |
| Query population              | All 2,896 MIRACL Arabic dev queries; no outcome-based selection                                                                     |
| Corpus                        | Complete official Arabic passage collection for benchmark claims; preserve passage IDs                                             |
| Topics/qrels revision         | `5be20db9509754dadad47689368639fcec739c00`                                                                                         |
| Corpus revision               | `d921ec7e349ce0d28daf30b2da9da5ee698bef0d`                                                                                         |
| Retrieval unit                | Original passage; no new chunking, deduplication, or relabeling                                                                    |
| Input text                    | Title + newline + passage text; same rule in every arm                                                                             |
| Primary comparison            | BM25 conservative minus BM25 raw, both-side normalization                                                                          |
| Primary metric                | Per-query nDCG@10, averaged equally across queries                                                                                 |
| Secondary metrics             | Recall@5, Recall@10, MRR@10, Recall@100                                                                                            |
| Retrieval depth               | 100                                                                                                                                |
| BM25                          | Controlled SQLite BM25; Unicode-category-v1 tokenizer; k1=1.2, b=0.75; unique query terms; corpus-ordinal ascending tie-break |
| Dense model                   | `facebook/mcontriever-msmarco`, revision `9ff6abed2c2fdf32bbbd8b4e98fb10160e317375`                                                |
| Dense pipeline                | SentenceTransformers mean pooling, L2-normalized vectors / cosine; no text prefixes; length 256; batch 32; record effective config |
| Dense interpretation          | A fixed mean-pooled cosine pipeline; not a reproduction of the original dot-product baseline                                      |
| Normalization side            | Both query and document; query-only is a separately labeled secondary study                                                        |
| Bootstrap                     | Paired query resampling with replacement, 10,000 samples, seed 42, percentile 95% interval                                         |
| Primary effect scale          | Absolute mean metric difference; also report relative change only if baseline > 0                                                  |
| Practical effect threshold    | No practical-effect threshold is set; interpret the observed absolute delta, paired 95% interval, and win/loss/tie counts together  |
| Other comparisons             | Exploratory; no family-wide significance claim from unadjusted individual intervals                                                |
| Manual review                 | Five largest nDCG wins, five largest losses, and ten random ties per chosen comparison; report fewer when unavailable              |
| Named-entity labels           | If reported, label 100 dev queries selected by lowest SHA-256 of `42:qid` before viewing dev rankings; save rubric, annotator, disagreements and counts |
| Hardware/software             | Host: Intel Core 9 270H, 32 GB RAM, RTX 5070 Laptop GPU 8 GB, Windows 11. Runs: Docker/WSL2 Linux 6.6.87.2, Python 3.12.13, SQLite 3.46.1. The final dense report recorded `device=cuda:0`, SentenceTransformers 6.1.0, Transformers 5.19.0, Torch 2.14.1 and NumPy 2.5.4. Exact run-time Git revisions were not captured; the saved engine source SHA-256 is `43b8f73abaeaf5e5f6f367d5eec11a559c536929c40935bdeb4f2078d15b59ba`. |


The public dev set is already visible; this is preregistration of your analysis, not a claim of a private blind test. If you inspect dev outcomes to change transforms, report that phase as exploratory. Do not silently promote a tuned dev result into a held-out claim.

## Exact primary transformations

These are the dedicated Arabic Norm experiment presets. Their names do **not** mean the same thing as the older, broader general Eval Lab presets.


| Preset       | Transformations, in order                             |
| ------------ | ----------------------------------------------------- |
| raw          | No external normalization.                            |
| diacritics   | Remove U+064B–U+0652 only.                            |
| tatweel      | Remove U+0640 only.                                   |
| alef         | U+0623 أ, U+0625 إ, U+0622 آ → U+0627 ا.              |
| conservative | Diacritics + tatweel + Alef above.                    |
| aggressive   | Conservative + U+0649 ى→U+064A ي + U+0629 ة→U+0647 ه. |


No preset adds stemming, stop words, digit conversion, Unicode NFC/NFKC, wasla ٱ replacement, standalone hamza deletion, ؤ/ئ replacement, or punctuation conversion. Those can be follow-up studies after this one. If the model tokenizer transforms text internally, keep that tokenizer fixed and disclose that raw means **no external Arabic normalization**, not absence of internal model preprocessing.

## Statistical and interpretation rules

For each query, compute `d_i = metric(candidate_i) - metric(raw_i)`. Resample the same query indices on both sides and calculate the mean difference for every bootstrap sample. Report the observed delta and the 2.5th/97.5th percentiles. Do not subtract independently bootstrapped marginal intervals. If the interval includes zero, say the data do not distinguish the sign at that uncertainty level; do not claim equivalence. Very few queries yield fragile intervals. If related queries create dependence, discuss it and consider a separately documented cluster bootstrap.

The different retrievers must use identical corpus IDs, query IDs, qrels, and tie policy. Retain relevant passages missing from an index in the recall denominator; missing positives are a data-integrity failure for this experiment, not grounds to make recall easier. Unjudged MIRACL passages receive zero credit in standard qrels-based scoring; this does not prove that humans judged them irrelevant.

Measure activation on both queries and documents. An unchanged query can change rank because document text, lexical document frequency, or embeddings changed. A query-changed subset is a useful description, not a complete accounting of the treatment's effect.

Show all declared variants, even losing ones. Preserve original Arabic, normalized text, passage IDs, ranks, and metric deltas for case studies. Report collision examples as mechanisms; the tiny authored fixture is not evidence of their real-world frequency.

## Deviations log


| Date | Change | Reason | Were evaluation results already viewed? | Analysis affected |
| ---- | ------ | ------ | --------------------------------------- | ----------------- |
| 2026-10-13 | Initial protocol freeze after diagnostic and MIRACL train-pilot development runs | The diagnostic and pilot established that the workflow executes before committing resources to the main study | Yes—diagnostic and train-pilot results only; no full-corpus dev results | Development runs remain exploratory; the declared full-corpus dev comparison is confirmatory only with respect to this freeze |
| 2026-10-14 | Added a 100-query public-dev run before the full run | Estimate cost and confirm the full-corpus workflow on available hardware | Yes—diagnostic and train-pilot results; the 100-query outcomes became visible after this run | The 100-query results are exploratory and are not the final claim |
| 2026-10-15 | Limited the final full run to raw and conservative conditions | Available compute did not support all six planned conditions | Yes—the exploratory 100-query raw/conservative results were visible | The preregistered primary comparison remains available; hypotheses about the other four conditions were not tested on all 2,896 queries |
| 2026-10-15 | Used eight BM25 query workers and external caches; dense reported `cuda:0` | Use the available CPU and GPU efficiently and preserve expensive indexes and embeddings | Yes—exploratory results were visible | Performance changed; scoring rules, model weights, query population and primary comparison did not change |
| 2026-10-17 | Derived more metrics and performed failure analysis from saved rankings | Improve reporting without repeating retrieval | Yes—all final outcomes were visible | Additional metrics and case review are exploratory; original nDCG, recall and MRR values were reproduced exactly |




## Completion criteria

- [x] Data provenance, complete configs and rankings are saved.
- [ ] A clean full raw BM25 rerun has not been completed. This remains an optional, expensive publication check.
- [x] The normalizer, tokenizer and metric tests pass.
- [x] Omitted full-run conditions are recorded as a protocol deviation.
- [x] The main result includes a paired interval and win/loss/tie counts.
- [x] The failure-analysis file includes gains, regressions and ties.
- [x] Claims match the actual corpus, query scope, model and preprocessing.
