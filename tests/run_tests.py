"""Standalone NORI test runner.

Discovers all test_*.py modules in this directory, imports them, and runs
every top-level function named test_*. Exits non-zero if any test fails.

Pytest-compatible (works with `python -m pytest tests/`) but does not require
pytest itself, to avoid the platform-specific version conflicts pytest 9.x
hits on some Python 3.13 builds.
"""
from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))


def main() -> int:
    tests_dir = ROOT / "tests"
    modules = sorted(
        p.stem for p in tests_dir.glob("test_*.py")
    )
    passed = failed = 0
    for mname in modules:
        mod = importlib.import_module(mname)
        fns = [
            getattr(mod, n) for n in dir(mod)
            if n.startswith("test_") and callable(getattr(mod, n))
        ]
        for fn in fns:
            try:
                fn()
                print(f"PASS  {mname}.{fn.__name__}")
                passed += 1
            except Exception as e:
                print(f"FAIL  {mname}.{fn.__name__}: {type(e).__name__}: {e}")
                traceback.print_exc()
                failed += 1
    print()
    print(f"Passed: {passed}, Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
