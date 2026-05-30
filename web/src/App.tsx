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
    </main>
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
