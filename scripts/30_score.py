"""Score each benchmarked model against the native Norwegian baseline.

Reads:
  - data/outputs/<model_id>/<prompt_id>.txt   (model generations)
  - results/baseline_native.json              (native reference distribution)

Writes:
  - results/scorecard.json                    (per-model scores + raw metrics)
  - results/scorecard.md                      (Markdown comparison table)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from _repro import seed_all, project_root, log_run  # noqa: E402
from metrics import (measure_text, aggregate, score, CorpusMetrics,  # noqa: E402
                     _to_dict)

ROOT = project_root()
OUT_DIR = ROOT / "data" / "outputs"
RESULTS = ROOT / "results"


def load_baseline() -> CorpusMetrics:
    with open(RESULTS / "baseline_native.json", encoding="utf-8") as f:
        rec = json.load(f)
    base = rec["results"]["_combined"]
    cm = CorpusMetrics()
    for k, v in base.items():
        if hasattr(cm, k):
            setattr(cm, k, v)
    return cm


def measure_model(model_dir: Path) -> tuple[CorpusMetrics, list]:
    metrics = []
    per_prompt = []
    for f in sorted(model_dir.glob("*.txt")):
        text = f.read_text(encoding="utf-8")
        if "[GENERATION ERROR" in text or len(text) < 50:
            continue
        m = measure_text(text)
        metrics.append(m)
        per_prompt.append({
            "prompt_id": f.stem,
            "n_words": m.n_words,
            "n_sentences": m.n_sentences,
            "em_dash_per_10k_chars": m.em_dash_per_10k_chars,
            "v2_violation_rate": m.v2_violation_rate,
            "mean_sentence_length": m.mean_sentence_length,
            "modal_particles_per_1k_words": m.modal_particles_per_1k_words,
            "connectives_per_1k_words": m.connectives_per_1k_words,
            "compound_integrity_rate": m.compound_integrity_rate,
        })
    return aggregate(metrics), per_prompt


def main():
    seed_all(42)
    print("Scoring models against native baseline\n")
    native = load_baseline()
    print(f"Baseline:")
    print(f"  em-dash/10k chars:  {native.em_dash_per_10k_chars}")
    print(f"  V2 violation rate:  {native.v2_violation_rate}")
    print(f"  mean sentence len:  {native.mean_sentence_length} ± {native.std_sentence_length}")
    print(f"  MTTR-1000:          {native.mttr_1000}")
    print(f"  modal particles/1k: {native.modal_particles_per_1k_words}")
    print(f"  connectives/1k:     {native.connectives_per_1k_words}")
    print(f"  compound integrity: {native.compound_integrity_rate}")
    print()

    scorecard = {"native_baseline": _to_dict(native), "models": {}}
    md_lines = []
    md_lines.append("# NorskhetsBench scorecard\n")
    md_lines.append("Higher per-axis score = closer to native Norwegian (1.0 = matches "
                    "native distribution within tolerance).\n")
    md_lines.append("| Model | composite | explicitation | normalization | "
                    "simplification | levelling | interference |")
    md_lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for model_dir in sorted(OUT_DIR.iterdir()):
        if not model_dir.is_dir():
            continue
        model_id = model_dir.name
        cm, per_prompt = measure_model(model_dir)
        if cm.n_documents == 0:
            print(f"  {model_id}: no generations found, skipping")
            continue
        sc = score(cm, native)
        scorecard["models"][model_id] = {
            "n_documents_scored": cm.n_documents,
            "score": sc.__dict__,
            "corpus_metrics": _to_dict(cm),
            "per_prompt": per_prompt,
        }
        print(f"\n=== {model_id} ===")
        print(f"  n_docs:             {cm.n_documents}")
        print(f"  em-dash/10k chars:  {cm.em_dash_per_10k_chars}")
        print(f"  V2 violation rate:  {cm.v2_violation_rate}")
        print(f"  mean sentence len:  {cm.mean_sentence_length} ± {cm.std_sentence_length}")
        print(f"  MTTR-1000:          {cm.mttr_1000}")
        print(f"  modal particles/1k: {cm.modal_particles_per_1k_words}")
        print(f"  connectives/1k:     {cm.connectives_per_1k_words}")
        print(f"  compound integrity: {cm.compound_integrity_rate}")
        print(f"  → composite score:  {sc.composite}")
        print(f"      eksplisittering: {sc.explicitation}")
        print(f"      normalisering:   {sc.normalization}")
        print(f"      forenkling:      {sc.simplification}")
        print(f"      utjevning:       {sc.levelling_out}")
        print(f"      interferens:     {sc.interference}")
        md_lines.append(f"| {model_id} | **{sc.composite}** | "
                        f"{sc.explicitation} | {sc.normalization} | "
                        f"{sc.simplification} | {sc.levelling_out} | "
                        f"{sc.interference} |")

    out_json = RESULTS / "scorecard.json"
    out_md = RESULTS / "scorecard.md"
    out_json.write_text(json.dumps(scorecard, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\n\nScorecard saved: {out_json}")
    print(f"Markdown table:  {out_md}")


if __name__ == "__main__":
    main()
