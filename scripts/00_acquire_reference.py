"""Acquire the native-Norwegian reference corpus for NORI.

Two sources, both openly licensed:

1. Norwegian Wikipedia (parquet, 2023-11-01 snapshot via wikimedia/wikipedia).
   We sample articles 1500 to 6000 chars long (avoiding stubs and very long
   technical articles) for a stable, varied baseline of editorially-edited
   modern Norwegian. License: CC-BY-SA-4.0.

2. Project Gutenberg Norwegian literature (a few classic novels). These are
   indisputably native Norwegian, predating any digital translation pipeline,
   and provide stylistic variety for the literary register. License: public
   domain.

Note on caveats (documented in the paper): Norwegian Wikipedia has some
articles that are translated from English. Translation drift is partially
mitigated by the editorial process Wikipedia articles go through, but is not
zero. The Gutenberg subset is unambiguously native but stylistically older
than modern editorial Norwegian. Future work could substitute the National
Library of Norway's bokhylla.no archive (more recent native literature) under
a research license.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from _repro import seed_all, hash_file, project_root  # noqa: E402

ROOT = project_root()
REF_DIR = ROOT / "data" / "reference"
REF_DIR.mkdir(parents=True, exist_ok=True)


def acquire_wikipedia(n_articles: int = 1500,
                      min_chars: int = 1500,
                      max_chars: int = 6000) -> dict:
    """Stream Norwegian Wikipedia (Bokmål); sample medium-length articles."""
    from datasets import load_dataset
    print(f"  streaming wikimedia/wikipedia 20231101.no, sampling up to {n_articles} articles...")
    ds = load_dataset("wikimedia/wikipedia", "20231101.no",
                      split="train", streaming=True)
    out_path = REF_DIR / "wikipedia_no.jsonl"
    n = 0
    seen = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for row in ds:
            seen += 1
            text = (row.get("text") or "").strip()
            if not (min_chars <= len(text) <= max_chars):
                continue
            f.write(json.dumps({
                "id": row.get("id"),
                "title": row.get("title"),
                "text": text,
                "source": "wikipedia_no",
            }, ensure_ascii=False) + "\n")
            n += 1
            if n % 200 == 0:
                print(f"    {n} articles selected (scanned {seen})")
            if n >= n_articles:
                break
    print(f"  wikipedia_no: {n} articles in length window {min_chars}-{max_chars}")
    return {
        "license": "CC-BY-SA-4.0",
        "source": "wikimedia/wikipedia 20231101.no",
        "config": {"min_chars": min_chars, "max_chars": max_chars,
                   "n_target": n_articles, "n_actual": n},
        "file": str(out_path.relative_to(ROOT)),
        "sha256": hash_file(out_path),
    }


# Project Gutenberg Norwegian: direct download of plain-text editions of
# canonical Norwegian works. Public domain.
GUTENBERG_TEXTS = [
    # (gutenberg_id, author, title, encoding)
    ("33012", "Bjornstjerne Bjornson",  "Synnove Solbakken", "iso-8859-1"),
    ("36205", "Knut Hamsun",            "Sult", "iso-8859-1"),
    ("28208", "Henrik Ibsen",           "Vildanden", "iso-8859-1"),
    ("31881", "Jonas Lie",              "Familjen paa Gilje", "iso-8859-1"),
    ("28036", "Alexander Kielland",     "Garman & Worse", "iso-8859-1"),
]


def acquire_gutenberg() -> dict:
    """Download a handful of canonical native-Norwegian literary texts."""
    out_path = REF_DIR / "gutenberg_no.jsonl"
    files: list[dict] = []
    n_total = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for gid, author, title, enc in GUTENBERG_TEXTS:
            for url_tpl in [
                f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
                f"https://www.gutenberg.org/files/{gid}/{gid}.txt",
                f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
            ]:
                try:
                    req = urllib.request.Request(
                        url_tpl, headers={"User-Agent": "norskhets-bench/0.1"})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        data = r.read()
                    text = data.decode(enc, errors="replace")
                    # Strip Gutenberg header/footer
                    start = text.find("*** START OF")
                    end = text.find("*** END OF")
                    if start >= 0:
                        text = text[text.find("\n", start) + 1:]
                    if end >= 0:
                        text = text[: text.rfind("\n", 0, end)]
                    text = text.strip()
                    f.write(json.dumps({
                        "id": f"gutenberg_{gid}",
                        "title": title,
                        "author": author,
                        "text": text,
                        "source": "gutenberg",
                    }, ensure_ascii=False) + "\n")
                    files.append({"gid": gid, "author": author, "title": title,
                                  "url": url_tpl, "chars": len(text)})
                    n_total += 1
                    print(f"  gutenberg {gid} {author}: {len(text):,} chars")
                    break
                except Exception as e:
                    continue
            else:
                print(f"  gutenberg {gid} {author}: failed all URL candidates")
    return {
        "license": "Public domain",
        "source": "Project Gutenberg",
        "files": files,
        "output": str(out_path.relative_to(ROOT)),
        "sha256": hash_file(out_path) if out_path.exists() else None,
        "n_works": n_total,
    }


def main():
    seed_all(42)
    print("NorskhetsBench reference-corpus acquisition\n")
    print("[1] Norwegian Wikipedia (modern editorial baseline)")
    wiki = acquire_wikipedia(n_articles=1500)
    print()
    print("[2] Project Gutenberg Norwegian (literary baseline)")
    gut = acquire_gutenberg()
    print()
    manifest = {"wikipedia_no": wiki, "gutenberg_no": gut}
    with open(REF_DIR / "MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest written: {REF_DIR / 'MANIFEST.json'}")


if __name__ == "__main__":
    main()
