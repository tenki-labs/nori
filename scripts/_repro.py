"""Reproducibility utilities for NorskhetsBench."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def seed_all(seed: int = 42) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def hash_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def env_fingerprint() -> dict[str, Any]:
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
    }
    libs = ["spacy", "scipy", "numpy", "transformers", "torch", "sacrebleu"]
    versions: dict[str, str | None] = {}
    for n in libs:
        try:
            mod = __import__(n)
            versions[n] = getattr(mod, "__version__", "?")
        except ImportError:
            versions[n] = None
    info["libraries"] = versions
    return info


def log_run(experiment_id: str, config: dict, inputs: list, results: dict,
            out_dir: Path | None = None) -> Path:
    out_dir = out_dir or (PROJECT_ROOT / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "experiment_id": experiment_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "input_hashes": {str(p): hash_file(p) for p in inputs if Path(p).exists()},
        "env": env_fingerprint(),
        "results": results,
    }
    out_path = out_dir / f"{experiment_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False, default=str)
    return out_path


def project_root() -> Path:
    return PROJECT_ROOT
