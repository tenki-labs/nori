# NORI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](CHANGELOG.md)
[![Validate submission](https://github.com/tenki-labs/nori/actions/workflows/validate-submission.yml/badge.svg)](https://github.com/tenki-labs/nori/actions/workflows/validate-submission.yml)

**NOR**wegian **I**diomatic. A reproducible benchmark that measures how natively Norwegian an LLM's Norwegian output actually is.

NORI scores generated text against a reference distribution of native Norwegian on five axes drawn from translation studies, the field that has spent thirty years naming the structural signatures of translated text. Standard Norwegian LLM evaluation (NorEval, FLORES-style chrF/BLEU) measures whether the model produces correct words. NORI measures whether the model produces *Norwegian* words in *Norwegian* structure, or whether it produces translatese: grammatically correct Norwegian words arranged in English-shaped sentences.

## Leaderboards

NORI v1.0 ships two parallel benchmarks: **NORI** for Bokmaal and **NORI-NN** for Nynorsk. They share the same five-axis framework and scoring formula but use language-specific lexicons (modal particles, connectives, subordinators) and reference distributions.

The headline number on each is the **NORI score** (`[0, 100]`, higher is more native Norwegian): arithmetic mean of the five axes scaled to a percentage, analogous to MMLU and GLUE. Two diagnostic aggregates accompany it:

* `nori_min` is the lowest of the five axes × 100. A weakest-link indicator: a model with four strong axes and one near-zero axis still feels translated to a native reader.
* `nori_g` is the geometric mean × 100. Penalizes weak axes much more than the arithmetic mean and is closer to how a human reader perceives an output: one bad axis pulls the whole impression down.

### NORI (Bokmaal)

| Rank | Model | NORI | nori_min | nori_g | Eksplisittering | Normalisering | Forenkling | Utjevning | Interferens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | gemma-4-e4b-it | **46.3** | 25.0 | 42.3 | 0.333 | 0.250 | 0.457 | 0.420 | 0.854 |
| 2 | qwen25-1_5b-instruct | **37.1** | 5.0 | 26.7 | 0.661 | 0.263 | 0.050 | 0.250 | 0.630 |
| 3 | qwen25-3b-instruct | **29.3** | 0.7 | 12.8 | 0.777 | 0.214 | 0.007 | 0.074 | 0.390 |

### NORI-NN (Nynorsk)

| Rank | Model | NORI-NN | nori_min | nori_g | Eksplisittering | Normalisering | Forenkling | Utjevning | Interferens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | gemma-4-e4b-it | **48.0** | 16.3 | 40.5 | 0.419 | 0.845 | 0.271 | 0.163 | 0.700 |
| 2 | qwen25-1_5b-instruct | **34.2** | 0.9 | 18.8 | 0.486 | 0.371 | 0.009 | 0.258 | 0.586 |
| 3 | qwen25-3b-instruct | **22.2** | 0.1 | 4.3 | 0.375 | 0.004 | 0.001 | 0.104 | 0.625 |

*(NORI v2.0.0 baseline. Greedy decoding, single seed, 25-prompt standard set per language. Per-axis scores are in `[0, 1]`, where 1.0 matches the native distribution within tolerance. **Not comparable to v1.x scores**: the forenkling axis switched from MTTR-1000 to MTTR-100, the V2 measurement filters out non-declaratives, and the compound detector uses a dictionary lookup instead of a 30-prefix list. See [CHANGELOG.md](CHANGELOG.md) for migration notes.)*

**Notable observations from the v2.0.0 leaderboard.**

- **Gemma 4 E4B leads both languages** (NORI 46.3, NORI-NN 48.0 vs Qwen at 22 to 37). The gap is concentrated on the **forenkling** axis: Gemma's MTTR-100 of 0.70 (NB) is close to the native baseline of 0.72; Qwen 1.5B and 3B drop to 0.26 and 0.40. Qwen models cycle through a narrow vocabulary in a way Gemma does not.
- **Gemma is uniquely consistent across the two written standards.** It actually scores slightly *higher* on Nynorsk than Bokmaal under v2 scoring (48.0 vs 46.3), driven by an impressive normalisering of 0.85 on NN (highest single-axis score in the leaderboard). Qwen 3B drops 7 points NB to NN (29.3 to 22.2); Qwen 1.5B drops 3 points (37.1 to 34.2).
- Gemma's **modal-particle density exceeds native** on both languages (NB: 8.11 vs 1.81 per 1000 words; NN: 8.39 vs 2.79). It overcorrects toward "feels Norwegian" by sprinkling "jo, da, vel" much more aggressively than native writers do.
- Gemma's **connective density is also above native** on both languages (NB: 6.84 vs 3.62; NN: 5.93 vs 3.27), pushing eksplisittering into mid-0.4 range. The model spells out logic more than native writers, a classic translatese marker.
- **Qwen 3B's compound integrity drops to 0.85 (NB)** under the new dictionary-backed detector (v1.x reported 1.0). The vocabulary lookup picks up real särskriving errors in the Qwen 3B output that the v1.x prefix list missed.
- Both Qwen models continue to collapse on the Bokmaal-to-Nynorsk transition. Qwen 3B's NN modal-particle rate falls to 0.15 per 1000 words against a native NN baseline of 2.79 per 1000 words: when prompted in Nynorsk, the model continues to write in Bokmaal-shaped prose with NN orthography sprinkled on top.

To submit a new model to either leaderboard, see [CONTRIBUTING.md](CONTRIBUTING.md). Submissions go under `data/outputs/<model_id>/` for Bokmaal and `data/outputs_nn/<model_id>/` for Nynorsk. Either or both languages may be submitted in the same PR.

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

After running on Qwen 2.5 Instruct 1.5B and 3B against the v2.0 native baseline (greedy decoding, single seed):

| Model | composite | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|
| qwen25-1_5b-instruct | **0.371** | 0.661 | 0.263 | 0.050 | 0.250 | 0.630 |
| qwen25-3b-instruct | **0.293** | 0.777 | 0.214 | 0.007 | 0.074 | 0.390 |

The standout signal is still the simplification axis (0.05 and 0.007). Both models repeat themselves heavily, and v2.0's MTTR-100 (a stable window for 200 to 400 word outputs) makes the magnitude unambiguous: Qwen 1.5B and Qwen 3B sit at 0.26 and 0.40 against a native baseline of 0.72. The interferens axis drops for Qwen 3B in particular under v2.0 because the new vocabulary-backed compound detector picks up real särskriving errors that the v1.x prefix list missed.

## Limitations

The V2 violation heuristic is still noisy on absolute terms. v2.0 filters out interrogatives, imperatives, and sentence fragments (issue [#1](https://github.com/tenki-labs/nori/issues/1)), which drops the native baseline from 34 percent in v1.0 to 30 percent (Bokmaal) and 17 percent (Nynorsk). The remaining noise is parser-side: the spaCy dependency parser sometimes attaches topicalized phrases as multiple constituents, inflating the "things before the verb" count. Relative model-to-baseline comparison is meaningful, but the absolute V2 rate should not be read as "this percent of clauses violate V2." A more precise implementation would inspect spaCy constituent boundaries directly rather than counting child tokens.

The reference corpus has translation drift. Norwegian Wikipedia includes some articles that are translated from English versions. Project Gutenberg supplements with unambiguously native literature, but skews older. A future iteration should add modern newspaper editorials (for example via the National Library of Norway's bokhylla.no archive under research license) to the reference. The v2.0 `--baseline-mapping` flag (issue [#5](https://github.com/tenki-labs/nori/issues/5)) lets you score against Wikipedia and Gutenberg separately rather than the combined distribution.

There is no native-speaker calibration of tolerances yet. The composite score's tolerances are chosen empirically from the reference corpus's distribution. They have not been calibrated against human "this feels native vs translated" judgments. The v2.0 `--human` scoring path (issue [#3](https://github.com/tenki-labs/nori/issues/3)) is ready to anchor the leaderboard against native human writers; the shipped release does not yet include human-written outputs. Until human writers are added, NORI scores are *relative* numbers against the specific native reference we built; they are useful for comparing models against each other, less useful as standalone quality claims.

The decoder is greedy by default. Sampling temperature is 0 to make the benchmark deterministic. Sampling-decode evaluation (issue [#9](https://github.com/tenki-labs/nori/issues/9)) is tracked for a future release. Multi-seed evaluation infrastructure is shipped in v2.0 via the `--seeds` flag (issue [#4](https://github.com/tenki-labs/nori/issues/4)); submitters can opt in to multi-seed generation today.

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
