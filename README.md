# YardMind

YardMind is a research-first optimization project for OGC 2026, focused on retrieval-aware shipyard block packing and scheduling.

## Demo Highlights

- judge-friendly React control room for the development solver, search trace, and official constructive comparison
- screenshot-ready presentation mode at `http://localhost:5173/?view=judge`
- terminal-style solver walkthrough at `http://localhost:5173/?walkthrough=1` for live demos
- exported demo artifacts under `artifacts/demo/`, including hackathon-ready PNG captures

## Goal

Build an anytime hybrid optimizer that:
- finds a feasible yard plan quickly
- reduces future retrieval conflicts
- improves solutions with neighborhood search
- uses local exact repair for difficult subproblems

## Repository Layout

- `docs/` design, analysis, planning, and report assets
- `src/yardmind/` Python package for data loading, state modeling, and solver logic
- `tests/` smoke tests and future regression checks

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,opt]
python -m yardmind.cli --help
python -m yardmind.cli examples/sample-instance.json --mode inspect
python -m yardmind.cli examples/sample-instance.json --mode constructive
python -m yardmind.cli examples/sample-instance.json --mode search --iterations 6 --seed 11
python -m yardmind.cli examples/sample-instance.json --mode benchmark --runs 2 --iterations 6 --seed 3 --output artifacts/benchmark-sample.json
python scripts/generate_official_baseline_artifact.py
python -m yardmind.demo --instance examples/sample-instance.json --output artifacts/demo/index.html
pwsh -File scripts/open-demo.ps1
cd web
npm install
npm run dev
python scripts/compare_official_constructive_variants.py
pytest
pwsh -File scripts/validate-documented-workflow.ps1
python scripts/generate_chart_ready_artifacts.py
```

Search and benchmark modes also accept `--time-limit-seconds` for timeout-safe runs.
`python -m yardmind.demo` generates a browser-viewable static demo page so the project has a presentation layer in addition to the CLI, including the development solver view plus official delegated-versus-native constructive comparison metrics and official bay placement snapshots.
That same demo generation step now also writes `artifacts/demo/demo-data.json` and syncs `web/public/demo-data.json`, which is the live data source for the React presentation app under `web/`.
`pwsh -File scripts/open-demo.ps1` regenerates that demo artifact and opens it in the default browser; use `-NoOpen` when you only want to rebuild the HTML.
For the richer product UI, run `npm install` once in `web/`, then `npm run dev` to open the React control-room app backed by the latest generated demo snapshot.
The loader also accepts `--input-format`, which now supports the development schema plus official OGC 2026 instance inspection.
Official inspect mode also accepts `--solution` to validate a candidate operations JSON through the released baseline feasibility checker.
Official constructive mode can now run either the delegated released baseline or the first YardMind-native official heuristic, and can write the returned operations JSON through `--output`.
Official search mode now runs an initial official portfolio search by evaluating the released baseline constructive solver plus multiple YardMind-native constructive orderings, then refining the best native candidate with nearby order perturbations and targeted bay-bias perturbations before returning the best feasible objective found; it can also write the selected official operations JSON through `--output`.
Official benchmark mode now compares those two official constructive variants on an official instance and prints feasibility, objective, and runtime side by side; use `--output` to persist the comparison summary as JSON.
The native official heuristic now also scores urgency-weighted future bay scarcity and future window overlap, so when the current block has alternatives it preferentially preserves bays that later, tighter-slack blocks are more dependent on and avoids occupying those bays during the windows they are likely to need.
The comparison script also records runtime alongside feasibility and objective in `artifacts/official/comparison/summary.json`.

## React Presentation App

The repository now has two presentation surfaces:
- the static artifact in `artifacts/demo/index.html`
- the React app in `web/`, which consumes `web/public/demo-data.json`

Current screenshot artifacts:
- `artifacts/demo/hackathon-frontend.png`
- `artifacts/demo/hackathon-frontend-judge.png`
- `artifacts/demo/hackathon-frontend-walkthrough.png`

Recommended local flow:

```bash
python -m yardmind.demo --instance examples/sample-instance.json --output artifacts/demo/index.html
cd web
npm run dev
```

Use `npm run build` in `web/` to produce a production bundle after refreshing the demo snapshot.
Use `http://localhost:5173/?view=judge` for the tighter screenshot/export layout that trims the search table and emphasizes the product story above the fold.
Use `http://localhost:5173/?walkthrough=1` to open the terminal-style solver walkthrough dialog for live explanation of the solve pipeline.
To regenerate the PNG captures used for hackathon submission materials, run the frontend locally and capture either the default view or the judge view after refreshing the demo snapshot.

## Current Input Schema

The scaffold currently supports a simple JSON format for local development:

```json
{
	"yard": {
		"width": 12,
		"height": 10,
		"zones": ["north", "south"]
	},
	"blocks": [
		{
			"id": "B1",
			"width": 4,
			"height": 3,
			"release_time": 0,
			"due_time": 5,
			"priority": 2
		}
	]
}
```

This is a development schema for the scaffold. The repository now also supports loading official OGC 2026 JSON instances for inspection and validation against the released baseline feasibility checker.

Today, official search mode is available as a diversified portfolio over the current official constructive variants, but a true official neighborhood-search layer is still not implemented.

Official example commands:

```bash
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode inspect
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode inspect --solution examples/official-sample-solution.json
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode constructive --time-limit-seconds 5
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode constructive --official-constructive-variant native --time-limit-seconds 5
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode constructive --time-limit-seconds 5 --output artifacts/official-sample-solution.json
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode search --time-limit-seconds 5 --output artifacts/official-search-solution.json
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode benchmark --time-limit-seconds 5 --output artifacts/official-benchmark-summary.json
python scripts/generate_official_baseline_artifact.py
python scripts/compare_official_constructive_variants.py
```

## Initial Scope

This scaffold provides:
- project metadata
- a CLI entrypoint
- core domain models
- a retrieval-aware constructive baseline with simple candidate scoring
- organized technical documentation under `docs/`

## Next Build Targets

1. Implement the official instance parser.
2. Extend the feasibility checker with official contest constraints.
3. Improve the constructive baseline beyond row packing.
4. Add ALNS destroy and repair operators.
5. Add local CP-SAT repair for selected neighborhoods.

## Submission Notes

See `docs/handoff/submission-packaging-notes.md` for the current submission packaging checklist and reproducibility notes.
The repository also includes `scripts/validate-documented-workflow.ps1` to run the current documented validation workflow end to end.
For report and presentation charts, use `scripts/generate_chart_ready_artifacts.py` and the output map in `docs/report/chart-ready-artifacts.md`.
