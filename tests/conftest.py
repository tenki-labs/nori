"""Pytest configuration: put scripts/ on sys.path so tests can import metrics."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
