# Demo Script

## Purpose

Use this script when presenting YardMind live to judges. It is designed to match the current frontend, screenshots, and submission kit so the spoken story stays consistent with the repository.

For a fast operational runbook, see `docs/presentation/demo-checklist.md`.

## Open Before Presenting

- React app: `http://localhost:5173`
- Judge view: `http://localhost:5173/?view=judge`
- Backup screenshot: `artifacts/demo/hackathon-frontend-judge.png`

## 30-Second Version

YardMind is a retrieval-aware optimizer for shipyard block planning. Instead of only checking whether a block fits right now, it also evaluates whether that placement will create expensive downstream retrieval conflicts later. We build a feasible plan quickly, improve it with search under runtime limits, and expose the whole process in a frontend that shows layouts, search behavior, and official-sample comparison in one judge-friendly surface.

## 90-Second Version

Shipyard planning is not just a packing problem. A layout can look efficient today and still become operationally expensive tomorrow if it blocks later retrievals or creates congestion.

YardMind addresses that by using retrieval-aware optimization. We first generate a feasible plan, then improve it with a seeded search loop. The key is that placements are scored not only for immediate fit, but also for downstream disruption risk.

In the frontend, we show that story directly. Judges can compare the constructive baseline with the improved layout, inspect search metrics and accepted moves, and see delegated-versus-native official constructive behavior without digging through raw logs or JSON.

So the value is not only that we optimize the yard. It is that we make the optimization legible, reproducible, and demo-ready.

## 3-Minute Live Demo Script

### Opening

We are YardMind. Our focus is shipyard block planning, but with one important difference: we optimize for retrieval-aware operations, not just dense placement.

A lot of layouts look good if you only ask, “Does this fit?” The real cost appears later, when a block has to be retrieved and the yard has become fragile, congested, or expensive to reshuffle.

### Screen 1: Hero And Metrics

On the first screen, I start with the control-room view. This gives the high-level story immediately: constructive objective, improved search objective, iteration count, and official comparison metrics.

What I want judges to notice here is that this is not just a static mockup. The interface is driven by generated solver data, and it exposes the optimization process rather than hiding it.

### Screen 2: Layout Comparison

Next, I compare the constructive baseline and the local-search incumbent.

This is where the core idea becomes visible. We are not only trying to pack blocks tightly. We are trying to arrange them in a way that reduces downstream operational pain. A slightly different placement now can avoid much more expensive retrieval disruption later.

### Screen 3: Search Trace

Then I scroll to the search trace.

This is important because it proves the system is actively exploring and improving candidates. You can see destroy and repair operators, feasibility of candidates, objective progression, and whether moves are accepted. That makes the solver behavior interpretable for both judges and technical reviewers.

### Screen 4: Official Comparison

After that, I show the official delegated-versus-native constructive comparison.

This is our bridge from the development solver to the official challenge path. It shows that we already support official-sample inspection, validation, constructive benchmarking, and a first official portfolio-search layer.

### Screen 5: Judge Mode

Finally, I switch to judge mode.

This view is optimized for screenshots and evaluation. It keeps the strongest parts of the story above the fold: the problem framing, the key metrics, the layout comparison, and the official comparison context.

### Close

The core message is simple: YardMind treats the yard as a time-evolving operational system. We build feasible plans quickly, improve them under runtime limits, and make the results visible enough for people to trust and evaluate them.

## Presenter Cues

- If time is short, skip directly from hero metrics to layout comparison and then to judge mode.
- If a judge asks what is technically novel, emphasize retrieval-aware scoring and explainable search traces.
- If a judge asks about challenge readiness, mention official-sample inspection, validation, constructive comparison, and portfolio search as the current bridge to the official path.
- If the live app is unavailable, use the exported judge screenshot and narrate the same sequence.

## Quick Q&A Answers

### What problem are you solving?

We are solving shipyard block planning as a coupled space-time optimization problem where future retrieval cost matters, not just immediate packing feasibility.

### Why is this better than greedy packing?

Greedy packing can create fragile layouts that are cheap now but expensive later. YardMind scores downstream disruption risk so it can preserve future mobility.

### What is in the frontend?

The frontend shows high-level optimization metrics, constructive versus improved layouts, search trace evidence, and official-sample constructive comparison in one view.

### What is the current limitation?

The official path is still early. We support official inspection, validation, constructive comparison, and a first portfolio-search layer, but a full official neighborhood-improvement loop is still the next major step.
