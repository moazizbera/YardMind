# YardMind Technical Report

## 1. Executive Summary

YardMind is a retrieval-aware optimization system for the OGC 2026 shipyard block placement problem. The central engineering claim is simple: a block placement is only useful if it is both feasible now and operationally reasonable later. A dense layout that creates future congestion, workload imbalance, or retrieval friction is not competitive enough.

The repository currently supports two coordinated solver views:
- a development path used to iterate quickly on spatial-temporal search behavior
- an official OGC 2026 path that loads official instances, constructs official operations, validates them, and exposes the official objective in a judge-facing frontend

The project is built around three design goals:
- feasibility first
- reproducible improvement under fixed seeds and bounded runtime
- explainability through objective decomposition, replay, and proof surfaces

## 2. Problem Statement

### 2.1 Operational Interpretation

The shipyard block placement problem is a coupled space-time optimization problem. Each block occupies physical area over a time interval and must later leave without violating yard geometry or temporal consistency. The optimization therefore combines:
- spatial containment
- temporal occupancy
- retrieval awareness
- distribution of work across bays

### 2.2 Official OGC 2026 Objective

For the official competition path, YardMind follows the released weighted objective:

$$
\min J = w_1 Z_1 + w_2 Z_2 + w_3 Z_3
$$

where:

$$
Z_1 = \sum_i T_i
$$

$$
Z_2 = \max_{j_1 \neq j_2} \left|u_{j_1}\sum_{i \in N(j_1)} L_i - u_{j_2}\sum_{i \in N(j_2)} L_i\right|
$$

$$
Z_3 = \sum_{j \in M} \sum_{i \in N(j)} \left(S_i^{\max} - S_{ij}\right)
$$

Interpretation:
- $Z_1$ measures tardiness
- $Z_2$ measures weighted imbalance between bays
- $Z_3$ measures the loss from moving blocks away from preferred bays
- $w_1$, $w_2$, and $w_3$ are instance-specific weights provided by the official input

### 2.3 Development Objective

The internal development solver still uses a proxy score to guide rapid iteration:

$$
\mathrm{Score} = U_{\mathrm{area}} - P_{\mathrm{late}} - P_{\mathrm{risk}} - P_{\mathrm{congestion}}
$$

This is intentionally not presented as the final competition metric. It is a development-time shaping objective that rewards dense usage while penalizing lateness, retrieval risk, and congestion.

## 3. Methodology

### 3.1 Constructive Baseline

The constructive solver builds the first feasible incumbent by enumerating admissible placements, filtering infeasible candidates, and ranking the remaining placements by urgency, compactness, local congestion, and retrieval-aware proxies.

This layer serves three roles:
- it guarantees a safe fallback solution
- it provides a baseline for comparison
- it defines the candidate-ranking prior reused by repair logic

### 3.2 Development Search

The development search uses a seeded destroy-and-repair loop. High-risk or congested neighborhoods are removed, then rebuilt using heuristic reinsertion or bounded exact repair.

Key engineering choices:
- best-so-far feasible solution is stored separately from the incumbent
- seeded execution preserves reproducibility
- acceptance compares the objective breakdown instead of only the scalar total

### 3.3 Official Search Path

The official path currently supports:
- delegated baseline constructive solving
- YardMind-native official constructive solving
- a portfolio-style official search that evaluates multiple constructive candidates and nearby perturbations, then returns the best feasible official solution found within the time limit

This is a competition-compatible official path, but it is not yet a full direct-improvement neighborhood search over official assignments.

## 4. System Architecture

The implementation is organized into focused layers:
- loader and domain models
- feasibility and validation
- constructive heuristics and scoring
- search state and operators
- official-format support and evaluator compatibility
- CLI, demo generation, and presentation outputs

Important code surfaces:
- `src/yardmind/loader.py`
- `src/yardmind/models.py`
- `src/yardmind/solver/constructive.py`
- `src/yardmind/solver/feasibility.py`
- `src/yardmind/solver/scoring.py`
- `src/yardmind/official.py`
- `myalgorithm.py`

## 5. Validation And Reproducibility

The repository validates both solver behavior and official compatibility.

Current validated surfaces include:
- loader and feasibility tests
- smoke tests
- official constructive validation
- official search validation
- submission entrypoint compatibility through `myalgorithm.py`

The official path now degrades more safely when delegated helper assets are unavailable because the native constructive path can act as the fallback.

Reproducibility surfaces also include generated benchmark and report artifacts under `artifacts/report/` and end-to-end documentation validation via `scripts/validate-documented-workflow.ps1`.

## 6. Results Summary

Current validated conclusions are:
- the constructive baseline is stable and feasible
- the development search improves over constructive on denser development cases
- official constructive and official search paths produce feasible official solutions on checked samples
- the frontend now presents official objective terms, proof view, and replay in a judge-facing format

The strongest current development-side evidence is backed by the generated report artifacts:
- `artifacts/report/repair_ablation_comparison.csv`
- `artifacts/report/realistic_default/summary.csv`
- `artifacts/report/realistic_default/convergence.csv`
- `artifacts/report/official_default/summary.json`
- `artifacts/report/official_search_proof/summary.json`
- `artifacts/report/official_search_quality/summary.json`
- `artifacts/report/official_search_case_summary.csv`
- `artifacts/report/presentation/realistic_seed1_convergence.csv`
- `artifacts/report/presentation/realistic_seed1_worked_example.csv`

### 6.1 Evaluation Table

| Surface | What It Shows | Current Role |
| --- | --- | --- |
| `artifacts/report/repair_ablation_comparison.csv` | heuristic-only versus bounded-exact repair comparison | report ablation table |
| `artifacts/report/realistic_default/summary.json` | repeated-run mean and best search results | benchmark evidence |
| `artifacts/report/official_default/summary.json` | repeated delegated/native/search official comparison with search-focused proof metrics | official stability evidence |
| `artifacts/report/official_search_proof/summary.json` | harder synthetic official case where search beats the simpler official paths | stronger official separation evidence |
| `artifacts/report/official_search_quality/summary.json` | synthetic official case where search beats a feasible native constructive result | official quality-improvement evidence |
| `artifacts/report/official_search_case_summary.csv` | one-table summary across public sample, proof case, and quality case | report-ready comparison table |
| `artifacts/report/realistic_default/convergence.csv` | iteration-by-iteration objective trace | convergence figure |
| `artifacts/report/presentation/realistic_seed1_worked_example.csv` | concrete before/after placement example | worked example figure |
| frontend `?view=organization` | ship-arrival to organized-yard sequence plus allocation trace and local impact signals | space-structure explanation |
| frontend `?view=equations` | official and development math surfaces | technical explanation |
| frontend `?view=proof` | objective terms plus official replay | judge-facing proof surface |
| frontend `?view=judge` | guided presentation order with autoplay and a closing competition claim | live demo route |

### 6.2 Official Comparison Table

The most concise official evidence surface in the repository is the generated comparison table below, sourced from `artifacts/report/official_search_case_summary.csv`.

| Instance | Delegated feasible | Native feasible | Search feasible | Delegated mean obj | Native mean obj | Search mean obj | Search vs delegated | Search vs native |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `official-sample-instance` | 6/6 | 6/6 | 6/6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `official-search-proof-instance` | 6/6 | 0/6 | 6/6 | 16.8056 | N/A | 9.7917 | -7.0139 | N/A |
| `official-search-quality-instance` | 6/6 | 6/6 | 6/6 | 72.0 | 72.0 | 23.0 | -49.0 | -49.0 |

Interpretation:
- the public sample is a stability check, not a separator
- the proof instance shows official search recovering a feasible result where native constructive fails
- the quality instance shows official search materially improving a feasible native solution rather than only rescuing infeasibility

## 7. Frontend Technical Alignment

The documentation is intentionally aligned with the current competition-facing frontend.

The frontend currently emphasizes:
- one active development layout at a time
- one active official replay at a time
- fullscreen dialogs for equations, proof, history, and walkthrough
- direct routes for proof, organization, and equations that can be opened independently for demos and judging
- a guided judge route that can autoplay through the strongest surfaces and finish on a closing claim
- the judge route now also pulls development repeated-run evidence, stable public-sample official evidence, a harder official rescue case, and a separate official quality-improvement case from the report artifact pipeline into the live demo snapshot
- KaTeX-rendered equations for the official and development objective surfaces

The two most important technical views are:
- `?view=equations`, which explains the mathematical objective surface
- `?view=proof`, which shows official objective terms, feasibility status, runtime, and replay in one fullscreen surface

The new supporting view is:
- `?view=organization`, which explains how YardMind moves from ship arrival to a readable yard by combining constructive placement, search repair, reserve preservation, and a per-block impact trace instead of only showing a final placement score

The presentation route that ties the story together is:
- `?view=judge`, which presents organization first, then equations, then proof, then a short why-we-win closer

The quickest local launcher for this route is:
- `./scripts/open-react-demo.ps1 -View judge -AutoPlay -Kiosk`

The quickest full presentation pack launcher is:
- `./scripts/open-judge-pack.ps1`

The quickest end-to-end rehearsal command is:
- `./scripts/open-submission-rehearsal.ps1`

This report and those two routes now describe the same objective notation and the same intended solver story.

## 8. Figures And Tables Plan

This repository now has a report structure that can support a stronger final submission package. The intended figure set is:
- objective decomposition figure from the equations view
- convergence figure from `artifacts/report/presentation/realistic_seed1_convergence.csv`
- worked example figure from `artifacts/report/presentation/realistic_seed1_worked_example.csv`
- space-organization figure from the frontend `?view=organization` route
- guided judge-sequence figure from the frontend `?view=judge` route
- repair ablation table from `artifacts/report/repair_ablation_comparison.csv`
- official proof screenshot from the frontend `?view=proof` route

This means the report can now be completed with concrete generated artifacts instead of invented post hoc figures.

### 8.1 Current Exported Figures

Organization and allocation figure:

![YardMind organization figure](../../artifacts/demo/hackathon-frontend-organization.png)

Official equations surface:

![YardMind equations figure](../../artifacts/demo/hackathon-frontend-equations.png)

Official proof surface:

![YardMind proof figure](../../artifacts/demo/hackathon-frontend-proof.png)

Judge-sequence overview:

![YardMind judge sequence](../../artifacts/demo/hackathon-frontend-judge.png)

## 9. Limitations

The current system is still limited in several important ways:
- the development objective remains a proxy and not the official contest score
- the official search path is lighter than a true direct official neighborhood-search solver
- exact repair is still bounded and local rather than backed by a full exact backend
- broader official runtime and quality evidence is still needed on larger instances

## 10. Next Technical Priorities

The highest-value next steps are:
- extend the official path into a true direct-improvement official neighborhood search
- generate stronger larger-scale official evidence
- turn the existing artifact pipeline into final report figures and tables
- keep the documentation, frontend proof surface, and algorithm implementation aligned

## 11. Document Map

Main technical report:
- `docs/report/technical-report.md`

Short judge-facing companion:
- `docs/report/judge-summary.md`

Draft predecessor retained for historical context:
- `docs/report/technical-report-outline.md`

Artifact index:
- `docs/report/chart-ready-artifacts.md`

One-command pack generation:
- `scripts/generate-report-pack.ps1`

Frontend proof and equations routes:
- `http://127.0.0.1:5182/?view=organization`
- `http://127.0.0.1:5182/?view=proof`
- `http://127.0.0.1:5182/?view=equations`