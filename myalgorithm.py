from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from yardmind.official import solve_official_constructive_native, solve_official_search  # noqa: E402


def algorithm(prob_info: dict[str, Any], timelimit: float = 60.0) -> dict[str, Any]:
    """Official OGC 2026 submission entrypoint.

    The evaluator expects this exact function signature in a root-level
    myalgorithm.py. YardMind uses the native official search path when
    possible and falls back to the native constructive path if the search
    path raises an exception.
    """

    safe_timelimit = max(0.01, float(timelimit))

    try:
        return solve_official_search(prob_info, timelimit=safe_timelimit)
    except Exception:
        fallback_budget = max(0.01, safe_timelimit * 0.5)
        return solve_official_constructive_native(prob_info, timelimit=fallback_budget)