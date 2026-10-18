# Arabic normalization for retrieval

This repository contains a controlled evaluation of Arabic text normalization for lexical and dense retrieval.

The experiment uses the complete MIRACL Arabic corpus and all 2,896 queries in the public development set. It compares raw text with conservative external normalization. The evaluation is not a private blind test.

## Main result

| Retriever | Raw nDCG@10 | Conservative nDCG@10 | Difference | Paired 95% interval |
|---|---:|---:|---:|---:|
| BM25 | 0.345234 | 0.360498 | +0.015264 | [0.010742, 0.019882] |
| Dense | 0.364622 | 0.360294 | -0.004328 | [-0.009548, 0.000777] |

Conservative normalization improved BM25 in this experiment. It did not show a reliable improvement for the dense retriever.

## Conservative normalization

The conservative condition applies three external transformations:

- Remove Arabic diacritics from U+064B through U+0652.
- Remove tatweel U+0640.
- Map `أ`, `إ`, and `آ` to `ا`.

Raw means no external Arabic normalization. The dense model still uses its fixed internal tokenizer.

## Repository contents

- `src/`: standalone experiment code and command-line interface.
- `tests/`: normalizer, metric, BM25, preparation, caching, and export tests.
- `scripts/`: metric derivation, failure analysis, report inspection, and TREC verification.
- `data/diagnostic/`: small fictional fixture for code checks only.
- `data/miracl-ar-dev/`: exact query set, qrels, and provenance. The 1.28 GB corpus is not stored in Git.
- `docs/PROTOCOL.md`: preregistered decisions and recorded deviations.
- `docs/run-register.tsv`: diagnostic, pilot, 100-query, and full-run records.
- `results/metrics/`: aggregate and per-query metrics plus failure analysis.
- `results/trec/`: four depth-100 TREC runs and independent `trec_eval` verification.
- `results/run-reports/`: summaries and compressed original JSON reports.

## Install

Install [uv](https://docs.astral.sh/uv/), then run:

```powershell
uv sync --extra dev
uv run pytest
```

Install the dense dependencies only when you need the dense retriever:

```powershell
uv sync --extra dev --extra dense
```

## Reproduce the full dataset

The following command downloads the pinned MIRACL files and prepares the complete Arabic development dataset:

```powershell
uv run arabic-retrieval prepare-miracl `
  --output work/miracl-ar-full-dev `
  --mode full `
  --split dev `
  --seed 42 `
  --dataset-revision 5be20db9509754dadad47689368639fcec739c00 `
  --corpus-revision d921ec7e349ce0d28daf30b2da9da5ee698bef0d
```

Import the prepared files:

```powershell
uv run arabic-retrieval import `
  --name "MIRACL Arabic full corpus all dev queries" `
  --corpus work/miracl-ar-full-dev/corpus.jsonl `
  --queries work/miracl-ar-full-dev/queries.jsonl `
  --qrels work/miracl-ar-full-dev/qrels.tsv `
  --provenance work/miracl-ar-full-dev/provenance.json
```

Save the returned `dataset_id`. Use it in the two commands below:

```powershell
$env:EVAL_BM25_QUERY_WORKERS = '8'
uv run arabic-retrieval run --dataset DATASET_ID --retrievers bm25 --presets raw conservative --normalization-side both --bootstrap-samples 10000 --seed 42

uv run arabic-retrieval run --dataset DATASET_ID --retrievers dense --presets raw conservative --normalization-side both --bootstrap-samples 10000 --seed 42 --dense-model facebook/mcontriever-msmarco --dense-revision 9ff6abed2c2fdf32bbbd8b4e98fb10160e317375 --dense-max-seq-length 256 --dense-batch-size 32
```

See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) for hardware, expected run time, saved identifiers, and verification details.

## Data and large artifacts

The saved dataset and result artifacts are also available in the [Hugging Face dataset repository](https://huggingface.co/datasets/ahmad-awad/arabic-normalization-retrieval).

This repository does not copy the MIRACL passage corpus or model cache. The preparation command retrieves the official pinned source files.

## License and attribution

The experiment code and original documentation use the MIT License. MIRACL and Wikipedia-derived data keep their upstream licenses and attribution requirements. See [docs/SOURCES.md](docs/SOURCES.md).
