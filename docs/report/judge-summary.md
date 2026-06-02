# YardMind Judge Summary

## 1. What YardMind Claims

YardMind is a feasibility-first retrieval-aware solver for shipyard block placement. It is designed to avoid the common failure mode where a dense placement looks good initially but creates expensive downstream interference.

## 2. What To Look At First

If a judge wants the shortest technical path through the project, use these two surfaces:
- `?view=proof` for feasibility status, official objective terms, runtime, and replay
- `?view=equations` for the mathematical objective and term definitions

If the conversation turns to why the layout itself is credible, also open:
- `?view=organization` for the figure that now walks from ship arrival through constructive placement, search repair, final organized yard structure, and per-block impact signals
- `?view=judge` for the full-screen guided sequence that steps through organization, equations, proof, and a closing competition claim in presentation order
- `./scripts/open-react-demo.ps1 -View judge -AutoPlay -Kiosk` when you need the fastest local live-demo entrypoint
- `./scripts/open-judge-pack.ps1` when you want the judge kiosk route and the two key report documents opened together
- `./scripts/open-submission-rehearsal.ps1` when you want the full pre-demo refresh and launch flow in one command

## 3. Official Objective

The official competition objective is:

$$
\min J = w_1 Z_1 + w_2 Z_2 + w_3 Z_3
$$

where:
- $Z_1$ is tardiness
- $Z_2$ is weighted bay imbalance
- $Z_3$ is preference-loss against better bay assignments

## 4. Current Solver Story

The current repository provides:
- a stable constructive baseline
- a development search layer that improves denser instances
- an official constructive comparison path
- an official portfolio-style search path that returns feasible official solutions

## 5. Current Evidence

The strongest current evidence in the repository is:
- generated convergence data under `artifacts/report/realistic_default/`
- a repair-ablation comparison in `artifacts/report/repair_ablation_comparison.csv`
- repeated-run summary data from `artifacts/report/realistic_default/summary.json`
- repeated-run official search comparison data from `artifacts/report/official_default/summary.json`
- repeated-run hard-case official search evidence from `artifacts/report/official_search_proof/summary.json`
- repeated-run quality-case official search evidence from `artifacts/report/official_search_quality/summary.json`
- a compact official-case comparison table in `artifacts/report/official_search_case_summary.csv`
- a worked example artifact in `artifacts/report/presentation/realistic_seed1_worked_example.csv`
- the exported judge sequence screenshot in `artifacts/demo/hackathon-frontend-judge.png`
- the exported ship-allocation organization screenshot in `artifacts/demo/hackathon-frontend-organization.png`
- the live proof surface in the frontend

## 6. Why The Organization View Matters

The strongest presentation improvement is that the layout is no longer shown as a static after-the-fact picture. The organization view now shows a ship entering the system, a staged arrival-to-placement sequence, a block-by-block trace of what the search phase changed relative to the constructive baseline, and explicit local impact signals for access, conflict pressure, and core fit. The judge route now mirrors the intended speaking order, can auto-advance hands-free, and ends on a short why-we-win frame instead of stopping on raw metrics. In the proof step it now carries development repeated-run evidence, stable public-sample official evidence, a hard case where search recovers a feasible result after native constructive fails, and a quality case where search materially beats an already feasible native result.

## 7. Current Limits

The project is not finished in competition terms. The largest remaining gaps are:
- the development objective is still a proxy objective
- the official search path is still lighter than a full direct-improvement official neighborhood search
- larger official runtime and quality studies are still needed

## 8. One-Line Assessment

YardMind is already structured like a competition solver and now has a clear technical story, but the next decisive step is to strengthen the official-search layer and back it with broader official-format evidence.