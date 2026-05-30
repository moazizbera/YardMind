from __future__ import annotations

from collections.abc import Callable
import csv
from dataclasses import dataclass
import json
from pathlib import Path

from yardmind.models import Instance
from yardmind.solver.constructive import ConstructiveSolver
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.local_search import IterationRecord, LocalSearchSolver, OperatorStats


@dataclass(slots=True)
class BenchmarkRun:
    seed: int
    constructive_objective: float
    search_objective: float
    search_feasible: bool
    destroy_stats: list[OperatorStats]
    repair_stats: list[OperatorStats]
    history: list[IterationRecord]

    @property
    def delta(self) -> float:
        return self.search_objective - self.constructive_objective


@dataclass(slots=True)
class BenchmarkSummary:
    runs: list[BenchmarkRun]

    @property
    def constructive_mean(self) -> float:
        return sum(run.constructive_objective for run in self.runs) / max(1, len(self.runs))

    @property
    def search_mean(self) -> float:
        return sum(run.search_objective for run in self.runs) / max(1, len(self.runs))

    @property
    def search_best(self) -> float:
        return max((run.search_objective for run in self.runs), default=0.0)

    @property
    def improved_runs(self) -> int:
        return sum(1 for run in self.runs if run.delta > 0)

    @property
    def operator_totals(self) -> list[OperatorStats]:
        totals_by_name: dict[str, OperatorStats] = {}

        for run in self.runs:
            for stats in run.destroy_stats:
                total = totals_by_name.setdefault(stats.name, OperatorStats(name=stats.name))
                total.attempts += stats.attempts
                total.feasible_candidates += stats.feasible_candidates
                total.accepted_candidates += stats.accepted_candidates
                total.improved_candidates += stats.improved_candidates

        return [totals_by_name[name] for name in sorted(totals_by_name)]

    @property
    def repair_totals(self) -> list[OperatorStats]:
        totals_by_name: dict[str, OperatorStats] = {}

        for run in self.runs:
            for stats in run.repair_stats:
                total = totals_by_name.setdefault(stats.name, OperatorStats(name=stats.name))
                total.attempts += stats.attempts
                total.feasible_candidates += stats.feasible_candidates
                total.accepted_candidates += stats.accepted_candidates
                total.improved_candidates += stats.improved_candidates

        return [totals_by_name[name] for name in sorted(totals_by_name)]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": {
                "runs": len(self.runs),
                "constructive_mean": self.constructive_mean,
                "search_mean": self.search_mean,
                "search_best": self.search_best,
                "improved_runs": self.improved_runs,
            },
            "runs": [
                {
                    "seed": run.seed,
                    "constructive_objective": run.constructive_objective,
                    "search_objective": run.search_objective,
                    "delta": run.delta,
                    "search_feasible": run.search_feasible,
                    "destroy_stats": [_operator_stats_to_dict(stats) for stats in run.destroy_stats],
                    "repair_stats": [_operator_stats_to_dict(stats) for stats in run.repair_stats],
                    "history": [_iteration_record_to_dict(record) for record in run.history],
                }
                for run in self.runs
            ],
            "destroy_totals": [_operator_stats_to_dict(stats) for stats in self.operator_totals],
            "repair_totals": [_operator_stats_to_dict(stats) for stats in self.repair_totals],
        }


def run_benchmark(
    instance: Instance,
    runs: int,
    iterations: int,
    start_seed: int = 0,
    time_limit_seconds: float | None = None,
    solver_factory: Callable[[FeasibilityChecker, int], LocalSearchSolver] | None = None,
) -> BenchmarkSummary:
    run_count = max(1, runs)
    base_checker = FeasibilityChecker(instance)
    constructive_state = ConstructiveSolver(checker=base_checker).solve(instance)
    results: list[BenchmarkRun] = []

    for offset in range(run_count):
        seed = start_seed + offset
        checker = FeasibilityChecker(instance)
        if solver_factory is None:
            search_solver = LocalSearchSolver(
                checker=checker,
                iterations=iterations,
                seed=seed,
                time_limit_seconds=time_limit_seconds,
            )
        else:
            search_solver = solver_factory(checker, seed)
        search_state = search_solver.solve(instance)
        is_feasible, _ = checker.validate_solution(search_state.placements)
        results.append(
            BenchmarkRun(
                seed=seed,
                constructive_objective=constructive_state.objective_value,
                search_objective=search_state.objective_value,
                search_feasible=is_feasible,
                destroy_stats=[
                    OperatorStats(
                        name=stats.name,
                        attempts=stats.attempts,
                        feasible_candidates=stats.feasible_candidates,
                        accepted_candidates=stats.accepted_candidates,
                        improved_candidates=stats.improved_candidates,
                    )
                    for stats in search_solver.last_diagnostics.destroy_stats
                ],
                repair_stats=[
                    OperatorStats(
                        name=stats.name,
                        attempts=stats.attempts,
                        feasible_candidates=stats.feasible_candidates,
                        accepted_candidates=stats.accepted_candidates,
                        improved_candidates=stats.improved_candidates,
                    )
                    for stats in search_solver.last_diagnostics.repair_stats
                ],
                history=[
                    IterationRecord(
                        iteration=record.iteration,
                        destroy_operator=record.destroy_operator,
                        repair_operator=record.repair_operator,
                        candidate_feasible=record.candidate_feasible,
                        candidate_objective=record.candidate_objective,
                        incumbent_objective=record.incumbent_objective,
                        best_objective=record.best_objective,
                        accepted=record.accepted,
                        improved_best=record.improved_best,
                    )
                    for record in search_solver.last_diagnostics.history
                ],
            )
        )

    return BenchmarkSummary(runs=results)


def write_benchmark_summary(summary: BenchmarkSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")


def write_chart_artifacts(summary: BenchmarkSummary, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_dir / "summary.csv",
        ["runs", "constructive_mean", "search_mean", "search_best", "improved_runs"],
        [
            {
                "runs": len(summary.runs),
                "constructive_mean": summary.constructive_mean,
                "search_mean": summary.search_mean,
                "search_best": summary.search_best,
                "improved_runs": summary.improved_runs,
            }
        ],
    )
    _write_csv(
        output_dir / "runs.csv",
        ["seed", "constructive_objective", "search_objective", "delta", "search_feasible"],
        [
            {
                "seed": run.seed,
                "constructive_objective": run.constructive_objective,
                "search_objective": run.search_objective,
                "delta": run.delta,
                "search_feasible": run.search_feasible,
            }
            for run in summary.runs
        ],
    )
    _write_csv(
        output_dir / "convergence.csv",
        [
            "seed",
            "iteration",
            "destroy_operator",
            "repair_operator",
            "candidate_feasible",
            "candidate_objective",
            "incumbent_objective",
            "best_objective",
            "accepted",
            "improved_best",
        ],
        [
            {
                "seed": run.seed,
                "iteration": record.iteration,
                "destroy_operator": record.destroy_operator,
                "repair_operator": record.repair_operator,
                "candidate_feasible": record.candidate_feasible,
                "candidate_objective": record.candidate_objective,
                "incumbent_objective": record.incumbent_objective,
                "best_objective": record.best_objective,
                "accepted": record.accepted,
                "improved_best": record.improved_best,
            }
            for run in summary.runs
            for record in run.history
        ],
    )
    _write_csv(
        output_dir / "destroy_totals.csv",
        ["name", "attempts", "feasible_candidates", "accepted_candidates", "improved_candidates"],
        [_operator_stats_to_dict(stats) for stats in summary.operator_totals],
    )
    _write_csv(
        output_dir / "repair_totals.csv",
        ["name", "attempts", "feasible_candidates", "accepted_candidates", "improved_candidates"],
        [_operator_stats_to_dict(stats) for stats in summary.repair_totals],
    )


def _operator_stats_to_dict(stats: OperatorStats) -> dict[str, object]:
    return {
        "name": stats.name,
        "attempts": stats.attempts,
        "feasible_candidates": stats.feasible_candidates,
        "accepted_candidates": stats.accepted_candidates,
        "improved_candidates": stats.improved_candidates,
    }


def _iteration_record_to_dict(record: IterationRecord) -> dict[str, object]:
    return {
        "iteration": record.iteration,
        "destroy_operator": record.destroy_operator,
        "repair_operator": record.repair_operator,
        "candidate_feasible": record.candidate_feasible,
        "candidate_objective": record.candidate_objective,
        "incumbent_objective": record.incumbent_objective,
        "best_objective": record.best_objective,
        "accepted": record.accepted,
        "improved_best": record.improved_best,
    }


def _write_csv(output_path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)