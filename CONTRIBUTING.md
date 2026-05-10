# Contributing to NORI

Thank you for your interest in contributing. NORI welcomes three kinds of contributions:

1. New model submissions (add a model to the leaderboard).
2. Methodology improvements (better metrics, better baseline, calibration against human judgments).
3. Bug fixes and infrastructure (CI, packaging, documentation).

## Submitting a model to the leaderboard

There are two paths, depending on whether you want to share precomputed outputs or have the maintainers regenerate them.

### Path A: Submit precomputed outputs (recommended for closed or API-only models)

Use this path for proprietary models, API-only models, or any model where you cannot share weights but can share generations.

1. Fork this repository.
2. Run the model on the standard prompt set (`configs/prompts.yaml`). Save each output as plain UTF-8 text at `data/outputs/<your-model-id>/<prompt-id>.txt` where `<prompt-id>` matches the IDs in `configs/prompts.yaml` (e.g. `ed01.txt`, `pe03.txt`).
3. Write a `data/outputs/<your-model-id>/meta.json` describing the model and the generation settings:

```json
{
  "model_id": "your-model-id",
  "display_name": "Your Model 7B Instruct",
  "hf": "Org/Repo",
  "version": "v1.0",
  "vendor": "Your organization",
  "license": "model license",
  "decode": {
    "max_new_tokens": 512,
    "do_sample": false,
    "temperature": 0.0,
    "top_p": 1.0
  },
  "system_prompt": "Du er en dyktig norsk skribent. Svar på norsk bokmål.",
  "submitted_by": "your-github-handle",
  "submitted_at": "2026-05-10",
  "notes": "Any caveats about how the outputs were generated."
}
```

4. Run `make score` locally to generate the scorecard. This updates `results/scorecard.json` and `results/scorecard.md`.
5. Open a pull request titled `Submit: <model display name>`. Use the `model_submission.md` PR template.
6. The CI workflow validates the submission format and recomputes the scorecard from your outputs. If the scores you submitted match what CI computes, the PR is approved by a maintainer and merged.

### Path B: Add a model spec for in-house generation (recommended for open-weight models)

Use this path for openly-licensed Hugging Face models where the maintainers can regenerate outputs from scratch.

1. Fork this repository.
2. Edit `scripts/20_run_models.py` and add your model to the `MODELS` list:

```python
MODELS = [
    {"id": "qwen25-3b-instruct", "hf": "Qwen/Qwen2.5-3B-Instruct", "qlora": True},
    {"id": "your-model-id",      "hf": "Org/Repo",                  "qlora": True},
]
```

3. Open a PR titled `Add model: <Org/Repo>` describing the model. Include any non-standard requirements (custom chat template, special quantization, prompt formatting). The maintainers will regenerate outputs and update the leaderboard.

## Methodology contributions

Improvements to `scripts/metrics.py` are welcome. Important categories:

- **V2-violation heuristic improvements** (filter to declarative main clauses, handle yes/no questions and imperatives separately).
- **Saerskriving detector improvements** (broader compound-prefix list, integration with a Norwegian dictionary check).
- **Round-trip stability metric** (generate Norwegian, MT to English, MT back, measure semantic distance as a translatese signature).
- **Native-speaker calibration** (collect 100-200 native judgments on existing model outputs, tune the score tolerances against them).
- **Nynorsk extension** (separate reference corpus, separate composite tracker, share the metric implementation).

For methodology PRs, please include:

1. A description of the change and its motivation.
2. Before/after scores on the existing leaderboard models.
3. A brief discussion of how the change affects the baseline distribution (and whether the baseline needs to be recomputed).

## Bug reports and feature requests

Use the issue templates under `.github/ISSUE_TEMPLATE/`. Please include:

- The NORI version (commit hash or tag).
- The model and prompt that reproduces the issue (if relevant).
- Expected vs actual behavior.

## Code of conduct

Be civil and constructive. NORI is a research benchmark intended for collaborative improvement of Norwegian LLMs, not a competitive ranking tool. Critique of methodology is welcome. Personal attacks on contributors are not.

## License

By contributing to NORI you agree to license your contribution under the same terms as the project (MIT for code, CC-BY-4.0 for data and scorecards).
