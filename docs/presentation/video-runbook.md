# YardMind 2-3 Minute Video Runbook

## Target

- Target runtime: `2:20` to `2:45`
- Goal: show that YardMind is not only visually polished, but technically credible, benchmarked, and competition-ready
- Tone: calm, confident, engineering-first

## Recording Setup

- Record in `16:9` at `1080p`
- Browser zoom: `90%` if needed so the main cards fit cleanly
- Keep cursor movement slow and intentional
- Do not scroll unless the script explicitly says to scroll
- Prefer one clean take with 5-7 scene changes instead of many fast cuts

## Winning Structure

1. Open with the product identity and problem framing
2. Show the development layout to prove this is a real optimizer, not a static mockup
3. Show the equation / proof surfaces to establish technical rigor
4. Show the official replay to make the result auditable
5. Close with benchmark evidence and the winning claim

## Exact Screens To Capture

### Shot 1: Landing identity

- Screen: `Landing Overview`
- Focus:
  - title area
  - status summary card
  - search lift and official delta cards
- Duration: `15-20s`
- Why: establishes the product, the challenge, and that the result is already measurable

### Shot 2: Development layout

- Screen: `Development layout`
- Focus:
  - active yard state
  - objective, delta vs baseline, risk, congestion pills
- Duration: `20-25s`
- Why: shows the solver is making layout decisions with operational meaning, not only producing a score

### Shot 3: Presentation flow

- Screen: `Open presentation flow`
- Focus:
  - left step rail
  - `Space organization`
  - `Optimization target`
- Duration: `20-25s`
- Why: shows judges there is a guided explanation path, not a messy dashboard

### Shot 4: Equation proof

- Screen: Presentation flow, `Equations`
- Focus:
  - official objective formula
- Duration: `15-20s`
- Why: makes the optimization target explicit and credible

### Shot 5: Official evidence

- Screen: Presentation flow, `Proof`
- Focus:
  - `Summary`
  - `Quality`
  - `Internal`
- Duration: `35-45s`
- Why: this is the strongest proof section and should carry the largest share of the video

### Shot 6: Replay

- Screen: top tab `Replay`
- Focus:
  - official search replay
  - play / pause controls
  - event pills showing `ENTRY` / `EXIT`
  - replay summary cards
- Duration: `25-35s`
- Why: converts benchmark claims into something judges can inspect visually

### Shot 7: Deep analysis close

- Screen: `Deep analysis`
- Focus:
  - benchmark evidence cards
  - internal robustness checks card
- Duration: `20-25s`
- Why: closes with evidence that the solver generalizes beyond one public case

## Shot-by-Shot Prompts For The Presenter

### Shot 1 Prompt

"Start on Landing Overview. Keep the pointer near the status cards. Pause long enough for judges to read search lift and official delta."

### Shot 2 Prompt

"Switch to Development layout. Hold on the active yard state and briefly circle the KPI pills for objective, delta, risk, and congestion."

### Shot 3 Prompt

"Open Presentation flow. Show that the product has a guided judge path: organization, equations, proof, and final claim."

### Shot 4 Prompt

"Move to Equations. Keep the formula centered on screen. Do not rush this shot. Let the judges see that the objective is explicit."

### Shot 5 Prompt

"Move to Proof. First show Summary, then click Quality, then Internal. Pause on each tab just long enough for the numbers to register."

### Shot 6 Prompt

"Switch to Replay. Press Play once, let one or two ENTRY or EXIT events occur, then pause. Keep the event pills and bay activity visible."

### Shot 7 Prompt

"Finish on Deep analysis and hold on the benchmark evidence cards. End with the internal robustness card visible."

## Professional Voiceover Prompt

Use this if you want to generate or rehearse a polished narration:

"Create a confident 2.5-minute hackathon demo voiceover for YardMind, a retrieval-aware shipyard block allocation optimizer. The tone should be professional, concise, and judge-facing. Emphasize feasibility first, improvement second, official validation, replay-based auditability, and benchmark evidence. Mention that the released quality case improves from 72 to 23, the proof case improves from 16.81 to 9.79 while staying feasible in 6 out of 6 runs, and internal hidden stress cases improve from 30 to 15 and from 38 to 18. Avoid hype words, avoid slang, and make every sentence sound technically credible and competition-ready." 

## Final Transcript

### Full 2-3 Minute Script

"This is YardMind, a retrieval-aware optimizer for shipyard block allocation. Instead of treating the yard like a static packing board, we model it as a time-evolving system where each placement affects future access, congestion, and schedule quality.

We start by constructing a feasible layout quickly, and then we improve it with targeted local search. That matters because in this problem, the best immediate fit is often not the best operational decision. A block can fit now, but still create expensive downstream moves later.

Here in the development layout, you can see that the system is not only chasing density. It is balancing objective value against retrieval risk and congestion, so the final arrangement remains workable and interpretable.

What makes YardMind strong in competition is that we do not stop at a visual layout. We also expose the actual optimization target. The objective is explicit, auditable, and tied to the released evaluation logic rather than a hidden heuristic story.

Then we move into proof. On the released proof instance, official search stays feasible in all 6 of 6 runs and improves the delegated mean objective from 16.81 to 9.79. On the released quality case, it improves the mean objective from 72 to 23, outperforming both delegated and native constructive baselines.

We also tested hidden official-format stress cases to check whether the solver generalizes beyond the public examples. In an overloaded-bay case, the mean objective improves from 30 to 15. In a tight-window cascade, it improves from 38 to 18, while native constructive is infeasible in all 6 runs. That gives us evidence of robustness, not just a single good demo instance.

Finally, the replay makes the schedule auditable. Judges can watch blocks enter, exit, and release bay capacity over time, while the official status, runtime, and objective delta remain visible. So the result is not a storyboard mockup. It is a validated, competition-facing solution with measurable gains and a clear explanation path.

YardMind combines readable allocation, explicit optimization logic, official validation, and robustness evidence. That is why we believe it is a strong, credible solution for this competition." 

## Shorter Backup Transcript

### 90-Second Version

"YardMind is a retrieval-aware optimizer for shipyard allocation. We first build a feasible layout, then improve it with local search that accounts for future access, congestion, and timing pressure.

The key point is that we are not only showing a layout. We expose the optimization objective, validate against the released checker, and make the solution auditable through replay.

On the released proof case, search improves the mean objective from 16.81 to 9.79 while staying feasible in 6 out of 6 runs. On the released quality case, it improves from 72 to 23. We also tested hidden official-format stress cases and saw further gains from 30 to 15 and from 38 to 18.

So YardMind is not just visually clear. It is measurable, validated, and robust under harder cases, which makes it a strong competition-ready solution." 

## Recording Notes

- Best order for the video:
  - `Landing Overview`
  - `Development layout`
  - `Open presentation flow`
  - `Equations`
  - `Proof > Quality`
  - `Proof > Internal`
  - `Replay`
  - `Deep analysis`
- If time gets tight, cut `Data panorama` first
- Do not spend too long in the development layout; the strongest proof is in `Proof`, `Replay`, and `Deep analysis`
- Keep the ending on evidence, not on navigation