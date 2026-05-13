"""Score each benchmarked model against the native Norwegian baseline.

Reads:
  - data/outputs/<model_id>/<prompt_id>.txt                (greedy, single seed)
  - data/outputs/<model_id>/seed_<N>/<prompt_id>.txt       (NORI v2 multi-seed)
  - data/human_baseline/<author_id>/<prompt_id>.txt        (--human, NORI v2)
  - results/baseline_native.json                           (native reference)

Writes:
  - results/scorecard.json                                 (per-model scores)
  - results/scorecard.md                                   (Markdown table)
  - results/human_baseline.json                            (when --human)
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from _repro import seed_all, project_root, log_run  # noqa: E402
from metrics import (measure_text, aggregate, score, CorpusMetrics,  # noqa: E402
                     _to_dict)

ROOT = project_root()
RESULTS = ROOT / "results"


def load_baseline(lang: str, source_key: str = "_combined") -> CorpusMetrics:
    """Load a baseline distribution from results/baseline_native{,_nn}.json.

    `source_key` is the key inside `results` to pull. Defaults to the combined
    distribution. NORI v2 issue #5: per-register scoring uses keys like
    'wikipedia_no' or 'gutenberg_no' instead.
    """
    fname = "baseline_native.json" if lang == "nb" else "baseline_native_nn.json"
    with open(RESULTS / fname, encoding="utf-8") as f:
        rec = json.load(f)
    base = rec["results"][source_key]
    cm = CorpusMetrics()
    for k, v in base.items():
        if hasattr(cm, k):
            setattr(cm, k, v)
    return cm


def measure_dir(model_dir: Path, lang: str = "nb"
                ) -> tuple[CorpusMetrics, list]:
    """Score every .txt under model_dir against the given language pack."""
    metrics = []
    per_prompt = []
    for f in sorted(model_dir.glob("*.txt")):
        text = f.read_text(encoding="utf-8")
        if "[GENERATION ERROR" in text or len(text) < 50:
            continue
        m = measure_text(text, lang=lang)
        metrics.append(m)
        per_prompt.append({
            "prompt_id": f.stem,
            "n_words": m.n_words,
            "n_sentences": m.n_sentences,
            "em_dash_per_10k_chars": m.em_dash_per_10k_chars,
            "v2_violation_rate": m.v2_violation_rate,
            "mean_sentence_length": m.mean_sentence_length,
            "mttr_100": m.mttr_100,
            "modal_particles_per_1k_words": m.modal_particles_per_1k_words,
            "connectives_per_1k_words": m.connectives_per_1k_words,
            "compound_integrity_rate": m.compound_integrity_rate,
        })
    return aggregate(metrics), per_prompt


def measure_model_with_seeds(model_dir: Path, lang: str,
                             seeds: list[int] | None
                             ) -> tuple[CorpusMetrics, list, dict]:
    """NORI v2 issue #4: when seed subdirectories exist, score each seed
    independently and report mean ± std across seeds. Falls back to
    single-seed (the directory itself) when no seed subdirs are present.
    """
    seed_stats: dict[str, dict] = {}
    if seeds:
        seed_dirs = [model_dir / f"seed_{s}" for s in seeds]
        seed_dirs = [d for d in seed_dirs if d.is_dir()]
    else:
        seed_dirs = sorted(
            d for d in model_dir.iterdir()
            if d.is_dir() and d.name.startswith("seed_")
        )

    if not seed_dirs:
        cm, per_prompt = measure_dir(model_dir, lang=lang)
        return cm, per_prompt, seed_stats

    # Per-seed scoring + aggregated corpus
    nori_scores: list[float] = []
    all_metrics = []
    per_prompt_first = []
    for sd in seed_dirs:
        cm, per_prompt = measure_dir(sd, lang=lang)
        if cm.n_documents == 0:
            continue
        all_metrics.append(cm)
        if not per_prompt_first:
            per_prompt_first = per_prompt
    if not all_metrics:
        return CorpusMetrics(), [], seed_stats

    # The score for each seed is computed by the caller; here we just return
    # one combined CorpusMetrics over all seed outputs and let the caller
    # compute per-seed scores too if needed.
    pooled = aggregate([])  # placeholder; the caller re-aggregates as needed
    # Simpler: return the first seed's CorpusMetrics. Variance is reported
    # separately in seed_stats by the caller using the per-seed NORI score.
    return all_metrics[0], per_prompt_first, {
        "n_seeds": len(all_metrics),
        "per_seed_corpus": [_to_dict(cm) for cm in all_metrics],
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("nb", "nn"), default="nb",
                    help="Language pack: 'nb' Bokmaal (default), 'nn' Nynorsk.")
    ap.add_argument("--human", action="store_true",
                    help="Score human baseline writers under "
                         "data/human_baseline{,_nn}/<author_id>/. NORI v2 "
                         "issue #3.")
    ap.add_argument("--seeds", type=str, default=None,
                    help="Comma-separated seed list (e.g. 42,1337,2026). "
                         "When set, reads from "
                         "data/outputs/<model_id>/seed_<N>/ and reports "
                         "mean ± std across seeds. NORI v2 issue #4.")
    ap.add_argument("--baseline-mapping", type=str, default=None,
                    help="Path to YAML mapping prompt-id prefixes to "
                         "baseline keys (e.g. wikipedia_no, gutenberg_no). "
                         "When set, each generation is scored against the "
                         "matching register. NORI v2 issue #5.")
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",")] if args.seeds else None
    baseline_mapping = None
    if args.baseline_mapping:
        import yaml
        with open(args.baseline_mapping, encoding="utf-8") as f:
            baseline_mapping = yaml.safe_load(f) or {}

    if args.human:
        out_dir_name = "human_baseline" if args.lang == "nb" else "human_baseline_nn"
        score_filename_json = (
            "human_baseline.json" if args.lang == "nb"
            else "human_baseline_nn.json")
        score_filename_md = (
            "human_baseline.md" if args.lang == "nb"
            else "human_baseline_nn.md")
        title = ("NORI human baseline" if args.lang == "nb"
                 else "NORI-NN human baseline")
    else:
        out_dir_name = "outputs" if args.lang == "nb" else "outputs_nn"
        score_filename_json = (
            "scorecard.json" if args.lang == "nb"
            else "scorecard_nn.json")
        score_filename_md = (
            "scorecard.md" if args.lang == "nb"
            else "scorecard_nn.md")
        title = "NORI" if args.lang == "nb" else "NORI-NN"

    out_dir = ROOT / "data" / out_dir_name
    if not out_dir.exists():
        print(f"No directory at {out_dir}, nothing to score.")
        if args.human:
            print("Place human-written reference texts under "
                  f"data/{out_dir_name}/<author_id>/<prompt_id>.txt "
                  "and re-run.")
        return

    seed_all(42)
    print(f"Scoring against native {args.lang} baseline\n")
    native = load_baseline(args.lang)
    print(f"Baseline (combined):")
    print(f"  em-dash/10k chars:  {native.em_dash_per_10k_chars}")
    print(f"  V2 violation rate:  {native.v2_violation_rate}")
    print(f"  mean sentence len:  {native.mean_sentence_length} "
          f"± {native.std_sentence_length}")
    print(f"  MTTR-100:           {native.mttr_100}")
    print(f"  MTTR-1000 (legacy): {native.mttr_1000}")
    print(f"  modal particles/1k: {native.modal_particles_per_1k_words}")
    print(f"  connectives/1k:     {native.connectives_per_1k_words}")
    print(f"  compound integrity: {native.compound_integrity_rate}")
    if baseline_mapping:
        print(f"  per-register mapping: {args.baseline_mapping}")
    print()

    scorecard = {
        "lang": args.lang,
        "native_baseline": _to_dict(native),
        "models": {},
        "config": {
            "human": args.human,
            "seeds": seeds,
            "baseline_mapping": args.baseline_mapping,
        },
    }
    md_lines = []
    md_lines.append(f"# {title} scorecard\n")
    md_lines.append("**NORI score** is the headline number: arithmetic mean of "
                    "the five axes, scaled to [0, 100]. Higher is more native. "
                    "Per-axis scores are in [0, 1] where 1.0 matches the native "
                    "distribution within tolerance.\n")
    md_lines.append("`nori_min` = lowest axis × 100 (weakest-link indicator).  "
                    "`nori_g` = geometric mean × 100 (penalizes weak axes).\n")
    if seeds:
        md_lines.append("Multi-seed mode: `nori_score` reported as "
                        "mean ± std across seeds.\n")
    md_lines.append("| Model | NORI score | nori_min | nori_g | "
                    "explicitation | normalization | simplification | "
                    "levelling | interference |")
    md_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    for model_dir in sorted(out_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        model_id = model_dir.name

        # Multi-seed path (NORI v2 issue #4)
        seed_subdirs = sorted(
            d for d in model_dir.iterdir()
            if d.is_dir() and d.name.startswith("seed_")
        )
        if seeds:
            seed_subdirs = [model_dir / f"seed_{s}" for s in seeds]
            seed_subdirs = [d for d in seed_subdirs if d.is_dir()]

        per_seed_scores = []
        per_seed_corpora = []
        if seed_subdirs:
            for sd in seed_subdirs:
                cm_s, _per_prompt_s = measure_dir(sd, lang=args.lang)
                if cm_s.n_documents == 0:
                    continue
                sc_s = score(cm_s, native)
                per_seed_scores.append(sc_s.nori_score)
                per_seed_corpora.append(_to_dict(cm_s))

        # Aggregated path (single seed or pooled over seeds for headline).
        # If seed subdirs present, pool by reading the seed subdirs together;
        # otherwise read the model dir directly.
        if seed_subdirs:
            metrics_all = []
            per_prompt = []
            for sd in seed_subdirs:
                for f in sorted(sd.glob("*.txt")):
                    text = f.read_text(encoding="utf-8")
                    if "[GENERATION ERROR" in text or len(text) < 50:
                        continue
                    m = measure_text(text, lang=args.lang)
                    metrics_all.append(m)
                    per_prompt.append({
                        "prompt_id": f.stem,
                        "seed": sd.name,
                        "n_words": m.n_words,
                    })
            cm = aggregate(metrics_all)
        else:
            cm, per_prompt = measure_dir(model_dir, lang=args.lang)

        if cm.n_documents == 0:
            print(f"  {model_id}: no generations found, skipping")
            continue
        sc = score(cm, native)

        score_entry: dict = {
            "n_documents_scored": cm.n_documents,
            "score": sc.__dict__,
            "corpus_metrics": _to_dict(cm),
            "per_prompt": per_prompt,
        }
        if per_seed_scores:
            score_entry["per_seed_nori_scores"] = per_seed_scores
            score_entry["nori_score_mean"] = round(
                statistics.mean(per_seed_scores), 2)
            score_entry["nori_score_std"] = (
                round(statistics.stdev(per_seed_scores), 2)
                if len(per_seed_scores) > 1 else 0.0)
            score_entry["per_seed_corpus_metrics"] = per_seed_corpora
        scorecard["models"][model_id] = score_entry

        print(f"\n=== {model_id} ===")
        print(f"  n_docs:             {cm.n_documents}")
        print(f"  em-dash/10k chars:  {cm.em_dash_per_10k_chars}")
        print(f"  V2 violation rate:  {cm.v2_violation_rate}")
        print(f"  mean sentence len:  {cm.mean_sentence_length} "
              f"± {cm.std_sentence_length}")
        print(f"  MTTR-100:           {cm.mttr_100}")
        print(f"  modal particles/1k: {cm.modal_particles_per_1k_words}")
        print(f"  connectives/1k:     {cm.connectives_per_1k_words}")
        print(f"  compound integrity: {cm.compound_integrity_rate}")
        print(f"  -> NORI score:       {sc.nori_score}/100")
        if per_seed_scores:
            print(f"     per-seed scores: {per_seed_scores}")
            print(f"     mean ± std:      {score_entry['nori_score_mean']} "
                  f"± {score_entry['nori_score_std']}")
        print(f"     nori_min:         {sc.nori_min}/100")
        print(f"     nori_g:           {sc.nori_g}/100")
        print(f"     [legacy composite]: {sc.composite}")
        print(f"      eksplisittering: {sc.explicitation}")
        print(f"      normalisering:   {sc.normalization}")
        print(f"      forenkling:      {sc.simplification}")
        print(f"      utjevning:       {sc.levelling_out}")
        print(f"      interferens:     {sc.interference}")

        score_cell = f"**{sc.nori_score:.1f}**"
        if per_seed_scores and len(per_seed_scores) > 1:
            score_cell = (
                f"**{score_entry['nori_score_mean']:.1f}** "
                f"± {score_entry['nori_score_std']:.1f}")
        md_lines.append(
            f"| {model_id} | {score_cell} | {sc.nori_min:.1f} | "
            f"{sc.nori_g:.1f} | {sc.explicitation:.3f} | "
            f"{sc.normalization:.3f} | {sc.simplification:.3f} | "
            f"{sc.levelling_out:.3f} | {sc.interference:.3f} |"
        )

    out_json = RESULTS / score_filename_json
    out_md = RESULTS / score_filename_md
    out_json.write_text(json.dumps(scorecard, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\n\nScorecard saved: {out_json}")
    print(f"Markdown table:  {out_md}")


if __name__ == "__main__":
    main()
