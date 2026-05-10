# NORI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](CHANGELOG.md)
[![Validate submission](https://github.com/tenki-labs/nori/actions/workflows/validate-submission.yml/badge.svg)](https://github.com/tenki-labs/nori/actions/workflows/validate-submission.yml)

**NOR**wegian **I**diomatic. A reproducible benchmark that measures how natively Norwegian an LLM's Norwegian output actually is.

NORI scores generated text against a reference distribution of native Norwegian on five axes drawn from translation studies, the field that has spent thirty years naming the structural signatures of translated text. Standard Norwegian LLM evaluation (NorEval, FLORES-style chrF/BLEU) measures whether the model produces correct words. NORI measures whether the model produces *Norwegian* words in *Norwegian* structure, or whether it produces translatese: grammatically correct Norwegian words arranged in English-shaped sentences.

## Leaderboard

The headline number is **NORI score** (`[0, 100]`, higher is more native Norwegian). It is the arithmetic mean of the five axes scaled to a percentage, analogous to MMLU and GLUE. Two diagnostic aggregates accompany it:

* `nori_min` is the lowest of the five axes × 100. A weakest-link indicator: a model with four strong axes and one near-zero axis still feels translated to a native reader.
* `nori_g` is the geometric mean × 100. Penalizes weak axes much more than the arithmetic mean and is closer to how a human reader perceives an output: one bad axis pulls the whole impression down.

| Rank | Model | NORI | nori_min | nori_g | Eksplisittering | Normalisering | Forenkling | Utjevning | Interferens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen25-1_5b-instruct | **39.7** | 5.0 | 27.8 | 0.661 | 0.263 | 0.050 | 0.250 | 0.760 |
| 2 | qwen25-3b-instruct | **34.9** | 0.7 | 14.2 | 0.777 | 0.214 | 0.007 | 0.074 | 0.673 |

*(NORI v0.1.0 baseline. Greedy decoding, single seed, 25-prompt standard set. Per-axis scores are in `[0, 1]`, where 1.0 matches the native distribution within tolerance.)*

The two `nori_min` values illustrate why the secondary metric matters: both models score 14 to 35 on the geometric mean and 0.7 to 5.0 on the weakest-link indicator, even though the headline arithmetic mean is in the mid-30s. A native reader who hits the simplification axis (heavy lexical repetition) will perceive that single failure even when other axes are strong.

To submit a new model to the leaderboard, see [CONTRIBUTING.md](CONTRIBUTING.md). The leaderboard updates on merged PRs that add submissions to `data/outputs/`.

## Why NORI

A Norwegian reader can identify machine-generated text within two sentences, even when every individual sentence is grammatical. The reason is structural, not lexical. LLMs trained predominantly on English produce Norwegian that is calqued from English: comma-spliced compound sentences, em dashes, redundant connectives ("derfor", "imidlertid"), V2 violations, *særskriving* of compounds, absent modal particles ("jo", "da", "vel"). Translation studies has named the universal signatures of this kind of text. NORI measures them.

## The five axes

| Axis | What it captures | Measurement |
|---|---|---|
| **Eksplisittering** (Explicitation) | Spelled-out logic, redundant connectives | Connectives per 1000 words |
| **Normalisering** (Normalization) | Over-conventional, low-variance prose | Sentence-length std vs reference |
| **Forenkling** (Simplification) | Lower vocabulary diversity, shorter words | MTTR-1000, mean word length |
| **Utjevning** (Levelling out) | Regression toward genre mean | Sentence-length distance from reference |
| **Kildespraak-interferens** (Source-language interference) | English structural calques | Em-dash density, V2 violations, compound integrity |

Each axis is normalized to `[0, 1]` where `1.0` means the model output matches the native distribution within tolerance and `0.0` means it drifts far from native. The composite NORI score is the mean of the five axes.

## Quick start

```bash
git clone https://github.com/tenki-labs/nori.git
cd nori

# 1. Pull native Norwegian reference corpus (Wikipedia + Project Gutenberg)
make data

# 2. Compute baseline distribution from reference corpus
make baseline

# 3. Generate text from the model panel on the standard prompt set
make generate

# 4. Score every model against the native baseline
make score
```

End-to-end runs in roughly one hour on a 16 GB consumer GPU.

To benchmark a single text without going through the full model pipeline:

```python
import json
from scripts.metrics import measure_text, score, CorpusMetrics, aggregate

# Load the precomputed native baseline
with open("results/baseline_native.json", encoding="utf-8") as f:
    rec = json.load(f)
native = CorpusMetrics()
for k, v in rec["results"]["_combined"].items():
    if hasattr(native, k):
        setattr(native, k, v)

# Score a single piece of text
text = "..."  # Your Norwegian text here
m = measure_text(text)
cm = aggregate([m])
result = score(cm, native)
print(result.composite, result.__dict__)
```

## Adding a model to the benchmark

Edit the `MODELS` list in `scripts/20_run_models.py`:

```python
MODELS = [
    {"id": "qwen25-3b-instruct", "hf": "Qwen/Qwen2.5-3B-Instruct", "qlora": True},
    {"id": "your-model-id",      "hf": "Org/Repo",                  "qlora": True},
]
```

Re-run `make generate && make score`. Existing model outputs are cached on disk, so the new model is the only one that gets generated.

## Reference baseline

| Source | n docs | n words | License | Note |
|---|---:|---:|---|---|
| Norwegian Bokmaal Wikipedia (20231101.no parquet) | 1,500 | 670k | CC-BY-SA-4.0 | Length-filtered to 1500 to 6000 chars |
| Project Gutenberg classics (Bjornson, Hamsun, Ibsen, Lie, Kielland) | 5 works, 301 chunks | 487k | Public domain | Older register, but unambiguously native |

Total: 1,801 chunks, roughly 1.16M words.

## Standard prompt set

25 prompts across 5 registers, 1 language (Bokmaal):

* 5 editorial / opinion (`ed01` to `ed05`)
* 5 personal essay / narrative (`pe01` to `pe05`)
* 5 technical explanation (`te01` to `te05`)
* 5 argumentative / persuasive (`ar01` to `ar05`)
* 5 letter / formal correspondence (`le01` to `le05`)

All prompts ask for 200 to 300 words. The same prompts run for every benchmarked model.

## Example scorecard

After running on Qwen 2.5 Instruct 1.5B and 3B (greedy decoding, single seed):

| Model | composite | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|
| qwen25-1_5b-instruct | **0.397** | 0.661 | 0.263 | 0.050 | 0.250 | 0.760 |
| qwen25-3b-instruct | **0.349** | 0.777 | 0.214 | 0.007 | 0.074 | 0.673 |

The standout signal is the simplification axis (0.05 and 0.007 against a tolerance calibrated to native variance). Both models repeat themselves heavily within 1000-token windows. MTTR-1000 of 0.18 and 0.28 against a native baseline of 0.55 quantifies what manual inspection of any specific output confirms: the models cycle through a narrow vocabulary and reuse phrases.

## Limitations

The V2 violation heuristic is noisy. The current implementation uses spaCy's dependency parser to count syntactic constituents before the main verb. Imperatives, questions, and sentence fragments all flag as "violations" by this heuristic. The native baseline therefore shows a 34% violation rate, which is above what a careful V2-only count would yield. Relative model-to-baseline comparison is still meaningful, but the absolute number should not be read as "this percent of clauses violate V2." A better implementation would filter to declarative main clauses only.

The reference corpus has translation drift. Norwegian Wikipedia includes some articles that are translated from English versions. Project Gutenberg supplements with unambiguously native literature, but skews older. A future iteration should add modern newspaper editorials (for example via the National Library of Norway's bokhylla.no archive under research license) to the reference.

There is no native-speaker calibration yet. The composite score's tolerances are chosen empirically from the reference corpus's distribution. They have not been calibrated against human "this feels native vs translated" judgments. A natural next step is to collect such judgments on 100 to 200 outputs and tune tolerances against them. Until then, NORI scores are *relative* numbers against the specific native reference we built; they are useful for comparing models against each other, less useful as standalone quality claims.

NORI evaluates Bokmaal only. Nynorsk has different stylistic conventions, requires its own reference corpus, and is not currently measured. The five-axis framework is language-independent; building NORI-NN is mostly a matter of corpus and tolerance recalibration.

The decoder is greedy by default. Sampling temperature is 0 to make the benchmark deterministic. Models may produce different output under sampling; this is unmeasured.

## Layout

```
nori/
  README.md                                   this file
  Makefile                                    `make data | baseline | generate | score`
  LICENSE
  configs/
    prompts.yaml                              25 standard test prompts
  scripts/
    _repro.py                                 seed_all, hash_file, log_run
    metrics.py                                core measurement library
    00_acquire_reference.py                   pull native Norwegian baseline
    10_compute_baseline.py                    aggregate baseline distributions
    20_run_models.py                          benchmark generations
    30_score.py                               compute scorecards
  data/
    reference/                                native baseline (Wikipedia + Gutenberg)
    outputs/<model_id>/<prompt_id>.txt        model generations
  results/
    baseline_native.json                      reference distribution
    scorecard.json                            per-model raw plus scored metrics
    scorecard.md                              human-readable comparison table
```

## Citing

If you use NORI in published work, cite as:

```
Holt, E. (2026). NORI: A Translation-Universals Benchmark for Norwegian LLMs.
tenki research preprint. https://github.com/tenki-labs/nori
```

## License

Code: MIT. Generated outputs and scorecards: CC-BY-4.0. Reference corpus provenance per the table above.
