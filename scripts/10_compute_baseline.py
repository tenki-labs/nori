"""Compute the native-Norwegian reference baseline.

Loads the reference corpus from data/reference/{wikipedia_no,gutenberg_no}.jsonl,
runs the metric library on each document, aggregates into corpus-level
statistics, and writes results/baseline_native.json.

This baseline is what every model output is compared against.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from _repro import seed_all, project_root, log_run  # noqa: E402
from metrics import measure_text, aggregate, _to_dict  # noqa: E402

ROOT = project_root()
REF_DIR = ROOT / "data" / "reference"


def load_documents(path: Path, max_chars_per_doc: int = 12000) -> list[str]:
    """Load and chunk corpus documents for measurement.

    Long Gutenberg novels are split into chunks of ≤max_chars_per_doc each so
    no single document dominates the corpus statistics.
    """
    docs: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            text = row.get("text", "").strip()
            if not text:
                continue
            for start in range(0, len(text), max_chars_per_doc):
                chunk = text[start:start + max_chars_per_doc]
                if len(chunk) >= 500:
                    docs.append(chunk)
    return docs


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("nb", "nn"), default="nb",
                    help="Language pack: 'nb' Bokmaal (default), 'nn' Nynorsk.")
    args = ap.parse_args()

    seed_all(42)
    print(f"Computing native-Norwegian baseline (lang={args.lang})\n")

    if args.lang == "nb":
        wiki_path = REF_DIR / "wikipedia_no.jsonl"
        gut_path = REF_DIR / "gutenberg_no.jsonl"
        wiki_label = "wikipedia_no"
        gut_label = "gutenberg_no"
        out_filename = "baseline_native.json"
        experiment_id = "baseline_native"
    else:
        wiki_path = REF_DIR / "wikipedia_nn.jsonl"
        gut_path = REF_DIR / "gutenberg_nn.jsonl"  # may not exist; that's OK
        wiki_label = "wikipedia_nn"
        gut_label = "gutenberg_nn"
        out_filename = "baseline_native_nn.json"
        experiment_id = "baseline_native_nn"

    wiki_docs = load_documents(wiki_path) if wiki_path.exists() else []
    gut_docs = load_documents(gut_path) if gut_path.exists() else []
    print(f"  loaded {len(wiki_docs)} wikipedia chunks, {len(gut_docs)} gutenberg chunks\n")

    sources: dict[str, list] = {
        wiki_label: wiki_docs,
        gut_label: gut_docs,
    }
    all_metrics = {"_combined": []}

    for src_label, docs in sources.items():
        print(f"  measuring {src_label} ({len(docs)} docs)...")
        if not docs:
            continue
        t0 = time.time()
        per_doc = []
        for i, text in enumerate(docs):
            try:
                m = measure_text(text, lang=args.lang)
                per_doc.append(m)
                all_metrics["_combined"].append(m)
            except Exception as e:
                print(f"    skip doc {i}: {type(e).__name__}: {e}")
            if (i + 1) % 200 == 0:
                print(f"    {i+1}/{len(docs)} ({time.time()-t0:.1f}s)")
        cm = aggregate(per_doc)
        all_metrics[src_label] = cm
        print(f"    aggregate: {cm.n_documents} docs, {cm.total_words:,} words, "
              f"em-dash/10k={cm.em_dash_per_10k_chars}, "
              f"V2-viol={cm.v2_violation_rate}, "
              f"sent-len={cm.mean_sentence_length}±{cm.std_sentence_length}")

    # Combined "all native sources" baseline
    combined = aggregate(all_metrics["_combined"])

    # Save the structured baseline (lang-specific path)
    out_path = ROOT / "results" / out_filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    serialised = {
        src: _to_dict(cm) for src, cm in all_metrics.items() if src != "_combined"
    }
    serialised["_combined"] = _to_dict(combined)
    # Also keep the sentence-length distribution for the combined baseline
    # (used for KL/Wasserstein in future work)
    serialised["_combined"]["sentence_length_distribution_sample"] = (
        combined.sentence_length_distribution[:5000]
    )

    log_run(
        experiment_id=experiment_id,
        config={"max_chars_per_doc": 12000, "min_chunk": 500, "seed": 42,
                "lang": args.lang},
        inputs=[wiki_path, gut_path],
        results=serialised,
    )
    # Also write a copy with the canonical filename so log_run's auto-timestamp
    # doesn't break consumers that expect baseline_native[_nn].json directly.
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"results": serialised, "config": {"lang": args.lang}}, f,
                  indent=2, ensure_ascii=False, default=str)

    # Summary print
    print("\n" + "=" * 70)
    print(f"{'metric':<32}{'wiki':>10}{'gutenberg':>14}{'combined':>14}")
    print("-" * 70)
    keys = [
        ("em_dash_per_10k_chars", "em-dash/10k chars"),
        ("v2_violation_rate", "V2 violation rate"),
        ("mean_sentence_length", "mean sentence len"),
        ("std_sentence_length", "std sentence len"),
        ("p90_sentence_length", "p90 sentence len"),
        ("mean_word_length", "mean word length"),
        ("type_token_ratio", "TTR"),
        ("mttr_1000", "MTTR-1000"),
        ("content_word_ratio", "content word ratio"),
        ("modal_particles_per_1k_words", "modal particles/1k"),
        ("connectives_per_1k_words", "connectives/1k"),
        ("compound_integrity_rate", "compound integrity"),
    ]
    wiki_cm = all_metrics.get(wiki_label)
    gut_cm = all_metrics.get(gut_label)
    for attr, label in keys:
        w = getattr(wiki_cm, attr, "n/a") if wiki_cm else "n/a"
        g = getattr(gut_cm, attr, "n/a") if gut_cm else "n/a"
        c = getattr(combined, attr)
        print(f"{label:<32}{w!s:>10}{g!s:>14}{c!s:>14}")
    print("=" * 70)
    print(f"\nBaseline saved: {out_path}")


if __name__ == "__main__":
    main()
