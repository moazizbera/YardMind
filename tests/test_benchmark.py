from pathlib import Path

from yardmind.benchmark import run_benchmark, write_benchmark_summary, write_chart_artifacts
from yardmind.loader import load_instance
from yardmind.models import Block, Instance, Yard
from yardmind.solver.local_search import BestOfTopRepairOperator, GreedyRepairOperator, LocalSearchSolver, SpreadRepairOperator


def test_run_benchmark_uses_requested_seed_range() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))

    summary = run_benchmark(instance=instance, runs=3, iterations=4, start_seed=5)

    assert [run.seed for run in summary.runs] == [5, 6, 7]
    assert len(summary.runs) == 3
    assert all(len(run.history) == 4 for run in summary.runs)
    assert {stats.name for stats in summary.operator_totals} == {
        "congestion_cluster",
        "congestion_cluster_k3",
        "global_restart",
        "high_risk_cluster",
        "high_risk_cluster_k3",
    }
    assert {stats.name for stats in summary.repair_totals} == {"best_of_top", "bounded_exact", "sampled_greedy", "spread"}


def test_run_benchmark_reports_improvements_on_synthetic_case() -> None:
    instance = Instance(
        yard=Yard(width=8, height=5, min_clearance=0),
        blocks=[
            Block(block_id="A", width=2, height=2, release_time=0, due_time=3, priority=1),
            Block(block_id="B", width=2, height=2, release_time=0, due_time=4, priority=0),
            Block(block_id="C", width=3, height=2, release_time=0, due_time=5, priority=2),
            Block(block_id="D", width=2, height=2, release_time=0, due_time=6, priority=0),
        ],
    )

    summary = run_benchmark(instance=instance, runs=4, iterations=12, start_seed=7)

    assert summary.improved_runs >= 1
    assert summary.search_best >= summary.constructive_mean
    assert any(stats.improved_candidates >= 1 for stats in summary.operator_totals)
    assert any(stats.improved_candidates >= 1 for stats in summary.repair_totals)


def test_run_benchmark_reports_improvements_on_curated_instance_file() -> None:
    instance = load_instance(Path("examples/curated-improvement-instance.json"))

    summary = run_benchmark(instance=instance, runs=4, iterations=12, start_seed=7)

    assert summary.improved_runs >= 1
    assert summary.search_best > summary.constructive_mean


def test_run_benchmark_reports_improvements_on_realistic_instance_file() -> None:
    instance = load_instance(Path("examples/realistic-improvement-instance.json"))

    summary = run_benchmark(instance=instance, runs=6, iterations=20, start_seed=0)

    assert summary.improved_runs >= 1
    assert summary.search_best > summary.constructive_mean


def test_bounded_exact_repair_beats_heuristic_only_mix_on_realistic_case() -> None:
    instance = load_instance(Path("examples/realistic-improvement-instance.json"))

    def heuristic_only_solver_factory(checker, seed):
        return LocalSearchSolver(
            checker=checker,
            iterations=20,
            seed=seed,
            repair_operators=[
                GreedyRepairOperator(checker=checker),
                BestOfTopRepairOperator(checker=checker),
                SpreadRepairOperator(checker=checker),
            ],
        )

    with_exact = run_benchmark(instance=instance, runs=6, iterations=20, start_seed=0)
    heuristic_only = run_benchmark(
        instance=instance,
        runs=6,
        iterations=20,
        start_seed=0,
        solver_factory=heuristic_only_solver_factory,
    )

    assert with_exact.search_mean > heuristic_only.search_mean
    assert with_exact.improved_runs >= heuristic_only.improved_runs


def test_write_benchmark_summary_creates_json_artifact(tmp_path) -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    summary = run_benchmark(instance=instance, runs=2, iterations=4, start_seed=3)
    output_path = tmp_path / "benchmarks" / "summary.json"

    write_benchmark_summary(summary=summary, output_path=output_path)

    content = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert '"summary"' in content
    assert '"destroy_totals"' in content
    assert '"repair_totals"' in content
    assert '"history"' in content


def test_write_chart_artifacts_creates_chart_ready_csv_files(tmp_path) -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    summary = run_benchmark(instance=instance, runs=2, iterations=4, start_seed=3)
    output_dir = tmp_path / "charts"

    write_chart_artifacts(summary=summary, output_dir=output_dir)

    summary_csv = (output_dir / "summary.csv").read_text(encoding="utf-8")
    runs_csv = (output_dir / "runs.csv").read_text(encoding="utf-8")
    convergence_csv = (output_dir / "convergence.csv").read_text(encoding="utf-8")
    destroy_totals_csv = (output_dir / "destroy_totals.csv").read_text(encoding="utf-8")
    repair_totals_csv = (output_dir / "repair_totals.csv").read_text(encoding="utf-8")

    assert (output_dir / "summary.csv").exists()
    assert (output_dir / "runs.csv").exists()
    assert (output_dir / "convergence.csv").exists()
    assert (output_dir / "destroy_totals.csv").exists()
    assert (output_dir / "repair_totals.csv").exists()
    assert "constructive_mean" in summary_csv
    assert "search_objective" in runs_csv
    assert "destroy_operator" in convergence_csv
    assert "accepted_candidates" in destroy_totals_csv
    assert "improved_candidates" in repair_totals_csv


def test_run_benchmark_respects_zero_time_limit() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))

    summary = run_benchmark(instance=instance, runs=2, iterations=10, start_seed=3, time_limit_seconds=0.0)

    assert len(summary.runs) == 2
    assert all(run.history == [] for run in summary.runs)


def test_run_benchmark_is_reproducible_for_same_seed_range() -> None:
    instance = load_instance(Path("examples/curated-improvement-instance.json"))

    first = run_benchmark(instance=instance, runs=3, iterations=12, start_seed=7)
    second = run_benchmark(instance=instance, runs=3, iterations=12, start_seed=7)

    assert first.to_dict() == second.to_dict()