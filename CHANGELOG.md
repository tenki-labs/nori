# NORI changelog

All notable changes to this benchmark are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
