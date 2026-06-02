# YardMind

YardMind is a research-first optimization project for OGC 2026, focused on retrieval-aware shipyard block packing and scheduling.

## Demo Highlights

- judge-friendly React control room for the development solver, search trace, and official constructive comparison
- screenshot-ready presentation mode via `./scripts/open-react-demo.ps1 -View judge`
- solve-story capture mode via `./scripts/open-react-demo.ps1 -View story`
- terminal-style solver walkthrough via `./scripts/open-react-demo.ps1 -View walkthrough`
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
python -m yardmind.demo --instance examples/realistic-improvement-instance.json --output artifacts/demo/index.html
./scripts/open-demo.ps1
./scripts/open-react-demo.ps1
./scripts/capture-react-demo.ps1
cd web
npm install
npm run dev -- --host=127.0.0.1 --port=5173
python scripts/compare_official_constructive_variants.py
pytest
./scripts/validate-documented-workflow.ps1
python scripts/generate_chart_ready_artifacts.py
```

Search and benchmark modes also accept `--time-limit-seconds` for timeout-safe runs.
`python -m yardmind.demo` generates a browser-viewable static demo page so the project has a presentation layer in addition to the CLI, including the development solver view plus official delegated-versus-native constructive comparison metrics and official bay placement snapshots. The default demo now uses `examples/realistic-improvement-instance.json` for the development yard and `examples/official-search-quality-instance.json` for the official comparison so the landing view opens on a stronger presentation case.
That same demo generation step now also writes `artifacts/demo/demo-data.json` and syncs `web/public/demo-data.json`, which is the live data source for the React presentation app under `web/`.
`./scripts/open-demo.ps1` regenerates that demo artifact and opens it in the default browser; use `-NoOpen` when you only want to rebuild the HTML.
For the richer product UI, use `./scripts/open-react-demo.ps1` from the repo root. It starts the React dev server in a separate PowerShell window, auto-selects the next free local port when `5173` is occupied, prints the exact URL, and opens the browser automatically. Add `-Intro` when you want the animated splash to play first before opening the selected view, including direct routes such as `-View judge` or `-View replay-stage`. You can also run `npm install` once in `web/` and then `npm run dev -- --host=127.0.0.1 --port=5173`. On this Windows/npm path, Vite is more reliable with `--host=` and `--port=` argument forwarding than the spaced form.
The loader also accepts `--input-format`, which now supports the development schema plus official OGC 2026 instance inspection.
Official inspect mode also accepts `--solution` to validate a candidate operations JSON through the released baseline feasibility checker.
Official constructive mode can now run either the delegated released baseline or the first YardMind-native official heuristic, and can write the returned operations JSON through `--output`.
Official search mode now runs an official portfolio plus incumbent-refinement loop: it evaluates the released baseline constructive solver plus multiple YardMind-native constructive orderings, then repeatedly rebuilds perturbation neighborhoods around the current best feasible incumbent using nearby order changes, bay-bias shifts, neighbor-aware incumbent repair, objective-driven rebuilds, reinsertion candidates, and partial reconstruction before returning the best feasible objective found; it can also write the selected official operations JSON through `--output`.
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
- `artifacts/demo/hackathon-frontend-story.png`
- `artifacts/demo/hackathon-frontend-walkthrough.png`

Recommended local flow:

```bash
python -m yardmind.demo --instance examples/realistic-improvement-instance.json --output artifacts/demo/index.html
cd web
npm run dev -- --host=127.0.0.1 --port=5173
```

Use `npm run build` in `web/` to produce a production bundle after refreshing the demo snapshot.
Use `./scripts/open-react-demo.ps1 -View judge` for the screenshot-oriented layout, `./scripts/open-react-demo.ps1 -View story` for the solve-story flow, and `./scripts/open-react-demo.ps1 -View walkthrough` to jump straight into the terminal walkthrough view. Add `-Intro` when you want the splash to play before the selected surface, and add `-Foreground` when you want the Vite logs in the current terminal instead of a separate PowerShell window.
Use `./scripts/capture-react-demo.ps1` to regenerate the demo snapshot and export the default, judge, story, and walkthrough PNG artifacts in one command. The first run installs the Playwright Chromium browser used for headless capture.
If you start the frontend manually, append `?view=judge`, `?view=story`, or `?walkthrough=1` to whatever local URL Vite prints.
The judge view trims the search table and emphasizes the product story above the fold.
The story view opens the walkthrough automatically over a simplified background.
The walkthrough view opens the terminal-style solver dialog for live explanation of the solve pipeline.
The walkthrough now supports autoplay plus manual `Next line`, `Pause/Resume`, and `Replay` controls for live judging.
To regenerate the PNG captures used for hackathon submission materials, run `./scripts/capture-react-demo.ps1` after refreshing the demo snapshot.

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

Today, official search mode includes a bounded incumbent-refinement loop over the current official constructive variants and perturbation families, including neighbor-aware incumbent repair around overlap and bay-pressure interactions, but it still stops short of a true direct assignment destroy/repair neighborhood search over incumbent official solutions.

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
The repository also includes `./scripts/validate-documented-workflow.ps1` to run the current documented validation workflow end to end.
For report and presentation charts, use `scripts/generate_chart_ready_artifacts.py` and the output map in `docs/report/chart-ready-artifacts.md`.
