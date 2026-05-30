# Chart-Ready Artifacts

Use `python scripts/generate_chart_ready_artifacts.py` from the repository root to regenerate the current report and presentation data files.

## Generated Outputs

- `artifacts/report/realistic_default/summary.csv`
- `artifacts/report/realistic_default/runs.csv`
- `artifacts/report/realistic_default/convergence.csv`
- `artifacts/report/realistic_default/destroy_totals.csv`
- `artifacts/report/realistic_default/repair_totals.csv`
- `artifacts/report/realistic_default/summary.json`
- `artifacts/report/realistic_heuristic_only/summary.csv`
- `artifacts/report/realistic_heuristic_only/runs.csv`
- `artifacts/report/realistic_heuristic_only/convergence.csv`
- `artifacts/report/realistic_heuristic_only/destroy_totals.csv`
- `artifacts/report/realistic_heuristic_only/repair_totals.csv`
- `artifacts/report/realistic_heuristic_only/summary.json`
- `artifacts/report/repair_ablation_comparison.csv`
- `artifacts/report/presentation/realistic_seed1_convergence.csv`
- `artifacts/report/presentation/realistic_seed1_worked_example.csv`

## Intended Usage

- use `repair_ablation_comparison.csv` for the report ablation table and runtime bar chart
- use `realistic_default/convergence.csv` or `presentation/realistic_seed1_convergence.csv` for convergence charts
- use `realistic_default/destroy_totals.csv` and `realistic_default/repair_totals.csv` for operator-effectiveness tables
- use `presentation/realistic_seed1_worked_example.csv` to rebuild the dense baseline versus improved-layout slide visuals

All files are regenerated from the current benchmark pipeline and seeded solver configuration, so the charts remain reproducible as the code evolves.