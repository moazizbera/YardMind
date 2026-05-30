from __future__ import annotations

import json
from pathlib import Path

from yardmind.loader import load_instance
from yardmind.official import solve_official_constructive, validate_official_solution


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    instance_path = repo_root / "examples" / "official-sample-instance.json"
    output_path = repo_root / "artifacts" / "official" / "official-sample-solution.json"

    instance = load_instance(instance_path, input_format="official")
    solution = solve_official_constructive(instance.metadata["raw_problem"], timelimit=5.0)
    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(solution, indent=2), encoding="utf-8")

    print(f"Wrote official constructive artifact to {output_path}")
    print(
        "Official baseline validation "
        f"feasible={result['feasible']} "
        f"stage={result['stage']} "
        f"objective={result['objective']}"
    )

    if not result["feasible"]:
        for violation in result["violations"]:
            print(f"VIOLATION: {violation}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()