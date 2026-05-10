# NORI changelog

All notable changes to this benchmark are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-10

Initial public release.

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
