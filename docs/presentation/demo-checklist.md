# Demo Checklist

## Goal

Use this checklist immediately before and during the live YardMind demo so the presentation stays tight, reproducible, and resilient.

## Before The Demo

- confirm the repository is on the intended commit
- regenerate the demo snapshot if solver or frontend data changed
- verify the judge screenshot still matches the current UI
- keep the fallback screenshot ready in a separate window or tab

## Regenerate Assets

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
$env:PYTHONPATH = "src"
python -m yardmind.demo --instance examples/sample-instance.json --output artifacts/demo/index.html
npm --prefix web run build
```

## Open These In Advance

- main app: `http://localhost:5173`
- judge view: `http://localhost:5173/?view=judge`
- fallback screenshot: `artifacts/demo/hackathon-frontend-judge.png`
- speaking notes: `docs/presentation/demo-script.md`

## If You Need The Live Frontend

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
npm --prefix web run dev
```

## Live Flow

1. Start on the main control-room screen and state the problem: shipyard planning is a space-time problem, not just a packing problem.
2. Point to the top metrics and explain that YardMind exposes constructive quality, search improvement, and official comparison in one surface.
3. Compare the constructive baseline with the improved layout and emphasize retrieval-aware placement.
4. Scroll to the search trace and show that the optimizer is actively exploring and accepting moves.
5. Show the official delegated-versus-native constructive comparison as the bridge to the challenge path.
6. Switch to judge view for a cleaner summary and screenshot-ready close.

## What To Say In One Sentence Per Screen

- Hero: YardMind optimizes for future retrieval efficiency, not only immediate fit.
- Layouts: We compare the fast feasible baseline against the improved search incumbent.
- Search trace: The solver behavior is visible and interpretable instead of hidden in logs.
- Official section: We already support official-sample inspection, validation, and constructive benchmarking.
- Judge view: This is the condensed version we use for screenshots and judge scanning.

## Fallback Plan

- if the live frontend is slow, switch to the judge screenshot immediately
- if the local server is unavailable, use `artifacts/demo/index.html` plus the exported PNG
- if time is cut short, show only the hero metrics, layout comparison, and judge view

## Final 20-Second Close

YardMind treats the yard as a time-evolving operational system. We build feasible plans quickly, improve them under runtime limits, and make the whole optimization process visible enough for judges to evaluate and trust.
