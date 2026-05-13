# NORI changelog

All notable changes to this benchmark are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-11

Accuracy and scoring methodology overhaul. **NORI v2 scores are not comparable
to NORI v1.x scores.** The v1.0 leaderboard should be retired. The five-axis
framework is unchanged, but the underlying measurements were silently biased on
short LLM outputs and non-declarative sentences, leading to scoring artifacts
that this release removes.

### Changed (breaking)
- **Forenkling axis now uses MTTR-100, not MTTR-1000** (issue #2). The legacy
  metric fell back to plain TTR on documents under 1000 tokens, which fires on
  essentially every NORI-style 200 to 400 word output. The fallback conflated
  vocabulary diversity with document length, driving the simplification axis
  to artificially near-zero values for short outputs. MTTR-100 is well-defined
  at LLM output lengths and matches the standard window used in stylometry
  literature (Covington and McFall 2010). Tolerance retuned to 0.08.
  `mttr_1000` is retained as a deprecated diagnostic field.
- **V2 violation rate now filters to declarative main clauses only** (issue
  #1). Interrogatives, imperatives, exclamations, and sentence fragments no
  longer count toward the rate. V2 in Norwegian is a property of declarative
  main clauses, and counting non-declaratives as "violations" inflated the
  native baseline (Wiki 31 percent in v1.0 to ~12 percent in v2.0; NN 34
  percent to 17 percent), making the interferens axis reward models for
  producing only formal declarative prose.
- **Compound-integrity detection uses spaCy vocabulary lookup** (issue #6).
  The v1.x implementation flagged adjacent NOUN+NOUN bigrams against a
  hand-curated 30-prefix list, catching an estimated 5 to 10 percent of
  actual särskriving errors. The v2.0 detector checks the concatenation
  W1+W2 against the spaCy `nb_core_news_md` vocabulary (~50k known
  Norwegian word entries) and falls back to an expanded prefix list. This
  detects substantially more compound splits, including those a model
  produces from less common compound stems.

### Added
- `mttr_100` field on `TextMetrics` and `CorpusMetrics`, populated for every
  measurement.
- `--seeds 42,1337,2026` flag on `scripts/30_score.py` (issue #4). When the
  model output tree includes `data/outputs/<model_id>/seed_<N>/` subdirs,
  each seed is scored independently and the headline NORI score is reported
  as mean ± std across seeds. Submitters can opt in by providing multi-seed
  generations; legacy single-seed submissions continue to work unchanged.
- `--baseline-mapping configs/baseline_mapping.yaml` flag on
  `scripts/30_score.py` (issue #5). Maps prompt-id prefix to baseline source
  (wikipedia, gutenberg, or combined) so that each generation is scored
  against the matching register instead of the averaged distribution. The
  shipped example maps editorial/technical/argumentative prompts to the
  Wikipedia baseline and personal/narrative prompts to the Gutenberg
  baseline. Combined-baseline mode remains the default.
- `--human` flag on `scripts/30_score.py` (issue #3). Scores writers placed
  under `data/human_baseline{,_nn}/<author_id>/<prompt_id>.txt` against the
  same native distribution and writes `results/human_baseline{,_nn}.json`.
  Lets users anchor the leaderboard against a native ceiling. The shipped
  release does not include human-written outputs; the scoring path is ready
  for them.
- `tests/` directory with 14 unit tests covering the V2 declarative filter,
  the MTTR-100 metric, and the new vocabulary-backed compound detector.
  `make test` runs the suite without requiring pytest.

### Migration notes
- v1.0 leaderboard rows are deprecated. The README leaderboard has been
  re-scored against the v2.0 baseline. Comparing a v1.x score to a v2.0
  score is meaningless because three of the five axes use different
  measurements.
- The `mttr_1000` field is preserved for diagnostic purposes and continues
  to be populated, but it is no longer consulted by `score()`. External
  tooling that reads `mttr_1000` should migrate to `mttr_100`.

### Deferred (tracked, not in v2.0)
- Round-trip stability axis (issue #7), LLM-as-judge coherence column
  (issue #8), sampling-decode evaluation (issue #9). Tracked for v2.x.

## [1.0.0] - 2026-05-10

First stable release. Adds Nynorsk benchmark (**NORI-NN**) alongside the
Bokmaal benchmark (**NORI**), unified under a `--lang nb|nn` flag.

### Added (NORI v1.0)
- **NORI-NN**: Nynorsk variant of the benchmark. Same five-axis structure,
  with Nynorsk-specific lexicons for modal particles (jo, då, vel, nok,
  altså, sjølvsagt, ...), explicit connectives (av di, difor, dimed,
  soleis, ...), and subordinators (kva, kvifor, jamvel om, sidan, ...).
- Native Nynorsk reference baseline: 1,500 articles from Nynorsk Wikipedia
  (542k words, license CC-BY-SA-4.0).
- 25 standard Nynorsk prompts (`configs/prompts_nn.yaml`), translated from
  the Bokmaal set with care for register parity.
- `--lang nb|nn` flag on all scripts. Default is `nb` for backward
  compatibility with NORI v0.1.
- Separate output paths: `data/outputs/` for nb, `data/outputs_nn/` for nn.
- Separate scorecard files: `results/scorecard{,_nn}.{json,md}`.

### Changed
- `metrics.py` introduces a `LangPack` dataclass with `BOKMAAL` and
  `NYNORSK` instances. The structural metrics (em-dash, V2, compound
  integrity, sentence/word lengths, lexical diversity) remain
  language-agnostic and use the spaCy `nb_core_news_md` parser for both
  languages (no spaCy NN model exists; `nb` parses NN structure adequately
  for our root/constituent identification needs).
- Backwards-compatible aliases: old `MODAL_PARTICLES`, `EXPLICIT_CONNECTIVES`,
  `SUBORDINATORS` constants preserved as Bokmaal defaults.
  `NorskhetsScore` preserved as alias for `NoriScore`.

### NORI v1.0 baseline scorecards (Qwen 2.5 Instruct)

| | NORI (nb) | NORI-NN (nn) |
|---|---:|---:|
| qwen25-1_5b-instruct | 39.7 | 35.5 |
| qwen25-3b-instruct | 34.9 | 23.9 |

Both Qwen models score lower on NN than on NB. The 3B model drops by 11 points
(34.9 to 23.9), the 1.5B by 4 points (39.7 to 35.5). The 3B model's
NN modal-particle rate (0.15/1k) collapses against the native NN rate (2.79/1k),
indicating that the model fails to switch register away from BM defaults
even when prompted in NN.

### Known limitations carried over from v0.1
- V2-violation heuristic over-counts on imperatives, questions, fragments.
- No native-speaker calibration of axis tolerances yet.
- spaCy has no NN parser; we reuse the NB parser for NN structure.

## [0.1.0] - 2026-05-10

Initial public release. Bokmaal-only baseline with five axes and 25 prompts.

### Added
- Five-axis NORI scoring framework based on translation universals (Toury 1995,
  Baker 1996, Mauranen and Kujamaki 2004).
- Native Norwegian reference corpus: 1,500 Wikipedia articles plus five Project
  Gutenberg literary works (1.16M words total).
- Standard prompt set: 25 prompts across 5 registers (editorial, personal,
  technical, argumentative, letter).
- Reproducible pipeline (`make data | baseline | generate | score`).
- Initial leaderboard with Qwen 2.5 1.5B and 3B Instruct.
- Per-prompt and per-axis breakdowns in `results/scorecard.json`.
- Submission protocol via GitHub PR (see CONTRIBUTING.md).
- CI validation workflow that recomputes scores from submitted outputs.

### Known limitations (documented in README)
- V2-violation heuristic over-counts on imperatives, questions, fragments.
- Reference corpus has some translation drift in Wikipedia content.
- No native-speaker calibration of composite tolerances yet.
- Bokmaal only; nynorsk requires separate corpus.

## Planned for 0.2.0
- Filter V2-violation count to declarative main clauses only.
- Add a third reference subset of modern editorial Norwegian.
- Native-speaker calibration of axis tolerances (target n=200 judgments).
- Nynorsk variant (NORI-NN) with separate reference corpus.
