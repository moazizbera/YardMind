from __future__ import annotations

import csv
from pathlib import Path
from time import perf_counter

from yardmind.benchmark import run_benchmark, write_benchmark_summary, write_chart_artifacts
from yardmind.loader import load_instance
from yardmind.solver.constructive import ConstructiveSolver
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.local_search import (
    BestOfTopRepairOperator,
    GreedyRepairOperator,
    LocalSearchSolver,
    SpreadRepairOperator,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_root = repo_root / "artifacts" / "report"
    realistic_instance = load_instance(repo_root / "examples" / "realistic-improvement-instance.json")

    default_summary, default_runtime = _timed_benchmark(
        instance=realistic_instance,
        runs=6,
        iterations=20,
        start_seed=0,
    )
    heuristic_summary, heuristic_runtime = _timed_benchmark(
        instance=realistic_instance,
        runs=6,
        iterations=20,
        start_seed=0,
        solver_factory=lambda checker, seed: LocalSearchSolver(
            checker=checker,
            iterations=20,
            seed=seed,
            repair_operators=[
                GreedyRepairOperator(checker=checker),
                BestOfTopRepairOperator(checker=checker),
                SpreadRepairOperator(checker=checker),
            ],
        ),
    )

    default_dir = artifacts_root / "realistic_default"
    heuristic_dir = artifacts_root / "realistic_heuristic_only"
    write_benchmark_summary(default_summary, default_dir / "summary.json")
    write_chart_artifacts(default_summary, default_dir)
    write_benchmark_summary(heuristic_summary, heuristic_dir / "summary.json")
    write_chart_artifacts(heuristic_summary, heuristic_dir)

    _write_ablation_csv(
        artifacts_root / "repair_ablation_comparison.csv",
        constructive_mean=default_summary.constructive_mean,
        heuristic_summary=heuristic_summary,
        heuristic_runtime=heuristic_runtime,
        default_summary=default_summary,
        default_runtime=default_runtime,
    )

    _write_presentation_artifacts(
        artifacts_root=artifacts_root,
        instance=realistic_instance,
        iterations=20,
        seed=1,
    )


def _timed_benchmark(**kwargs):
    started_at = perf_counter()
    summary = run_benchmark(**kwargs)
    return summary, perf_counter() - started_at


def _write_ablation_csv(
    output_path: Path,
    constructive_mean: float,
    heuristic_summary,
    heuristic_runtime: float,
    default_summary,
    default_runtime: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["variant", "search_mean", "search_best", "improved_runs", "runtime_seconds"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "variant": "constructive_baseline",
                "search_mean": constructive_mean,
                "search_best": constructive_mean,
                "improved_runs": 0,
                "runtime_seconds": "",
            }
        )
        writer.writerow(
            {
                "variant": "heuristic_only_repairs",
                "search_mean": heuristic_summary.search_mean,
                "search_best": heuristic_summary.search_best,
                "improved_runs": heuristic_summary.improved_runs,
                "runtime_seconds": heuristic_runtime,
            }
        )
        writer.writerow(
            {
                "variant": "bounded_exact_repairs",
                "search_mean": default_summary.search_mean,
                "search_best": default_summary.search_best,
                "improved_runs": default_summary.improved_runs,
                "runtime_seconds": default_runtime,
            }
        )


def _write_presentation_artifacts(
    artifacts_root: Path,
    instance,
    iterations: int,
    seed: int,
) -> None:
    presentation_dir = artifacts_root / "presentation"
    checker = FeasibilityChecker(instance)
    constructive = ConstructiveSolver(checker=checker).solve(instance)
    solver = LocalSearchSolver(checker=FeasibilityChecker(instance), iterations=iterations, seed=seed)
    search = solver.solve(instance)

    presentation_dir.mkdir(parents=True, exist_ok=True)

    with (presentation_dir / "realistic_seed1_convergence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["iteration", "best_objective", "destroy_operator", "repair_operator", "improved_best"],
        )
        writer.writeheader()
        for record in solver.last_diagnostics.history:
            writer.writerow(
                {
                    "iteration": record.iteration,
                    "best_objective": record.best_objective,
                    "destroy_operator": record.destroy_operator,
                    "repair_operator": record.repair_operator,
                    "improved_best": record.improved_best,
                }
            )

    with (presentation_dir / "realistic_seed1_worked_example.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["variant", "block_id", "x", "y", "objective", "congestion_penalty", "retrieval_risk_penalty"],
        )
        writer.writeheader()
        for variant, state in (("constructive", constructive), ("search", search)):
            for placement in state.placements:
                writer.writerow(
                    {
                        "variant": variant,
                        "block_id": placement.block_id,
                        "x": placement.x,
                        "y": placement.y,
                        "objective": state.objective_value,
                        "congestion_penalty": state.objective_breakdown.congestion_penalty,
                        "retrieval_risk_penalty": state.objective_breakdown.retrieval_risk_penalty,
                    }
                )


if __name__ == "__main__":
    main()