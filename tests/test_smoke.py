import sys
from pathlib import Path

from yardmind.cli import build_parser, main


def test_cli_parser_builds() -> None:
    parser = build_parser()
    assert parser.prog == "yardmind"


def test_constructive_cli_prints_objective_breakdown(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--mode",
            "constructive",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Objective breakdown" in captured.out
    assert "area_utilization=" in captured.out
    assert "retrieval_risk_penalty=" in captured.out


def test_search_cli_runs(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--mode",
            "search",
            "--iterations",
            "5",
            "--seed",
            "11",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Search solution" in captured.out
    assert "Objective breakdown" in captured.out


def test_search_cli_runs_with_time_limit(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--mode",
            "search",
            "--iterations",
            "5",
            "--seed",
            "11",
            "--time-limit-seconds",
            "0",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Search solution" in captured.out


def test_benchmark_cli_runs(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--mode",
            "benchmark",
            "--runs",
            "2",
            "--iterations",
            "4",
            "--seed",
            "3",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Benchmark summary" in captured.out
    assert "improved_runs=" in captured.out
    assert "Benchmark run seed=3" in captured.out
    assert "Operator totals kind=destroy" in captured.out
    assert "Operator totals kind=repair" in captured.out


def test_benchmark_cli_writes_json_output(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    output_path = tmp_path / "benchmark-results.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--mode",
            "benchmark",
            "--runs",
            "2",
            "--iterations",
            "4",
            "--seed",
            "3",
            "--output",
            str(output_path),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "Benchmark results written to" in captured.out


def test_benchmark_cli_runs_with_time_limit(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--mode",
            "benchmark",
            "--runs",
            "2",
            "--iterations",
            "4",
            "--seed",
            "3",
            "--time-limit-seconds",
            "0",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Benchmark summary" in captured.out


def test_cli_inspects_official_instance(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Loaded official instance official-sample-instance with 2 blocks across 2 bays." in captured.out
    assert "Official weights w1=10 w2=3 w3=1" in captured.out


def test_cli_validates_official_solution_during_inspect(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--solution",
            str(Path("examples/official-sample-solution.json")),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Official feasibility feasible=True stage=5 objective=0.0000" in captured.out
    assert "Official objective breakdown obj1=0.0000 obj2=0.0000 obj3=0.0000" in captured.out


def test_cli_runs_official_constructive(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--mode",
            "constructive",
            "--time-limit-seconds",
            "5",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Official constructive solution variant=delegated assignments=2" in captured.out
    assert "Official feasibility feasible=True stage=5 objective=0.0000" in captured.out


def test_cli_runs_native_official_constructive(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--mode",
            "constructive",
            "--official-constructive-variant",
            "native",
            "--time-limit-seconds",
            "5",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Official constructive solution variant=native assignments=2" in captured.out
    assert "Official feasibility feasible=True stage=5 objective=0.0000" in captured.out


def test_cli_writes_official_constructive_output(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    output_path = tmp_path / "official-constructive-solution.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--mode",
            "constructive",
            "--time-limit-seconds",
            "5",
            "--output",
            str(output_path),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "Official solution written to" in captured.out


def test_cli_runs_official_search(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--mode",
            "search",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Official search solution assignments=2" in captured.out
    assert "Official feasibility feasible=True stage=5 objective=0.0000" in captured.out


def test_cli_runs_official_benchmark(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--mode",
            "benchmark",
            "--time-limit-seconds",
            "5",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Official benchmark instance=official-sample-instance" in captured.out
    assert "Official benchmark runtime" in captured.out
    assert "Official benchmark feasibility delegated=True@stage5 native=True@stage5" in captured.out


def test_cli_writes_official_benchmark_output(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    output_path = tmp_path / "official-benchmark-summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/official-sample-instance.json")),
            "--input-format",
            "official",
            "--mode",
            "benchmark",
            "--time-limit-seconds",
            "5",
            "--output",
            str(output_path),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "Official benchmark results written to" in captured.out


def test_cli_rejects_solution_flag_for_development_input(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yardmind",
            str(Path("examples/sample-instance.json")),
            "--solution",
            str(Path("examples/official-sample-solution.json")),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--solution is only supported with --input-format official --mode inspect" in captured.out
