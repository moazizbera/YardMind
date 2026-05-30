from pathlib import Path
from yardmind.official_compare import generate_official_constructive_comparison


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = repo_root / "artifacts" / "official" / "comparison"
    summary = generate_official_constructive_comparison(repo_root, output_root=output_root)

    print(f"Wrote official comparison artifacts to {output_root}")
    print(
        "Delegated baseline "
        f"runtime_seconds={float(summary['delegated_baseline']['runtime_seconds']):.6f} "
        f"feasible={summary['delegated_baseline']['feasible']} "
        f"stage={summary['delegated_baseline']['stage']} "
        f"objective={summary['delegated_baseline']['objective']}"
    )
    print(
        "Native constructive "
        f"runtime_seconds={float(summary['native_constructive']['runtime_seconds']):.6f} "
        f"feasible={summary['native_constructive']['feasible']} "
        f"stage={summary['native_constructive']['stage']} "
        f"objective={summary['native_constructive']['objective']}"
    )

    if not summary["delegated_baseline"]["feasible"] or not summary["native_constructive"]["feasible"]:
        raise SystemExit(1)
if __name__ == "__main__":
    main()