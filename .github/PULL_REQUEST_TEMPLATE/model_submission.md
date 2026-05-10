<!-- Use this template when submitting a new model to the NORI leaderboard. -->

## Model submission

**Model display name:**
**Hugging Face / origin URL:**
**Vendor / authors:**
**License:**
**Model size (parameters):**

## Submission path

- [ ] Path A: I am attaching precomputed outputs in `data/outputs/<model-id>/*.txt` plus `meta.json`. The CI workflow will validate format and recompute scores.
- [ ] Path B: I am adding the model spec to `MODELS` in `scripts/20_run_models.py`. The maintainers will regenerate outputs.

## Generation settings

| Setting | Value |
|---|---|
| max_new_tokens | |
| temperature | |
| top_p | |
| do_sample | |
| repetition_penalty | |
| system prompt | |

## Self-reported NORI scores (Path A only)

If you computed scores locally, paste the relevant rows from `scorecard.md` here:

| Model | composite | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|
|       |     |     |     |     |     |     |

## Notes

Anything the reviewers should know about how the outputs were generated, any
deviations from the standard prompt protocol, known caveats, etc.

## Checklist

- [ ] I have read CONTRIBUTING.md.
- [ ] All 25 prompts have a corresponding `<prompt-id>.txt` output (Path A only).
- [ ] `meta.json` is present and follows the schema in CONTRIBUTING.md (Path A only).
- [ ] I have run `make score` locally and the leaderboard table updates as expected.
- [ ] My contribution is licensed under MIT (code) / CC-BY-4.0 (data) per the project license.
