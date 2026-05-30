from pathlib import Path

from yardmind.demo import generate_demo_report


def test_generate_demo_report_writes_html(tmp_path: Path) -> None:
    output_path = tmp_path / "demo" / "index.html"

    result_path = generate_demo_report(
        Path("examples/sample-instance.json"),
        output_path,
        iterations=4,
        seed=3,
    )

    html_output = result_path.read_text(encoding="utf-8")
    assert result_path == output_path
    assert output_path.exists()
    assert "YardMind Presentation Layer" in html_output
    assert "Constructive Baseline" in html_output
    assert "Local Search Incumbent" in html_output
    assert "Official Constructive Comparison" in html_output
    assert "Delegated Baseline obj" in html_output
    assert "Native Constructive obj" in html_output
    assert "Bay 0" in html_output
    assert "Block 0" in html_output
    assert "Search Trace" in html_output
    assert "<svg" in html_output