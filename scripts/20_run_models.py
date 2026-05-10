"""Generate Norwegian text from each benchmarked model on the standard prompt
set. Outputs are saved per language under data/outputs[_<lang>]/<model_id>/<prompt_id>.txt.

Then 30_score.py measures and scores them.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# UTF-8 console
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repro import seed_all, project_root  # noqa: E402

ROOT = project_root()

# Model panel: keep additive. Same structure as the BNCR study.
MODELS = [
    {"id": "qwen25-3b-instruct", "hf": "Qwen/Qwen2.5-3B-Instruct", "qlora": True},
    {"id": "qwen25-1_5b-instruct", "hf": "Qwen/Qwen2.5-1.5B-Instruct", "qlora": True},
]


def load_prompts(lang: str):
    import yaml
    fname = "prompts.yaml" if lang == "nb" else "prompts_nn.yaml"
    with open(ROOT / "configs" / fname, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["settings"], cfg["prompts"]


SYSTEM_PROMPTS = {
    "nb": ("Du er en dyktig norsk skribent. Svar på norsk bokmål. "
           "Skriv naturlig, idiomatisk norsk i hverdagsregister, ikke "
           "stiv oversettelses-norsk. Unngå tankestreker (—) og "
           "særskriving av sammensatte ord."),
    "nn": ("Du er ein dyktig norsk skribent. Svar på nynorsk. "
           "Skriv naturleg, idiomatisk nynorsk i kvardagsregister, ikkje "
           "stiv omsetjings-norsk. Unngå tankestrekar (—) og "
           "særskriving av samansette ord."),
}


def load_model(spec):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    qcfg = None
    if spec.get("qlora"):
        qcfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
    tok = AutoTokenizer.from_pretrained(spec["hf"], trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        spec["hf"],
        quantization_config=qcfg,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        trust_remote_code=True,
    )
    model.eval()
    return model, tok


def generate(model, tok, prompt: str, settings: dict, lang: str = "nb") -> str:
    import torch
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPTS[lang]},
        {"role": "user", "content": prompt},
    ]
    s = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    enc = tok(s, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=settings["decode"]["max_new_tokens"],
            do_sample=settings["decode"]["do_sample"],
            temperature=settings["decode"]["temperature"],
            top_p=settings["decode"]["top_p"],
            repetition_penalty=settings["decode"]["repetition_penalty"],
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    gen_ids = out[0, enc["input_ids"].shape[1]:]
    return tok.decode(gen_ids, skip_special_tokens=True).strip()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("nb", "nn"), default="nb",
                    help="Language pack: 'nb' Bokmaal (default), 'nn' Nynorsk.")
    args = ap.parse_args()

    seed_all(42)
    out_root = ROOT / "data" / ("outputs" if args.lang == "nb" else "outputs_nn")
    out_root.mkdir(parents=True, exist_ok=True)

    settings, prompts = load_prompts(args.lang)
    print(f"NORI ({args.lang}): {len(prompts)} prompts × {len(MODELS)} models = "
          f"{len(prompts) * len(MODELS)} generations\n")

    for spec in MODELS:
        out_dir = out_root / spec["id"]
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== Model: {spec['id']} ({spec['hf']}) ===")
        t0 = time.time()
        model, tok = load_model(spec)
        load_s = time.time() - t0

        meta = {
            "model_id": spec["id"], "hf": spec["hf"],
            "load_seconds": round(load_s, 1),
            "lang": args.lang,
            "settings": settings,
            "generations": [],
        }
        for i, p in enumerate(prompts):
            out_path = out_dir / f"{p['id']}.txt"
            if out_path.exists():
                print(f"  [{i+1}/{len(prompts)}] {p['id']}: cached")
                continue
            t1 = time.time()
            try:
                txt = generate(model, tok, p["text"], settings, lang=args.lang)
            except Exception as e:
                txt = f"[GENERATION ERROR: {type(e).__name__}: {e}]"
            elapsed = time.time() - t1
            out_path.write_text(txt, encoding="utf-8")
            meta["generations"].append({
                "prompt_id": p["id"], "register": p["register"],
                "elapsed_s": round(elapsed, 1), "n_chars": len(txt),
            })
            print(f"  [{i+1}/{len(prompts)}] {p['id']} ({p['register']}): "
                  f"{len(txt)} chars in {elapsed:.1f}s")

        meta_path = out_dir / "meta.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        print(f"  total: {time.time()-t0:.0f}s. Meta saved: {meta_path}")

        # Free GPU
        import gc, torch
        del model, tok
        gc.collect()
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
