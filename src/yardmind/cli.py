from __future__ import annotations

import argparse
import json
from pathlib import Path

from yardmind.benchmark import run_benchmark, write_benchmark_summary
from yardmind.loader import InstanceFormatError, load_instance
from yardmind.official import (
    OfficialSupportError,
    load_official_solution,
    solve_official_constructive,
    solve_official_constructive_native,
    solve_official_search,
    validate_official_solution,
)
from yardmind.official_compare import generate_official_constructive_comparison
from yardmind.solver.constructive import ConstructiveSolver
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.local_search import LocalSearchSolver


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yardmind",
        description="YardMind command-line entrypoint.",
    )
    parser.add_argument(
        "instance",
        nargs="?",
        type=Path,
        help="Path to an OGC 2026 instance file.",
    )
    parser.add_argument(
        "--mode",
        choices=["inspect", "constructive", "search", "benchmark"],
        default="inspect",
        help="Run mode for the scaffold.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=8,
        help="Number of local-search iterations when --mode search is used.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for local-search decisions when --mode search is used.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of benchmark repetitions when --mode benchmark is used.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path when --mode benchmark is used.",
    )
    parser.add_argument(
        "--time-limit-seconds",
        type=float,
        help="Optional wall-clock time limit for search, benchmark, and official constructive runs.",
    )
    parser.add_argument(
        "--input-format",
        choices=["development", "official"],
        default="development",
        help="Instance schema to parse. Official mode is reserved for the competition schema.",
    )
    parser.add_argument(
        "--solution",
        type=Path,
        help="Optional solution JSON to validate during inspect mode for official input.",
    )
    parser.add_argument(
        "--official-constructive-variant",
        choices=["delegated", "native"],
        default="delegated",
        help="Constructive variant for official input when --mode constructive is used.",
    )
    return parser


def _print_solution_summary(label: str, placements_count: int, objective_value: float, is_feasible: bool) -> None:
    print(f"{label} placements={placements_count} objective={objective_value:.2f} feasible={is_feasible}")


def _print_objective_breakdown(area_utilization: float, lateness_penalty: float, retrieval_risk_penalty: float, congestion_penalty: float) -> None:
    print(
        "Objective breakdown "
        f"area_utilization={area_utilization:.4f} "
        f"lateness_penalty={lateness_penalty:.2f} "
        f"retrieval_risk_penalty={retrieval_risk_penalty:.2f} "
        f"congestion_penalty={congestion_penalty:.2f}"
    )


def _print_benchmark_summary(runs: int, constructive_mean: float, search_mean: float, search_best: float, improved_runs: int) -> None:
    print(
        "Benchmark summary "
        f"runs={runs} "
        f"constructive_mean={constructive_mean:.4f} "
        f"search_mean={search_mean:.4f} "
        f"search_best={search_best:.4f} "
        f"improved_runs={improved_runs}/{runs}"
    )


def _print_benchmark_run(seed: int, search_objective: float, delta: float, search_feasible: bool) -> None:
    print(
        "Benchmark run "
        f"seed={seed} "
        f"search_objective={search_objective:.4f} "
        f"delta={delta:.4f} "
        f"feasible={search_feasible}"
    )


def _print_operator_totals(kind: str, name: str, attempts: int, feasible_candidates: int, accepted_candidates: int, improved_candidates: int) -> None:
    print(
        "Operator totals "
        f"kind={kind} "
        f"name={name} "
        f"attempts={attempts} "
        f"feasible={feasible_candidates} "
        f"accepted={accepted_candidates} "
        f"improved={improved_candidates}"
    )


def _print_official_validation_summary(result: dict[str, object]) -> None:
    objective = result.get("objective")
    objective_text = "None" if objective is None else f"{float(objective):.4f}"
    print(
        "Official feasibility "
        f"feasible={result.get('feasible')} "
        f"stage={result.get('stage')} "
        f"objective={objective_text}"
    )


def _print_official_objective_breakdown(result: dict[str, object]) -> None:
    if not result.get("feasible"):
        return
    print(
        "Official objective breakdown "
        f"obj1={float(result['obj1']):.4f} "
        f"obj2={float(result['obj2']):.4f} "
        f"obj3={float(result['obj3']):.4f}"
    )


def _print_official_benchmark_summary(summary: dict[str, object]) -> None:
    delegated = summary["delegated_baseline"]
    native = summary["native_constructive"]
    delegated_objective = delegated["objective"]
    native_objective = native["objective"]
    delegated_text = "None" if delegated_objective is None else f"{float(delegated_objective):.4f}"
    native_text = "None" if native_objective is None else f"{float(native_objective):.4f}"
    objective_delta = None
    if delegated_objective is not None and native_objective is not None:
        objective_delta = float(native_objective) - float(delegated_objective)
    objective_delta_text = "None" if objective_delta is None else f"{objective_delta:.4f}"
    print(
        "Official benchmark "
        f"instance={summary['instance']} "
        f"delegated_objective={delegated_text} "
        f"native_objective={native_text} "
        f"objective_delta={objective_delta_text}"
    )
    print(
        "Official benchmark runtime "
        f"delegated_seconds={float(delegated['runtime_seconds']):.6f} "
        f"native_seconds={float(native['runtime_seconds']):.6f}"
    )
    print(
        "Official benchmark feasibility "
        f"delegated={delegated['feasible']}@stage{delegated['stage']} "
        f"native={native['feasible']}@stage{native['stage']}"
    )


def _count_official_assignments(solution: dict[str, object]) -> int:
    operations = solution.get("operations", {})
    if not isinstance(operations, dict):
        return 0
    return sum(
        1
        for ops_at_time in operations.values()
        if isinstance(ops_at_time, list)
        for operation in ops_at_time
        if isinstance(operation, dict) and operation.get("type") == "ENTRY"
    )


def _write_json_output(output_path: Path, payload: object) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.instance is None:
        parser.print_help()
        return 0

    if args.solution is not None and not (args.input_format == "official" and args.mode == "inspect"):
        print("INPUT ERROR: --solution is only supported with --input-format official --mode inspect.")
        return 2

    try:
        instance = load_instance(args.instance, input_format=args.input_format)
    except InstanceFormatError as exc:
        print(f"INPUT ERROR: {exc}")
        return 2

    if args.mode == "inspect":
        if instance.source_format == "official":
            print(
                f"Loaded official instance {instance.name} with {len(instance.blocks)} blocks "
                f"across {len(instance.bays)} bays."
            )
            if instance.weights:
                print(
                    "Official weights "
                    f"w1={instance.weights['w1']:.0f} "
                    f"w2={instance.weights['w2']:.0f} "
                    f"w3={instance.weights['w3']:.0f}"
                )
            if args.solution is not None:
                try:
                    solution = load_official_solution(args.solution)
                    result = validate_official_solution(instance.metadata["raw_problem"], solution)
                except OfficialSupportError as exc:
                    print(f"INPUT ERROR: {exc}")
                    return 2
                _print_official_validation_summary(result)
                _print_official_objective_breakdown(result)
                for violation in result.get("violations", []):
                    print(f"VIOLATION: {violation}")
        else:
            print(
                f"Loaded instance with {len(instance.blocks)} blocks on a yard "
                f"of size {instance.yard.width}x{instance.yard.height}."
            )
        return 0

    if instance.source_format == "official":
        if args.mode == "constructive":
            try:
                if args.official_constructive_variant == "native":
                    solution = solve_official_constructive_native(
                        instance.metadata["raw_problem"],
                        timelimit=args.time_limit_seconds or 60.0,
                    )
                else:
                    solution = solve_official_constructive(
                        instance.metadata["raw_problem"],
                        timelimit=args.time_limit_seconds or 60.0,
                    )
                result = validate_official_solution(instance.metadata["raw_problem"], solution)
            except OfficialSupportError as exc:
                print(f"INPUT ERROR: {exc}")
                return 2

            print(
                f"Official constructive solution variant={args.official_constructive_variant} "
                f"assignments={_count_official_assignments(solution)}"
            )
            if args.output is not None:
                _write_json_output(args.output, solution)
                print(f"Official solution written to {args.output}")
            _print_official_validation_summary(result)
            _print_official_objective_breakdown(result)
            for violation in result.get("violations", []):
                print(f"VIOLATION: {violation}")
            return 0 if result.get("feasible") else 1

        if args.mode == "search":
            try:
                solution = solve_official_search(
                    instance.metadata["raw_problem"],
                    timelimit=args.time_limit_seconds or 5.0,
                )
                result = validate_official_solution(instance.metadata["raw_problem"], solution)
            except OfficialSupportError as exc:
                print(f"INPUT ERROR: {exc}")
                return 2

            print(f"Official search solution assignments={_count_official_assignments(solution)}")
            if args.output is not None:
                _write_json_output(args.output, solution)
                print(f"Official solution written to {args.output}")
            _print_official_validation_summary(result)
            _print_official_objective_breakdown(result)
            for violation in result.get("violations", []):
                print(f"VIOLATION: {violation}")
            return 0 if result.get("feasible") else 1

        if args.mode == "benchmark":
            try:
                comparison_output_root = args.output.parent if args.output is not None else None
                summary = generate_official_constructive_comparison(
                    repo_root=Path(__file__).resolve().parents[2],
                    output_root=comparison_output_root,
                    instance_path=args.instance,
                    timelimit=args.time_limit_seconds or 5.0,
                )
            except OfficialSupportError as exc:
                print(f"INPUT ERROR: {exc}")
                return 2

            if args.output is not None:
                _write_json_output(args.output, summary)
                print(f"Official benchmark results written to {args.output}")
            _print_official_benchmark_summary(summary)
            return 0

        print("INPUT ERROR: Official input does not support this mode yet.")
        return 2

    checker = FeasibilityChecker(instance)

    if args.mode == "benchmark":
        summary = run_benchmark(
            instance=instance,
            runs=args.runs,
            iterations=args.iterations,
            start_seed=args.seed,
            time_limit_seconds=args.time_limit_seconds,
        )
        _print_benchmark_summary(
            runs=len(summary.runs),
            constructive_mean=summary.constructive_mean,
            search_mean=summary.search_mean,
            search_best=summary.search_best,
            improved_runs=summary.improved_runs,
        )
        for run in summary.runs:
            _print_benchmark_run(
                seed=run.seed,
                search_objective=run.search_objective,
                delta=run.delta,
                search_feasible=run.search_feasible,
            )
        for stats in summary.operator_totals:
            _print_operator_totals(
                kind="destroy",
                name=stats.name,
                attempts=stats.attempts,
                feasible_candidates=stats.feasible_candidates,
                accepted_candidates=stats.accepted_candidates,
                improved_candidates=stats.improved_candidates,
            )
        for stats in summary.repair_totals:
            _print_operator_totals(
                kind="repair",
                name=stats.name,
                attempts=stats.attempts,
                feasible_candidates=stats.feasible_candidates,
                accepted_candidates=stats.accepted_candidates,
                improved_candidates=stats.improved_candidates,
            )
        if args.output is not None:
            write_benchmark_summary(summary=summary, output_path=args.output)
            print(f"Benchmark results written to {args.output}")
        return 0

    if args.mode == "constructive":
        state = ConstructiveSolver(checker=checker).solve(instance)
        label = "Constructive solution"
    else:
        state = LocalSearchSolver(
            checker=checker,
            iterations=args.iterations,
            seed=args.seed,
            time_limit_seconds=args.time_limit_seconds,
        ).solve(instance)
        label = "Search solution"

    is_feasible, violations = checker.validate_solution(state.placements)

    _print_solution_summary(
        label=label,
        placements_count=len(state.placements),
        objective_value=state.objective_value,
        is_feasible=is_feasible,
    )
    _print_objective_breakdown(
        area_utilization=state.objective_breakdown.area_utilization,
        lateness_penalty=state.objective_breakdown.lateness_penalty,
        retrieval_risk_penalty=state.objective_breakdown.retrieval_risk_penalty,
        congestion_penalty=state.objective_breakdown.congestion_penalty,
    )
    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
