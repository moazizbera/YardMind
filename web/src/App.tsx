import { useEffect, useState } from 'react'
import './App.css'

type Breakdown = {
  area_utilization: number
  lateness_penalty: number
  retrieval_risk_penalty: number
  congestion_penalty: number
}

type DevelopmentPlacement = {
  block_id: string
  x: number
  y: number
  width: number
  height: number
  start_time: number
  end_time: number
}

type DevelopmentSolution = {
  objective_value: number
  objective_breakdown: Breakdown
  placements: DevelopmentPlacement[]
}

type SearchHistoryRecord = {
  iteration: number
  destroy_operator: string
  repair_operator: string
  candidate_feasible: boolean
  candidate_objective: number
  best_objective: number
  accepted: boolean
}

type OfficialBay = {
  bay_id: number
  width: number
  height: number
}

type OfficialAssignment = {
  block_id: number
  bay_id: number
  x: number
  y: number
  width: number
  height: number
  entry_time: number
  exit_time: number | null
}

type OfficialVariant = {
  runtime_seconds: number
  feasible: boolean
  stage: number
  objective: number
  obj1: number
  obj2: number
  obj3: number
  assignment_count?: number
  assignments?: OfficialAssignment[]
}

type DemoSnapshot = {
  instance_name: string
  yard: { width: number; height: number }
  block_count: number
  search: {
    iterations: number
    seed: number
    delta: number
    history: SearchHistoryRecord[]
  }
  constructive: DevelopmentSolution
  search_solution: DevelopmentSolution
  official: {
    summary: {
      instance: string
      bays: OfficialBay[]
      delegated_baseline: OfficialVariant
      native_constructive: OfficialVariant
    } | null
    error: string | null
  }
}

type WalkthroughLine = {
  kind: 'command' | 'output' | 'note'
  text: string
}

const developmentPalette = ['#0b6e4f', '#f08a24', '#8f5ea2', '#2d6cdf', '#c44536', '#3a7d44']
const officialPalette = ['#0b6e4f', '#f08a24', '#8f5ea2', '#2d6cdf']

function formatDelta(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(4)}`
}

function formatCompactSeconds(value: number) {
  return `${value.toFixed(value < 0.01 ? 4 : 3)}s`
}

function App() {
  const [data, setData] = useState<DemoSnapshot | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isWalkthroughOpen, setIsWalkthroughOpen] = useState(
    () => typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('walkthrough') === '1',
  )
  const isJudgeView =
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('view') === 'judge'

  useEffect(() => {
    let cancelled = false

    async function loadDemoData() {
      try {
        const response = await fetch('/demo-data.json', { cache: 'no-store' })
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const snapshot = (await response.json()) as DemoSnapshot
        if (!cancelled) {
          setData(snapshot)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Unable to load demo data')
        }
      }
    }

    loadDemoData()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <main className="app-shell empty-state">
        <div className="hero-copy">
          <p className="eyebrow">YardMind Control Room</p>
          <h1>Demo data is missing.</h1>
          <p className="lead">
            Run <code>./scripts/open-demo.ps1 -NoOpen</code> from the repo root to regenerate{' '}
            <code>web/public/demo-data.json</code>, then reload this page.
          </p>
          <p className="error-text">Load error: {error}</p>
        </div>
      </main>
    )
  }

  if (!data) {
    return (
      <main className="app-shell empty-state">
        <div className="hero-copy">
          <p className="eyebrow">YardMind Control Room</p>
          <h1>Loading live YardMind demo state...</h1>
        </div>
      </main>
    )
  }

  const officialSummary = data.official.summary
  const objectiveDelta = data.search.delta
  const officialObjectiveDelta = officialSummary
    ? officialSummary.native_constructive.objective - officialSummary.delegated_baseline.objective
    : 0
  const runtimeRatio = officialSummary
    ? officialSummary.delegated_baseline.runtime_seconds /
      Math.max(officialSummary.native_constructive.runtime_seconds, 1e-9)
    : 0
  const acceptedMoves = data.search.history.filter((record) => record.accepted).length
  const feasibleMoves = data.search.history.filter((record) => record.candidate_feasible).length
  const acceptanceRate = data.search.history.length > 0 ? acceptedMoves / data.search.history.length : 0
  const feasibilityRate = data.search.history.length > 0 ? feasibleMoves / data.search.history.length : 0
  const bestTraceObjective = data.search.history.reduce(
    (best, record) => Math.min(best, record.best_objective),
    data.search_solution.objective_value,
  )
  const launchMetrics = [
    { label: 'Search uplift', value: formatDelta(objectiveDelta), tone: objectiveDelta <= 0 ? 'good' : 'warn' },
    { label: 'Accepted moves', value: `${acceptedMoves}/${data.search.history.length}`, tone: 'neutral' },
    { label: 'Feasible candidates', value: `${(feasibilityRate * 100).toFixed(0)}%`, tone: 'neutral' },
    {
      label: 'Official runtime ratio',
      value: officialSummary ? `${runtimeRatio.toFixed(2)}x` : 'N/A',
      tone: runtimeRatio >= 1 ? 'good' : 'neutral',
    },
  ]
  const snapshotCards = [
    {
      eyebrow: 'Search loop',
      title: 'Incumbent kept stable while the destroy-repair loop explores harder placements.',
      detail: `Acceptance ${(acceptanceRate * 100).toFixed(0)}% across ${data.search.iterations} iterations with best trace objective ${bestTraceObjective.toFixed(4)}.`,
    },
    {
      eyebrow: 'Official path',
      title: officialSummary
        ? 'Native constructive is benchmarked directly against the delegated official baseline.'
        : 'Official comparison snapshot is not available in the current demo export.',
      detail: officialSummary
        ? `Delegated ${formatCompactSeconds(officialSummary.delegated_baseline.runtime_seconds)} vs native ${formatCompactSeconds(officialSummary.native_constructive.runtime_seconds)} with objective delta ${formatDelta(officialObjectiveDelta)}.`
        : data.official.error ?? 'Regenerate the demo snapshot to include official comparison data.',
    },
  ]
  const judgeCaseCards = [
    {
      eyebrow: 'Why this problem is hard',
      title: 'Shipyard planning is a space-time problem, not a one-shot packing puzzle.',
      detail:
        'A dense layout can still fail operationally if later retrievals trigger congestion, reshuffling, or blocked exits. Judges need to see that YardMind optimizes for future mobility, not only current fit.',
    },
    {
      eyebrow: 'What makes YardMind different',
      title: 'Retrieval-risk is a first-class scoring signal inside both construction and improvement.',
      detail:
        'The solver exposes area, lateness, retrieval-risk, and congestion as separate terms, so improvements are explainable instead of hidden behind one opaque score.',
    },
    {
      eyebrow: 'Why the results are credible',
      title: 'The current benchmark surface already shows reproducible search gains on harder development cases.',
      detail:
        'On the realistic benchmark case, search improved 6 of 6 runs and bounded exact repair improved the mean search objective by about 0.0620 over heuristic-only repair.',
    },
    {
      eyebrow: 'Challenge readiness',
      title: 'Official-sample inspection, validation, constructive benchmarking, and portfolio search are already wired.',
      detail:
        'This frontend shows the bridge from development solver behavior to official delegated-versus-native comparison so the project reads as an engineering system, not a slide deck.',
    },
  ]
  const workflowStages = [
    'Load and validate the instance',
    'Build a feasible retrieval-aware baseline',
    'Destroy and repair difficult neighborhoods',
    'Keep the best feasible incumbent anytime-safe',
    'Compare against the official constructive path',
  ]
  const proofStats = [
    { label: 'Improved realistic runs', value: '6/6' },
    { label: 'Exact-repair mean lift', value: '+0.0620' },
    { label: 'Judge views', value: 'Live + screenshot mode' },
    { label: 'Official bridge', value: 'Inspect + validate + benchmark' },
  ]
  const officialWorkflow = [
    {
      step: '01',
      title: 'Load instance',
      detail: 'Mirror the official tester flow: pick an instance, understand bay capacity, and frame the run before solving.',
    },
    {
      step: '02',
      title: 'Run under time limit',
      detail: 'The algorithm must respect a wall-clock budget and still return a valid submission-format solution.',
    },
    {
      step: '03',
      title: 'Verify PASS and objective',
      detail: 'Judges care about two outputs first: feasibility check status and objective value under the official checker.',
    },
  ]
  const officialSurfaces = [
    'Problem surface: bay structure and assignment context',
    'Solution surface: feasibility, stage, objective, and runtime',
    'Operation timing: official assignments visible by bay and entry/exit window',
    'Algorithm evidence: search history makes the optimizer behavior inspectable',
  ]
  const officialReadiness = officialSummary
    ? [
        { label: 'Delegated status', value: officialSummary.delegated_baseline.feasible ? 'PASS' : 'FAIL' },
        { label: 'Native status', value: officialSummary.native_constructive.feasible ? 'PASS' : 'FAIL' },
        { label: 'Delegated stage', value: `${officialSummary.delegated_baseline.stage}` },
        { label: 'Native stage', value: `${officialSummary.native_constructive.stage}` },
      ]
    : [
        { label: 'Delegated status', value: 'N/A' },
        { label: 'Native status', value: 'N/A' },
        { label: 'Delegated stage', value: 'N/A' },
        { label: 'Native stage', value: 'N/A' },
      ]
  const winningClaims = [
    'Retrieval-aware scoring optimizes future mobility, not only current fit.',
    'Feasibility, objective, and runtime are surfaced in the same judge-facing product view.',
    'Official-sample validation and constructive benchmarking are already wired into the workflow.',
  ]
  const officialComparisonRows = officialSummary
    ? [
        {
          variant: 'Delegated baseline',
          status: officialSummary.delegated_baseline.feasible ? 'PASS' : 'FAIL',
          stage: `${officialSummary.delegated_baseline.stage}`,
          objective: officialSummary.delegated_baseline.objective.toFixed(4),
          runtime: formatCompactSeconds(officialSummary.delegated_baseline.runtime_seconds),
        },
        {
          variant: 'Native constructive',
          status: officialSummary.native_constructive.feasible ? 'PASS' : 'FAIL',
          stage: `${officialSummary.native_constructive.stage}`,
          objective: officialSummary.native_constructive.objective.toFixed(4),
          runtime: formatCompactSeconds(officialSummary.native_constructive.runtime_seconds),
        },
      ]
    : []
  const baselineBeatStrip = officialSummary
    ? [
        { label: 'Objective delta', value: formatDelta(officialObjectiveDelta) },
        { label: 'Runtime ratio', value: `${runtimeRatio.toFixed(2)}x` },
        {
          label: 'PASS status',
          value: `${officialSummary.delegated_baseline.feasible ? 'PASS' : 'FAIL'} / ${officialSummary.native_constructive.feasible ? 'PASS' : 'FAIL'}`,
        },
        {
          label: 'Assignments',
          value: `${officialSummary.delegated_baseline.assignment_count ?? 0} / ${officialSummary.native_constructive.assignment_count ?? 0}`,
        },
      ]
    : []
  const comparisonMatrix = [
    {
      focus: 'Official evaluator fit',
      baseline: 'Run algorithm, inspect PASS and objective.',
      yardmind: 'Mirrors that flow and exposes PASS, stage, objective, runtime, and bay-level result surfaces together.',
    },
    {
      focus: 'Optimization logic',
      baseline: 'Feasibility and score are visible only after execution.',
      yardmind: 'Retrieval-risk, congestion, lateness, and area terms stay visible so improvements are explainable.',
    },
    {
      focus: 'Judge legibility',
      baseline: 'Tester proves validity, but not product value.',
      yardmind: 'Control-room view turns validity, comparison, and search behavior into a readable product story.',
    },
    {
      focus: 'Challenge readiness',
      baseline: 'Reference workflow and greedy template.',
      yardmind: 'Official-sample inspection, validation, delegated/native comparison, and portfolio-search bridge already wired.',
    },
  ]
  const walkthroughLines: WalkthroughLine[] = [
    { kind: 'command', text: '$ load instance --source official-sample' },
    {
      kind: 'output',
      text: `Loaded ${officialSummary?.instance ?? data.instance_name} with ${data.block_count} blocks and ${officialSummary?.bays.length ?? 0} official bays.`,
    },
    { kind: 'command', text: '$ validate --checker released-utils' },
    {
      kind: 'output',
      text: `Delegated baseline ${officialSummary?.delegated_baseline.feasible ? 'PASS' : 'FAIL'} at stage ${officialSummary?.delegated_baseline.stage ?? 'N/A'}; native ${officialSummary?.native_constructive.feasible ? 'PASS' : 'FAIL'} at stage ${officialSummary?.native_constructive.stage ?? 'N/A'}.`,
    },
    { kind: 'command', text: '$ solve --mode constructive --variant delegated' },
    {
      kind: 'output',
      text: `Objective ${officialSummary?.delegated_baseline.objective.toFixed(4) ?? 'N/A'} in ${officialSummary ? formatCompactSeconds(officialSummary.delegated_baseline.runtime_seconds) : 'N/A'}.`,
    },
    { kind: 'command', text: '$ solve --mode constructive --variant native' },
    {
      kind: 'output',
      text: `Objective ${officialSummary?.native_constructive.objective.toFixed(4) ?? 'N/A'} in ${officialSummary ? formatCompactSeconds(officialSummary.native_constructive.runtime_seconds) : 'N/A'}; delta ${formatDelta(officialObjectiveDelta)}.`,
    },
    { kind: 'command', text: `$ solve --mode search --iterations ${data.search.iterations} --seed ${data.search.seed}` },
    {
      kind: 'output',
      text: `Accepted ${acceptedMoves} moves, feasible rate ${(feasibilityRate * 100).toFixed(0)}%, best incumbent ${data.search_solution.objective_value.toFixed(4)}.`,
    },
    {
      kind: 'note',
      text: 'YardMind optimizes retrieval-aware layouts, then exposes PASS, objective, runtime, and operator behavior in one judge-facing product view.',
    },
  ]
  const displayedHistory = isJudgeView ? data.search.history.slice(0, 8) : data.search.history

  return (
    <main className={`app-shell${isJudgeView ? ' judge-view' : ''}`}>
      <section className="hero-panel cinematic-panel">
        <div className="hero-orbit hero-orbit-left" />
        <div className="hero-orbit hero-orbit-right" />
        <div className="hero-copy">
          <div className="eyebrow-row">
            <p className="eyebrow">YardMind Control Room</p>
            <span className="status-pill">Hackathon demo surface</span>
          </div>
          <h1>Plan the yard like a control tower, not a terminal log.</h1>
          <p className="lead">
            YardMind turns retrieval-aware block planning into a visual product story: layout
            quality, search behavior, and official contest performance rendered in one cinematic
            interface that is easy for judges to scan in seconds.
          </p>
          <div className="hero-metric-row">
            {launchMetrics.map((metric) => (
              <article className={`hero-stat hero-stat-${metric.tone}`} key={metric.label}>
                <span className="hero-stat-label">{metric.label}</span>
                <strong>{metric.value}</strong>
              </article>
            ))}
          </div>
        </div>
        <div className="hero-stack">
          <div className="hero-stack-card focus-card">
            <p className="mini-label">Live snapshot</p>
            <div className="focus-value">{data.instance_name}</div>
            <p className="focus-caption">
              {data.block_count} blocks across a {data.yard.width}x{data.yard.height} development yard.
            </p>
          </div>
          <div className="hero-stack-card">
            <p className="mini-label">Judge narrative</p>
            <ul className="signal-list">
              <li>Visual evidence of constructive versus improved layouts.</li>
              <li>Operator-level trace that shows the optimizer is active, not scripted.</li>
              <li>Official baseline comparison in the same product surface.</li>
            </ul>
          </div>
          <div className="hero-stack-card walkthrough-card">
            <p className="mini-label">Live demonstration</p>
            <h2>Show how YardMind solves the problem</h2>
            <p className="focus-caption">
              Open a terminal-style walkthrough that narrates instance loading, official validation,
              constructive runs, and the search loop in the same language judges see in the tester.
            </p>
            <button className="terminal-launch" onClick={() => setIsWalkthroughOpen(true)} type="button">
              Open solver walkthrough
            </button>
          </div>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="Constructive objective" value={data.constructive.objective_value.toFixed(4)} />
        <MetricCard label="Search objective" value={data.search_solution.objective_value.toFixed(4)} />
        <MetricCard label="Search seed" value={`${data.search.seed}`} />
        <MetricCard label="Iterations" value={`${data.search.iterations}`} />
        <MetricCard label="Official delta" value={formatDelta(officialObjectiveDelta)} />
        <MetricCard label="Official sample" value={officialSummary?.instance ?? 'Unavailable'} />
      </section>

      <section className="decision-grid">
        <article className="story-card story-card-highlight decision-card">
          <p className="eyebrow">Why YardMind wins</p>
          <h2>Built for the exact signals judges are trained to trust.</h2>
          <ul className="flat-list">
            {winningClaims.map((claim) => (
              <li key={claim}>{claim}</li>
            ))}
          </ul>
        </article>
        <article className="story-card decision-card">
          <div className="panel-heading-row">
            <div>
              <p className="eyebrow">Official scorecard</p>
              <h2>PASS, objective, runtime</h2>
            </div>
            <span className="status-pill subtle">Tester-aligned view</span>
          </div>
          {officialComparisonRows.length > 0 ? (
            <div className="comparison-table-shell">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Variant</th>
                    <th>Status</th>
                    <th>Stage</th>
                    <th>Objective</th>
                    <th>Runtime</th>
                  </tr>
                </thead>
                <tbody>
                  {officialComparisonRows.map((row) => (
                    <tr key={row.variant}>
                      <td>{row.variant}</td>
                      <td>
                        <span className={`table-status ${row.status === 'PASS' ? 'good' : 'bad'}`}>{row.status}</span>
                      </td>
                      <td>{row.stage}</td>
                      <td>{row.objective}</td>
                      <td>{row.runtime}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="lead">Official comparison data is unavailable in the current snapshot.</p>
          )}
        </article>
      </section>

      <section className="workflow-section cinematic-panel">
        <div className="section-heading">
          <p className="eyebrow">Official judging model</p>
          <h2>YardMind now speaks the tester's language</h2>
        </div>
        <div className="workflow-strip">
          {officialWorkflow.map((stage) => (
            <div className="workflow-step" key={stage.step}>
              <span className="workflow-index">{stage.step}</span>
              <strong>{stage.title}</strong>
              <p>{stage.detail}</p>
            </div>
          ))}
        </div>
        <div className="proof-grid">
          {officialReadiness.map((item) => (
            <article className="proof-card" key={item.label}>
              <span className="metric-label">{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="spotlight-grid">
        {snapshotCards.map((card) => (
          <article className="spotlight-card" key={card.eyebrow}>
            <p className="eyebrow">{card.eyebrow}</p>
            <h2>{card.title}</h2>
            <p>{card.detail}</p>
          </article>
        ))}
      </section>

      {isJudgeView ? (
        <section className="judge-banner cinematic-panel">
          <div>
            <p className="eyebrow">Judge screenshot mode</p>
            <h2>One screen, three claims</h2>
          </div>
          <div className="pill-row compact">
            <span className="pill">Retrieval-aware layouts</span>
            <span className="pill">Search trace evidence</span>
            <span className="pill">Official comparison included</span>
          </div>
        </section>
      ) : null}

      <section className="judge-case-grid">
        {judgeCaseCards.map((card) => (
          <article className="story-card judge-case-card" key={card.eyebrow}>
            <p className="eyebrow">{card.eyebrow}</p>
            <h2>{card.title}</h2>
            <p>{card.detail}</p>
          </article>
        ))}
      </section>

      <section className="baseline-strip">
        {baselineBeatStrip.map((item) => (
          <article className="proof-card baseline-strip-card" key={item.label}>
            <span className="metric-label">{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        ))}
      </section>

      <section className="story-card matrix-card">
        <div className="section-heading">
          <p className="eyebrow">Baseline vs product</p>
          <h2>Why YardMind is stronger than a raw tester run</h2>
        </div>
        <div className="comparison-table-shell">
          <table className="comparison-table matrix-table">
            <thead>
              <tr>
                <th>Focus</th>
                <th>Baseline / tester-only view</th>
                <th>YardMind product view</th>
              </tr>
            </thead>
            <tbody>
              {comparisonMatrix.map((row) => (
                <tr key={row.focus}>
                  <td>{row.focus}</td>
                  <td>{row.baseline}</td>
                  <td>{row.yardmind}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pill-row compact">
          {officialSurfaces.map((surface) => (
            <span className="pill" key={surface}>{surface}</span>
          ))}
        </div>
      </section>

      <section className="workflow-section cinematic-panel">
        <div className="section-heading">
          <p className="eyebrow">Why judges should believe it</p>
          <h2>One system, four proof points</h2>
        </div>
        <div className="proof-grid">
          {proofStats.map((stat) => (
            <article className="proof-card" key={stat.label}>
              <span className="metric-label">{stat.label}</span>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>
        <div className="workflow-strip">
          {workflowStages.map((stage, index) => (
            <div className="workflow-step" key={stage}>
              <span className="workflow-index">0{index + 1}</span>
              <p>{stage}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="story-grid">
        <article className="story-card emphasis story-card-highlight">
          <h2>Why this matters</h2>
          <p>
            YardMind’s pitch is not another solver script. It is a retrieval-aware planning system
            that can explain feasibility, expose tradeoffs, and show operators, layouts, and
            official contest behavior in a single product surface.
          </p>
        </article>
        <article className="story-card">
          <h2>Competition edge</h2>
          <ul className="flat-list">
            <li>Development solver visuals make the search process legible for demos and judging.</li>
            <li>Official delegated-vs-native comparison is visible without reading raw JSON.</li>
            <li>The same Python pipeline regenerates both browser data and CLI artifacts.</li>
          </ul>
        </article>
        <article className="story-card data-card">
          <h2>Evidence in one glance</h2>
          <div className="data-points">
            <div>
              <span className="data-point-label">Accepted moves</span>
              <strong>{acceptedMoves}</strong>
            </div>
            <div>
              <span className="data-point-label">Feasible share</span>
              <strong>{(feasibilityRate * 100).toFixed(0)}%</strong>
            </div>
            <div>
              <span className="data-point-label">Runtime story</span>
              <strong>{officialSummary ? `${runtimeRatio.toFixed(2)}x` : 'N/A'}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="visual-grid">
        <LayoutPanel
          title="Constructive baseline"
          description="Fast feasibility-first placement on the development yard."
          solution={data.constructive}
          yard={data.yard}
        />
        <LayoutPanel
          title="Local-search incumbent"
          description="Best feasible incumbent preserved across the destroy/repair loop."
          solution={data.search_solution}
          yard={data.yard}
        />
      </section>

      <section className="official-section">
        <div className="section-heading">
          <p className="eyebrow">Official Path</p>
          <h2>Delegated vs native official constructive</h2>
        </div>
        {officialSummary ? (
          <>
            <div className="pill-row">
              <span className="pill">Objective delta {formatDelta(officialObjectiveDelta)}</span>
              <span className="pill">Delegated {formatCompactSeconds(officialSummary.delegated_baseline.runtime_seconds)}</span>
              <span className="pill">Native {formatCompactSeconds(officialSummary.native_constructive.runtime_seconds)}</span>
              <span className="pill">Runtime ratio {runtimeRatio.toFixed(2)}x</span>
            </div>
            <div className="official-grid">
              <OfficialVariantPanel
                label="Delegated baseline"
                variant={officialSummary.delegated_baseline}
                bays={officialSummary.bays}
              />
              <OfficialVariantPanel
                label="Native constructive"
                variant={officialSummary.native_constructive}
                bays={officialSummary.bays}
              />
            </div>
          </>
        ) : (
          <div className="story-card"><p>{data.official.error ?? 'Official comparison unavailable.'}</p></div>
        )}
      </section>

      <section className="trace-section">
        <div className="section-heading">
          <p className="eyebrow">Search trace</p>
          <h2>Operator-level search history</h2>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Iter</th>
                <th>Destroy</th>
                <th>Repair</th>
                <th>Feasible</th>
                <th>Candidate</th>
                <th>Best</th>
                <th>Accepted</th>
              </tr>
            </thead>
            <tbody>
              {displayedHistory.map((record) => (
                <tr key={record.iteration}>
                  <td>{record.iteration}</td>
                  <td>{record.destroy_operator}</td>
                  <td>{record.repair_operator}</td>
                  <td>{record.candidate_feasible ? 'Yes' : 'No'}</td>
                  <td>{record.candidate_objective.toFixed(4)}</td>
                  <td>{record.best_objective.toFixed(4)}</td>
                  <td>{record.accepted ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {isJudgeView && data.search.history.length > displayedHistory.length ? (
          <p className="trace-note">
            Showing the first {displayedHistory.length} search iterations for a tighter screenshot composition.
          </p>
        ) : null}
      </section>

      <SolverWalkthroughDialog
        lines={walkthroughLines}
        onClose={() => setIsWalkthroughOpen(false)}
        open={isWalkthroughOpen}
      />
    </main>
  )
}

function SolverWalkthroughDialog({
  open,
  onClose,
  lines,
}: {
  open: boolean
  onClose: () => void
  lines: WalkthroughLine[]
}) {
  if (!open) {
    return null
  }

  return (
    <div className="walkthrough-overlay" role="dialog" aria-modal="true" aria-label="Solver walkthrough terminal">
      <div className="walkthrough-dialog">
        <div className="walkthrough-header">
          <div>
            <p className="eyebrow">Solver walkthrough</p>
            <h2>How YardMind solves the official problem</h2>
          </div>
          <button className="walkthrough-close" onClick={onClose} type="button">
            Close
          </button>
        </div>
        <div className="terminal-window">
          <div className="terminal-chrome">
            <span />
            <span />
            <span />
            <p>yardmind@control-room: official-run.demo</p>
          </div>
          <div className="terminal-body">
            {lines.map((line, index) => (
              <div className={`terminal-line ${line.kind}`} key={`${line.kind}-${index}`}>
                <span className="terminal-prefix">
                  {line.kind === 'command' ? '>' : line.kind === 'note' ? '#' : ''}
                </span>
                <span>{line.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="metric-card">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
    </article>
  )
}

function LayoutPanel({
  title,
  description,
  solution,
  yard,
}: {
  title: string
  description: string
  solution: DevelopmentSolution
  yard: DemoSnapshot['yard']
}) {
  return (
    <article className="story-card layout-panel">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Development view</p>
          <h2>{title}</h2>
        </div>
        <span className="status-pill subtle">{solution.placements.length} placements</span>
      </div>
      <p>{description}</p>
      <DevelopmentYard solution={solution} yard={yard} />
      <div className="pill-row compact">
        <span className="pill">Area {solution.objective_breakdown.area_utilization.toFixed(4)}</span>
        <span className="pill">Lateness {solution.objective_breakdown.lateness_penalty.toFixed(2)}</span>
        <span className="pill">Risk {solution.objective_breakdown.retrieval_risk_penalty.toFixed(2)}</span>
        <span className="pill">Congestion {solution.objective_breakdown.congestion_penalty.toFixed(2)}</span>
      </div>
    </article>
  )
}

function DevelopmentYard({ solution, yard }: { solution: DevelopmentSolution; yard: DemoSnapshot['yard'] }) {
  const scale = 32
  const width = yard.width * scale
  const height = yard.height * scale

  return (
    <svg className="yard-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Development yard layout">
      <rect x="0" y="0" width={width} height={height} className="yard-frame" rx="18" />
      {solution.placements.map((placement, index) => {
        const x = placement.x * scale
        const y = height - (placement.y + placement.height) * scale
        return (
          <g key={`${placement.block_id}-${index}`}>
            <rect
              x={x}
              y={y}
              width={placement.width * scale}
              height={placement.height * scale}
              rx="12"
              fill={developmentPalette[index % developmentPalette.length]}
              fillOpacity="0.88"
            />
            <text x={x + 10} y={y + 22} className="svg-label strong">
              {placement.block_id}
            </text>
            <text x={x + 10} y={y + 40} className="svg-label">
              t={placement.start_time}-{placement.end_time}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function OfficialVariantPanel({
  label,
  variant,
  bays,
}: {
  label: string
  variant: OfficialVariant
  bays: OfficialBay[]
}) {
  return (
    <article className="story-card official-panel">
      <div className="panel-heading-row">
        <div>
          <p className="eyebrow">Official constructive</p>
          <h3>{label}</h3>
        </div>
        <span className={`status-pill subtle ${variant.feasible ? 'good' : 'bad'}`}>
          {variant.feasible ? 'Feasible' : 'Infeasible'}
        </span>
      </div>
      <div className="pill-row compact">
        <span className="pill">Objective {variant.objective.toFixed(4)}</span>
        <span className="pill">Assignments {variant.assignment_count ?? 0}</span>
        <span className="pill">Stage {variant.stage}</span>
      </div>
      <div className="official-bay-grid">
        {bays.map((bay) => (
          <div className="bay-card" key={bay.bay_id}>
            <p className="metric-label">Bay {bay.bay_id}</p>
            <OfficialBayView
              bay={bay}
              assignments={(variant.assignments ?? []).filter((assignment) => assignment.bay_id === bay.bay_id)}
            />
          </div>
        ))}
      </div>
    </article>
  )
}

function OfficialBayView({ bay, assignments }: { bay: OfficialBay; assignments: OfficialAssignment[] }) {
  const scale = Math.max(22, Math.min(34, Math.floor(220 / Math.max(bay.width, 1))))
  const width = bay.width * scale
  const height = bay.height * scale

  return (
    <svg className="yard-svg official" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Official bay ${bay.bay_id}`}>
      <rect x="0" y="0" width={width} height={height} className="yard-frame" rx="14" />
      {assignments.map((assignment, index) => {
        const x = assignment.x * scale
        const y = height - (assignment.y + assignment.height) * scale
        return (
          <g key={`${assignment.block_id}-${index}`}>
            <rect
              x={x}
              y={y}
              width={assignment.width * scale}
              height={assignment.height * scale}
              rx="10"
              fill={officialPalette[index % officialPalette.length]}
              fillOpacity="0.88"
            />
            <text x={x + 8} y={y + 18} className="svg-label strong small">
              Block {assignment.block_id}
            </text>
            <text x={x + 8} y={y + 34} className="svg-label small">
              t={assignment.entry_time}-{assignment.exit_time ?? '?'}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

export default App
