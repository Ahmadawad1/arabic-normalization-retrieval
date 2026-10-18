# Tutorial: Evaluating Arabic Text Normalization for Retrieval

This tutorial explains the experiment from the research question to the final conclusion. It is written for readers who are new to AI evaluation and information retrieval.

## 1. What problem does this experiment study?

Arabic words can have several written forms that express the same intended word.

For example:

- `إجراءات` and `اجراءات` differ in their Alef form.
- `إجــراءات` contains tatweel, which stretches the word visually.
- A word can contain vowel marks in one document and no vowel marks in another.

A lexical search system can treat these forms as different tokens. This can prevent a useful passage from matching a query.

Normalization changes selected characters into a common form. This can improve matching. It can also remove useful distinctions and produce worse rankings.

The experiment asks:

> Does conservative Arabic normalization improve retrieval quality when the data and retrieval system stay fixed?

## 2. A simple mental model

Think of retrieval as a race.

1. A user provides a query.
2. The retrieval system compares the query with every passage.
3. The system assigns a score to each passage.
4. The system sorts passages by score.
5. The evaluation checks where the known relevant passages appear.

This experiment runs the same race twice:

- **Raw condition:** no external Arabic normalization.
- **Conservative condition:** apply the declared Arabic transformations to queries and passages.

Everything else must stay fixed. If another part changes, we cannot clearly connect the score difference to normalization.

## 3. What does “raw” mean?

Raw means that this experiment applies no external Arabic normalization.

It does not mean that the computer sees untouched characters at every internal stage.

BM25 still uses a fixed tokenizer to separate text into tokens. The dense model still uses its own fixed model tokenizer. A model tokenizer converts text into the numeric token IDs that the model accepts.

The important rule is simple:

> Keep the internal tokenizer fixed in both conditions. Change only the declared external normalization.

## 4. The conservative transformation

The conservative condition applies these operations in order:

1. Remove Arabic diacritics from U+064B through U+0652.
2. Remove tatweel U+0640.
3. Map `أ`, `إ`, and `آ` to `ا`.

It does not add stemming, stop-word removal, digit conversion, Unicode folding, or punctuation conversion.

The word “conservative” is only the name of this smaller rule set. It does not guarantee that the transformation is harmless.

## 5. Why compare two retrievers?

The experiment uses BM25 and a dense retriever because they represent two different ways to search.

### BM25

BM25 is a lexical retriever. It depends strongly on token overlap between the query and passage.

If the query contains `اجراءات` and a passage contains `إجراءات`, raw BM25 can treat them as different tokens. Normalization can make the tokens match.

This experiment uses:

- `k1 = 1.2`
- `b = 0.75`
- unique query terms
- a fixed Unicode-category tokenizer
- corpus order as the final tie-break rule

### Dense retrieval

Dense retrieval converts each query and passage into a numeric vector. Similar vectors receive higher scores.

Dense models can sometimes learn that two spelling variants are related. This means external normalization might help less than it helps BM25. However, normalization can still change tokenization, truncation, and the final vector.

This experiment uses:

- model: `facebook/mcontriever-msmarco`
- model revision: `9ff6abed2c2fdf32bbbd8b4e98fb10160e317375`
- mean pooling
- L2-normalized vectors
- cosine similarity
- maximum sequence length 256
- batch size 32
- no query or passage prefix

This is one fixed dense pipeline. It does not represent every dense retrieval model.

## 6. Dataset and evaluation population

The final experiment uses:

- 2,061,414 MIRACL Arabic passages
- all 2,896 Arabic public development queries
- 29,197 relevance judgments
- retrieval depth 100

The source revisions are fixed:

- topics and qrels: `5be20db9509754dadad47689368639fcec739c00`
- corpus: `d921ec7e349ce0d28daf30b2da9da5ee698bef0d`

The public development labels were already visible. Therefore, this is not a private blind test.

The protocol was frozen after diagnostic and train-pilot work but before the complete development-set run. The later query-level failure analysis is exploratory because the outcomes were visible at that time.

## 7. Why use the complete corpus?

A small candidate corpus is useful for checking code. It is not a substitute for the full benchmark.

If we select passages using relevance labels, the resulting task becomes easier. Its retrieval scores are not directly comparable with a full-corpus evaluation.

The final result uses every official Arabic passage. This preserves the real competition between relevant and non-relevant candidates.

The small fictional dataset in `data/diagnostic/` serves a different purpose. It checks that transformations, ranking, and metrics behave as expected. It does not provide benchmark evidence.

## 8. The controlled comparison

The independent variable is the text condition:

- raw
- conservative

The following items stay fixed:

- passage IDs and boundaries
- query IDs
- relevance judgments
- query population
- input field rule: title, newline, then passage text
- retrieval depth
- BM25 parameters
- dense model weights and revision
- dense pooling and similarity
- random seed
- tie policy

Normalization is applied to both the query and the passage. This is important for BM25 because a shared normalized form improves the chance of exact token overlap.

## 9. The main hypothesis

The primary hypothesis was:

> Conservative normalization on both queries and passages improves mean BM25 nDCG@10 compared with raw text.

The primary hypothesis was selected before the complete development-set run.

The original protocol also described more normalization conditions. The full run used only raw and conservative because of the available compute. This is recorded as a protocol deviation. The primary comparison remained unchanged.

## 10. Metrics in simple language

No single metric explains the complete ranking. This experiment reports several metrics.

### nDCG@10

nDCG@10 measures ranking quality in the first ten results. It gives more value to relevant passages near the top. It also uses graded relevance labels.

- `1.0` means an ideal top-ten ranking for that query.
- `0.0` means no judged relevant passage received credit in the top ten.

This is the primary metric.

### Precision@10

Precision@10 asks:

> What fraction of the first ten retrieved passages are judged relevant?

MIRACL judgments are incomplete. An unjudged passage gets zero credit, but it is not necessarily irrelevant. This makes precision a conservative estimate.

### Recall@10 and Recall@100

Recall asks:

> What fraction of all known relevant passages did the system retrieve?

Recall@10 checks the first ten results. Recall@100 checks the first 100 results.

### MRR@10

MRR@10 measures how early the first relevant passage appears in the top ten.

- Relevant at rank 1 gives `1.0`.
- Relevant at rank 2 gives `0.5`.
- No relevant passage in the top ten gives `0.0`.

MRR does not reward additional relevant passages after the first one.

### Average precision

Average precision rewards systems that retrieve several relevant passages and place them early. The report uses AP@100 for each query and averages it across queries.

## 11. Why use a paired comparison?

Each query runs in both conditions. This creates a natural pair:

```text
query difference = conservative score - raw score
```

The experiment calculates this difference for every query. It then averages the query differences.

This is better than treating the two conditions as unrelated samples. The paired design controls for query difficulty because each query acts as its own comparison.

## 12. What is the bootstrap interval?

The experiment uses a paired bootstrap with 10,000 samples and seed 42.

For each bootstrap sample:

1. Sample 2,896 query positions with replacement.
2. Use the same sampled positions for raw and conservative.
3. Calculate the average paired difference.

The 2.5th and 97.5th percentiles form the reported 95% interval.

If the interval stays above zero, the observed improvement has a consistent positive sign under this resampling method. If the interval crosses zero, the data do not clearly determine the sign at this uncertainty level.

This interval is not proof that the result will generalize to every Arabic dataset.

## 13. How to install the project

Clone the repository and enter its directory:

```powershell
git clone https://github.com/Ahmadawad1/arabic-normalization-retrieval.git
Set-Location arabic-normalization-retrieval
```

Install the base and test dependencies:

```powershell
uv sync --extra dev
```

Run the tests:

```powershell
uv run pytest
```

The repository currently has 21 tests. They check normalization, tokenization, BM25 calculations, invalid data, paired statistics, cache reuse, MIRACL preparation, and TREC export behavior.

Install the dense dependencies only when you need dense retrieval:

```powershell
uv sync --extra dev --extra dense
```

## 14. How to prepare MIRACL

Run this command from the repository root:

```powershell
uv run arabic-retrieval prepare-miracl `
  --output work/miracl-ar-full-dev `
  --mode full `
  --split dev `
  --seed 42 `
  --dataset-revision 5be20db9509754dadad47689368639fcec739c00 `
  --corpus-revision d921ec7e349ce0d28daf30b2da9da5ee698bef0d
```

This command:

1. Downloads the pinned Arabic query and qrel files.
2. Downloads and scans all five Arabic corpus shards.
3. Writes `queries.jsonl`, `qrels.tsv`, `corpus.jsonl`, and `provenance.json`.
4. Calculates hashes for the prepared files.
5. Keeps an `INCOMPLETE` marker until preparation finishes successfully.

The full corpus file is approximately 1.28 GB in this experiment.

## 15. How to import the prepared dataset

```powershell
uv run arabic-retrieval import `
  --name "MIRACL Arabic full corpus all dev queries" `
  --corpus work/miracl-ar-full-dev/corpus.jsonl `
  --queries work/miracl-ar-full-dev/queries.jsonl `
  --qrels work/miracl-ar-full-dev/qrels.tsv `
  --provenance work/miracl-ar-full-dev/provenance.json
```

The import validates the identifiers and relevance judgments. It also creates an immutable local dataset record.

Save the returned `dataset_id`. The run commands require it.

## 16. How to run BM25

Use eight workers on a similar CPU:

```powershell
$env:EVAL_BM25_QUERY_WORKERS = '8'
```

Run the two conditions:

```powershell
uv run arabic-retrieval run `
  --dataset DATASET_ID `
  --retrievers bm25 `
  --presets raw conservative `
  --normalization-side both `
  --bootstrap-samples 10000 `
  --seed 42
```

The completed full BM25 run took 1,499 seconds, or about 25 minutes, on the recorded machine.

## 17. How to run dense retrieval

First confirm that the installed PyTorch build can see the GPU:

```powershell
uv run python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Then run:

```powershell
uv run arabic-retrieval run `
  --dataset DATASET_ID `
  --retrievers dense `
  --presets raw conservative `
  --normalization-side both `
  --bootstrap-samples 10000 `
  --seed 42 `
  --dense-model facebook/mcontriever-msmarco `
  --dense-revision 9ff6abed2c2fdf32bbbd8b4e98fb10160e317375 `
  --dense-max-seq-length 256 `
  --dense-batch-size 32
```

The model uses the GPU for encoding when CUDA is available. Exact ranking scans the saved vectors in blocks with NumPy.

The recorded full dense run took 4,037 seconds, or about 67 minutes. This run reused passage embeddings from the earlier 100-query run. A first run that must encode all passages will take much longer.

## 18. Saved results

The final scores are:

| Retriever | Metric | Raw | Conservative | Difference | Paired 95% interval |
|---|---|---:|---:|---:|---:|
| BM25 | nDCG@10 | 0.345234 | 0.360498 | +0.015264 | [0.010742, 0.019882] |
| BM25 | Precision@10 | 0.077970 | 0.082113 | +0.004144 | [0.003004, 0.005318] |
| BM25 | Recall@10 | 0.454999 | 0.476873 | +0.021874 | [0.015144, 0.028767] |
| BM25 | MRR@10 | 0.358240 | 0.373373 | +0.015133 | [0.009586, 0.020830] |
| BM25 | Recall@100 | 0.719024 | 0.751656 | +0.032633 | [0.026479, 0.038959] |
| Dense | nDCG@10 | 0.364622 | 0.360294 | -0.004328 | [-0.009548, 0.000777] |
| Dense | Precision@10 | 0.086395 | 0.085739 | -0.000656 | [-0.002106, 0.000794] |
| Dense | Recall@10 | 0.504929 | 0.496792 | -0.008137 | [-0.016228, -0.000275] |
| Dense | MRR@10 | 0.365282 | 0.361857 | -0.003425 | [-0.009806, 0.002978] |
| Dense | Recall@100 | 0.802570 | 0.799136 | -0.003434 | [-0.010493, 0.003552] |

For BM25, the primary nDCG@10 improvement is about 4.42% relative to the raw score. The interval stays above zero.

For dense retrieval, the nDCG@10 estimate is slightly negative. Its interval crosses zero. Therefore, the experiment does not show a reliable nDCG@10 improvement for this dense pipeline.

## 19. Wins, losses, and ties

An average can hide different query behaviors.

For BM25 nDCG@10:

- 251 queries improved.
- 203 queries became worse.
- 2,442 queries tied.

For dense nDCG@10:

- 593 queries improved.
- 577 queries became worse.
- 1,726 queries tied.

Many BM25 queries tied because the selected transformation did not change useful matching terms or did not change the first ten judged results.

Dense retrieval changed more query rankings, but its gains and losses mostly balanced. This is why a high number of changed queries does not automatically produce a positive average effect.

## 20. Example query behavior

For BM25 query `9952`, the query was:

```text
ما هي عاصمة استراليا؟
```

The selected relevant passage moved from rank 53 to rank 1 after conservative normalization. The query received an nDCG@10 gain of `1.0`.

For BM25 query `11598`, the query was:

```text
ما هو الأَسْبِرِين؟
```

The selected relevant passage moved from rank 1 to rank 18. The query received an nDCG@10 loss of `1.0`.

These rank movements are facts from the saved results. They do not by themselves prove one linguistic cause. A causal explanation requires inspection of the query, relevant passage, competing passages, normalized strings, and term statistics.

See `results/metrics/failure-analysis.tsv` for the saved evidence.

## 21. Independent verification

The experiment exported four standard TREC run files:

1. BM25 raw.
2. BM25 conservative.
3. Dense raw.
4. Dense conservative.

NIST `trec_eval` 10.0-rc3 independently checked 40 aggregate values. Every checked value agreed with the saved metrics within `0.00005`.

This check reduces the chance that the conclusion depends on a private metric implementation error.

See:

- `results/trec/STEP-12-VERIFICATION.md`
- `results/trec/verification.json`

## 22. What the result supports

The experiment supports this narrow conclusion:

> The declared conservative Arabic normalization improved BM25 retrieval on the complete public MIRACL Arabic development set under the fixed pipeline.

It also supports this dense result:

> The same normalization did not show a reliable nDCG@10 improvement for the fixed mContriever pipeline.

## 23. What the result does not support

The experiment does not prove that:

- normalization always improves Arabic search
- the rule set is best for every Arabic domain
- all dense models react in the same way
- unjudged passages are irrelevant
- the result is a private held-out benchmark result
- the exploratory failure-analysis stories are causal explanations

Wikipedia passages differ from dialectal messages, OCR text, legal archives, product search, and fully vocalized educational text.

## 24. How to design a follow-up experiment

Use a new protocol before inspecting new outcomes.

A useful follow-up can test one change at a time:

- query-only normalization
- separate diacritic, tatweel, and Alef conditions
- aggressive `ى→ي` and `ة→ه` mappings
- a different Arabic embedding model
- OCR or dialectal Arabic data
- latency, memory, and index-size effects

Do not select the best transformation on the public development set and then describe that score as a new held-out result. Use a separate test set or clearly label the work as exploratory.

## 25. Where to find each artifact

| Need | File or directory |
|---|---|
| Research decisions and deviations | `docs/PROTOCOL.md` |
| Hardware and run identifiers | `docs/REPRODUCIBILITY.md` |
| Every recorded run | `docs/run-register.tsv` |
| Main result summary | `results/metrics/FINAL-REPORT.md` |
| Machine-readable aggregate results | `results/metrics/final-metrics.json` |
| Tidy aggregate table | `results/metrics/metrics-summary.csv` |
| Per-query scores | `results/metrics/per-query-metrics.csv` |
| Failure cases | `results/metrics/failure-analysis.tsv` |
| Standard rankings | `results/trec/` |
| Original reports | `results/run-reports/` |
| Artifact checksums | `results/SHA256SUMS` |
| Dataset mirror | [Hugging Face](https://huggingface.co/datasets/ahmad-awad/arabic-normalization-retrieval) |

## Final lesson

Normalization is not automatically good or bad. It changes the information available to the retrieval system.

The correct evaluation keeps the rest of the pipeline fixed, measures paired query differences, reports both gains and losses, records uncertainty, and limits the conclusion to the tested data and systems.
