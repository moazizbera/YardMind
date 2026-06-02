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
- `artifacts/report/official_default/summary.json`
- `artifacts/report/official_search_proof/summary.json`
- `artifacts/report/official_search_quality/summary.json`
- `artifacts/report/official_search_case_summary.csv`
- `artifacts/report/repair_ablation_comparison.csv`
- `artifacts/report/realistic_default/summary.json`
- `artifacts/report/presentation/realistic_seed1_convergence.csv`
- `artifacts/report/presentation/realistic_seed1_worked_example.csv`
- `artifacts/demo/hackathon-frontend-judge.png`
- `artifacts/demo/hackathon-frontend-organization.png`
- `artifacts/demo/hackathon-frontend-equations.png`
- `artifacts/demo/hackathon-frontend-proof.png`

## Intended Usage

- use `repair_ablation_comparison.csv` for the report ablation table and runtime bar chart
- use `realistic_default/summary.json` when you need one compact repeated-run evidence block for the judge route or report summary
- use `official_default/summary.json` when you need compact repeated official search-vs-native-vs-delegated evidence for the judge route or technical report
- use `official_search_proof/summary.json` when you need a stronger official-search-wins proof case instead of the easy public sample
- use `official_search_quality/summary.json` when you need a case where search beats a feasible native official result
- use `official_search_case_summary.csv` when you need one direct table comparing all official evidence cases in the report
- use `realistic_default/convergence.csv` or `presentation/realistic_seed1_convergence.csv` for convergence charts
- use `realistic_default/destroy_totals.csv` and `realistic_default/repair_totals.csv` for operator-effectiveness tables
- use `presentation/realistic_seed1_worked_example.csv` to rebuild the dense baseline versus improved-layout slide visuals
- use `artifacts/demo/hackathon-frontend-judge.png` when you need a single screenshot that sells the guided judging sequence and closing claim
- use `artifacts/demo/hackathon-frontend-organization.png` when you need a concrete ship-to-yard allocation figure with the organization story and impact-signal trace
- use `artifacts/demo/hackathon-frontend-equations.png` and `artifacts/demo/hackathon-frontend-proof.png` as report-ready screenshots of the math and proof surfaces

All files are regenerated from the current benchmark pipeline and seeded solver configuration, so the charts remain reproducible as the code evolves.

## Documentation Consumers

- `docs/report/technical-report.md` is the main full technical document
- `docs/report/judge-summary.md` is the short judge-facing companion
- `scripts/generate-report-pack.ps1` regenerates the current demo, chart artifacts, and React build in one command; add `-CaptureScreenshots` to include the PNG figure exports
- `scripts/open-react-demo.ps1 -View judge -AutoPlay -Kiosk` is the quickest local live-demo entrypoint for the fullscreen judge route
- `scripts/open-judge-pack.ps1` opens the judge summary, technical report, and judge kiosk route together for live presentation
- `scripts/open-submission-rehearsal.ps1` refreshes the report pack, regenerates screenshots, and then launches the judge presentation flow
- the frontend `?view=organization` route is the live ship-arrival and space-organization figure with the impact-signal allocation trace
- the frontend `?view=judge` route is the fastest live walkthrough for judges and can auto-advance through the presentation order
- the frontend `?view=equations` route is the live mathematical surface for the same objective definitions
- the frontend `?view=proof` route is the live proof surface for feasibility, objective terms, and replay