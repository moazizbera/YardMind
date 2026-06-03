import { useEffect, useMemo, useState, type ReactNode } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import './App.css'
import shipyardImage from './images/Shipyard.webp'
import bayImage from './images/bay.webp'

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

type DevelopmentReportEvidence = {
  runs: number
  constructive_mean: number
  search_mean: number
  search_best: number
  improved_runs: number
}

type OfficialComparisonEvidence = {
  instance: string
  runs: number
  delegated_feasible_runs: number
  native_feasible_runs: number
  search_feasible_runs: number
  delegated_objective_mean: number | null
  native_objective_mean: number | null
  search_objective_mean: number | null
  objective_delta_mean: number | null
  search_vs_delegated_delta_mean: number | null
  search_vs_native_delta_mean: number | null
  delegated_runtime_mean: number | null
  native_runtime_mean: number | null
  search_runtime_mean: number | null
  native_better_or_equal_runs: number
  native_faster_runs: number
  search_better_or_equal_than_delegated_runs: number
  search_better_or_equal_than_native_runs: number
  search_faster_than_delegated_runs: number
}

type OfficialReportEvidence = {
  public_sample: OfficialComparisonEvidence | null
  proof_case: OfficialComparisonEvidence | null
  quality_case: OfficialComparisonEvidence | null
  hidden_overloaded_bay: OfficialComparisonEvidence | null
  hidden_tight_window: OfficialComparisonEvidence | null
}

type ReportEvidence = {
  development: DevelopmentReportEvidence | null
  official: OfficialReportEvidence | null
}

type AllocationTraceRow = {
  block_id: string
  from_x: number
  from_y: number
  to_x: number
  to_y: number
  moved: boolean
  access_delta: number
  conflict_delta: number
  core_delta: number
  signal_score: number
  reason: string
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
      official_search: OfficialVariant
    } | null
    error: string | null
  }
  report_evidence: ReportEvidence | null
  allocation_trace: AllocationTraceRow[]
}
type DemoProgressSummary = {
  instance: string
  blockCount: number
  searchLift: number
  objective: number | null
  runtimeSeconds: number | null
  stage: number | null
  status: string
  statusTone?: 'neutral' | 'good' | 'warn' | 'bad'
}

type WalkthroughLine = {
  kind: 'command' | 'output' | 'note'
  text: string
}

type OfficialPlaybackBounds = {
  start: number
  end: number
}

type OfficialOperationEvent = {
  kind: 'ENTRY' | 'EXIT'
  block_id: number
  bay_id: number
}

type DialogView = 'brief' | 'controls' | 'equations' | 'history' | 'judge' | 'organization' | 'proof' | 'walkthrough' | null
type PanoramaView = 'yard' | 'objective' | 'search' | 'proof' | 'judge'
type LandingTab = 'overview' | 'panorama' | 'development' | 'replay' | 'analysis'
type SolutionTab = 'constructive' | 'search'
const splashTargetLabels: Record<Exclude<DialogView, null>, string> = {
  brief: 'overview brief',
  controls: 'demo controls',
  equations: 'equation brief',
  history: 'search history',
  judge: 'presentation flow',
  organization: 'ship flow',
  proof: 'validation view',
  walkthrough: 'algorithm walkthrough',
}

const developmentPalette = ['#0b6e4f', '#f08a24', '#8f5ea2', '#2d6cdf', '#c44536', '#3a7d44']
const officialPalette = ['#0b6e4f', '#f08a24', '#8f5ea2', '#2d6cdf']

function formatDelta(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(4)}`
}

function formatCompactSeconds(value: number) {
  return `${value.toFixed(value < 0.01 ? 4 : 3)}s`
}

function formatPercent(value: number, digits = 0) {
  return `${(value * 100).toFixed(digits)}%`
}

function formatOptionalDelta(value: number | null) {
  return value === null ? 'n/a' : formatDelta(value)
}

function formatOptionalSeconds(value: number | null) {
  return value === null ? 'n/a' : formatCompactSeconds(value)
}

function formatOptionalFixed(value: number | null) {
  return value === null ? 'n/a' : value.toFixed(4)
}

function getDominantLabel(values: string[]) {
  if (values.length === 0) {
    return 'n/a'
  }

  const counts = new Map<string, number>()
  let leader = values[0]
  let leaderCount = 0

  for (const value of values) {
    const nextCount = (counts.get(value) ?? 0) + 1
    counts.set(value, nextCount)

    if (nextCount > leaderCount) {
      leader = value
      leaderCount = nextCount
    }
  }

  return leader
}

function useAnimatedNumber(target: number, enabled: boolean, duration = 1100) {
  const [value, setValue] = useState(enabled ? 0 : target)

  useEffect(() => {
    if (!enabled) {
      setValue(target)
      return
    }

    let frameId = 0
    let startTime = 0

    function tick(timestamp: number) {
      if (startTime === 0) {
        startTime = timestamp
      }

      const progress = Math.min((timestamp - startTime) / duration, 1)
      const eased = 1 - (1 - progress) * (1 - progress)
      setValue(target * eased)

      if (progress < 1) {
        frameId = window.requestAnimationFrame(tick)
      }
    }

    setValue(0)
    frameId = window.requestAnimationFrame(tick)

    return () => window.cancelAnimationFrame(frameId)
  }, [duration, enabled, target])

  return value
}

function getAssignmentsAtTime(assignments: OfficialAssignment[], time: number) {
  return assignments.filter((assignment) => {
    if (assignment.exit_time === null) {
      return assignment.entry_time <= time
    }
    return assignment.entry_time <= time && time < assignment.exit_time
  })
}

function getOperationsAtTime(assignments: OfficialAssignment[], time: number): OfficialOperationEvent[] {
  const exits = assignments
    .filter((assignment) => assignment.exit_time === time)
    .map((assignment) => ({ kind: 'EXIT' as const, block_id: assignment.block_id, bay_id: assignment.bay_id }))
  const entries = assignments
    .filter((assignment) => assignment.entry_time === time)
    .map((assignment) => ({ kind: 'ENTRY' as const, block_id: assignment.block_id, bay_id: assignment.bay_id }))

  return [...exits, ...entries].sort((left, right) => {
    if (left.kind !== right.kind) {
      return left.kind === 'EXIT' ? -1 : 1
    }

    return left.block_id - right.block_id
  })
}

function getTimelineBounds(assignments: OfficialAssignment[]): OfficialPlaybackBounds {
  if (assignments.length === 0) {
    return { start: 0, end: 0 }
  }

  const start = assignments.reduce((best, assignment) => Math.min(best, assignment.entry_time), assignments[0].entry_time)
  const end = assignments.reduce(
    (best, assignment) => Math.max(best, assignment.exit_time ?? assignment.entry_time),
    assignments[0].exit_time ?? assignments[0].entry_time,
  )

  return { start, end }
}

function App() {
  const [data, setData] = useState<DemoSnapshot | null>(null)
  const [error, setError] = useState<string | null>(null)
  const queryParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null
  const viewParam = queryParams?.get('view')
  const splashParam = queryParams?.get('splash')
  const kioskMode = queryParams?.get('kiosk') === '1'
  const splashRequested = splashParam === '1'
  const splashEnabled = !kioskMode && splashParam !== '0' && (splashRequested || !viewParam)
  const judgeAutoAdvance = queryParams?.get('autoplay') !== '0'
  const initialDialog =
    viewParam === 'brief' ||
    viewParam === 'equations' ||
    viewParam === 'history' ||
    viewParam === 'judge' ||
    viewParam === 'organization' ||
    viewParam === 'proof' ||
    viewParam === 'walkthrough'
      ? viewParam
      : kioskMode
        ? 'judge'
      : null
  const [activeDialog, setActiveDialog] = useState<DialogView>(initialDialog)
  const [activePanorama, setActivePanorama] = useState<PanoramaView>('yard')
  const [activeLandingTab, setActiveLandingTab] = useState<LandingTab>('overview')
  const [solutionTab, setSolutionTab] = useState<SolutionTab>('search')
  const [showSplash, setShowSplash] = useState(() => splashEnabled)

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
        <section className="surface hero-surface">
          <span className="surface-label">YardMind</span>
          <h1>Demo data is missing.</h1>
          <p className="surface-copy compact">
            Run <code>./scripts/open-demo.ps1 -NoOpen</code> from the repo root to regenerate{' '}
            <code>web/public/demo-data.json</code>, then reload this page.
          </p>
          <p className="error-text">Load error: {error}</p>
        </section>
      </main>
    )
  }

  if (showSplash) {
    return <SplashScreen data={data} ready={Boolean(data)} targetView={initialDialog} onDismiss={() => setShowSplash(false)} />
  }

  if (!data) {
    return (
      <main className="app-shell empty-state">
        <section className="surface hero-surface">
          <span className="surface-label">YardMind</span>
          <h1>Loading demo snapshot...</h1>
        </section>
      </main>
    )
  }

  const officialSummary = data.official.summary
  const acceptedMoves = data.search.history.filter((record) => record.accepted).length
  const feasibleMoves = data.search.history.filter((record) => record.candidate_feasible).length
  const feasibilityRate = data.search.history.length > 0 ? feasibleMoves / data.search.history.length : 0
  const movedBlocks = data.allocation_trace.filter((row) => row.moved).length
  const movedBlockShare = data.allocation_trace.length > 0 ? movedBlocks / data.allocation_trace.length : 0
  const dominantDestroy = getDominantLabel(data.search.history.map((record) => record.destroy_operator))
  const dominantRepair = getDominantLabel(data.search.history.map((record) => record.repair_operator))
  const proofVariant = officialSummary?.official_search ?? officialSummary?.native_constructive ?? null
  const officialObjectiveDelta = officialSummary
    && proofVariant
    ? proofVariant.objective - officialSummary.delegated_baseline.objective
    : 0
  const runtimeRatio = officialSummary
    && proofVariant
    ? officialSummary.delegated_baseline.runtime_seconds /
      Math.max(proofVariant.runtime_seconds, 1e-9)
    : 0
  const activeDevelopmentSolution = solutionTab === 'search' ? data.search_solution : data.constructive
  const developmentDeltaFromBaseline = activeDevelopmentSolution.objective_value - data.constructive.objective_value
  const landingOfficialVariant = officialSummary?.official_search ?? officialSummary?.native_constructive ?? officialSummary?.delegated_baseline ?? null
  const landingOfficialLabel = officialSummary?.official_search
    ? 'Official search replay'
    : officialSummary?.native_constructive
      ? 'Native constructive replay'
      : officialSummary?.delegated_baseline
        ? 'Delegated baseline replay'
        : 'Official replay'
  const landingOfficialDelta = officialSummary && landingOfficialVariant
    ? landingOfficialVariant.objective - officialSummary.delegated_baseline.objective
    : 0
  const officialAssignmentCount = landingOfficialVariant?.assignment_count ?? landingOfficialVariant?.assignments?.length ?? 0
  const officialBayCount = officialSummary?.bays.length ?? 0
  const developmentEvidence = data.report_evidence?.development ?? null
  const publicSampleEvidence = data.report_evidence?.official?.public_sample ?? null
  const proofCaseEvidence = data.report_evidence?.official?.proof_case ?? null
  const qualityCaseEvidence = data.report_evidence?.official?.quality_case ?? null
  const hiddenOverloadedBayEvidence = data.report_evidence?.official?.hidden_overloaded_bay ?? null
  const hiddenTightWindowEvidence = data.report_evidence?.official?.hidden_tight_window ?? null
  const developmentImprovementRate = developmentEvidence && developmentEvidence.runs > 0
    ? developmentEvidence.improved_runs / developmentEvidence.runs
    : null
  const proofCaseFeasibleRate = proofCaseEvidence && proofCaseEvidence.runs > 0
    ? proofCaseEvidence.search_feasible_runs / proofCaseEvidence.runs
    : null
  const qualityCaseDelta = qualityCaseEvidence?.search_vs_native_delta_mean ?? qualityCaseEvidence?.search_vs_delegated_delta_mean ?? null
  const hiddenOverloadedBayDelta = hiddenOverloadedBayEvidence?.search_vs_delegated_delta_mean ?? null
  const hiddenTightWindowDelta = hiddenTightWindowEvidence?.search_vs_delegated_delta_mean ?? null
  const progressSummary: DemoProgressSummary = {
    instance: officialSummary?.instance ?? data.instance_name,
    blockCount: data.block_count,
    searchLift: data.search.delta,
    objective: proofVariant?.objective ?? null,
    runtimeSeconds: proofVariant?.runtime_seconds ?? null,
    stage: proofVariant?.stage ?? null,
    status: proofVariant ? (proofVariant.feasible ? 'PASS' : 'FAIL') : 'Pending',
    statusTone: proofVariant ? (proofVariant.feasible ? 'good' : 'bad') : 'neutral',
  }
  const walkthroughLines: WalkthroughLine[] = [
    { kind: 'command', text: '$ algorithm(problem, timelimit)' },
    {
      kind: 'output',
      text: `Load ${officialSummary?.instance ?? data.instance_name}, parse ${data.block_count} blocks, and build the bay-time state.`,
    },
    { kind: 'command', text: '$ constructive phase' },
    {
      kind: 'output',
      text: `Construct a feasible baseline with objective ${data.constructive.objective_value.toFixed(4)} on the development proxy score.`,
    },
    { kind: 'command', text: '$ destroy / repair loop' },
    {
      kind: 'output',
      text: `Run ${data.search.iterations} iterations, accept ${acceptedMoves} moves, and keep the best incumbent at ${data.search_solution.objective_value.toFixed(4)}.`,
    },
    { kind: 'command', text: '$ official evaluator view' },
    {
      kind: 'output',
      text: officialSummary
        ? `Official search is ${proofVariant?.feasible ? 'PASS' : 'FAIL'} at stage ${proofVariant?.stage ?? 'N/A'} with objective ${proofVariant ? proofVariant.objective.toFixed(4) : 'N/A'}.`
        : 'Official comparison data is not available in this snapshot.',
    },
    {
      kind: 'note',
      text: 'The frontend is intentionally simple: equations, one active yard view, one active official replay, and full history only in a dialog.',
    },
  ]

  return (
    <main className="app-shell app-shell-landing">
      <div className="landing-shell-atmosphere" aria-hidden="true">
        <span className="landing-shell-orb landing-shell-orb-a" />
        <span className="landing-shell-orb landing-shell-orb-b" />
        <span className="landing-shell-grid-veil" />
      </div>
      <section className="landing-top-tabs" role="tablist" aria-label="Landing views">
        <button
          className={`landing-top-tab${activeLandingTab === 'overview' ? ' active' : ''}`}
          onClick={() => setActiveLandingTab('overview')}
          role="tab"
          aria-selected={activeLandingTab === 'overview'}
          type="button"
        >
          Landing Overview
        </button>
        <button
          className={`landing-top-tab${activeLandingTab === 'panorama' ? ' active' : ''}`}
          onClick={() => setActiveLandingTab('panorama')}
          role="tab"
          aria-selected={activeLandingTab === 'panorama'}
          type="button"
        >
          Data panorama
        </button>
        <button
          className={`landing-top-tab${activeLandingTab === 'development' ? ' active' : ''}`}
          onClick={() => setActiveLandingTab('development')}
          role="tab"
          aria-selected={activeLandingTab === 'development'}
          type="button"
        >
          Development layout
        </button>
        <button
          className={`landing-top-tab${activeLandingTab === 'replay' ? ' active' : ''}`}
          onClick={() => setActiveLandingTab('replay')}
          role="tab"
          aria-selected={activeLandingTab === 'replay'}
          type="button"
        >
          Replay
        </button>
        <button
          className={`landing-top-tab${activeLandingTab === 'analysis' ? ' active' : ''}`}
          onClick={() => setActiveLandingTab('analysis')}
          role="tab"
          aria-selected={activeLandingTab === 'analysis'}
          type="button"
        >
          Deep analysis
        </button>
      </section>

      {activeLandingTab === 'overview' ? (
      <>
      <DemoProgressStrip label="Landing progress" summary={progressSummary} />
      <section className="surface landing-command-surface">
        <div className="landing-command-atmosphere" aria-hidden="true">
          <span className="landing-command-orb landing-command-orb-a" />
          <span className="landing-command-orb landing-command-orb-b" />
          <span className="landing-command-grid-veil" />
        </div>
        <div className="landing-command-grid">
          <div className="landing-command-copy">
            <section className="landing-command-intro-box">
              <div className="landing-command-intro-grid">
                <div className="landing-command-intro-copy">
                  <span className="surface-label landing-command-label">YardMind Main Deck</span>
                  <h1>Integrated yard improvement with official verification.</h1>
                  <div className="action-row landing-command-actions">
                    <button className="action-button landing-hero-action landing-hero-action-primary" onClick={() => setActiveDialog('judge')} type="button">
                      Open presentation flow
                    </button>
                    <button className="action-button landing-hero-action" onClick={() => setActiveDialog('controls')} type="button">
                      Open demo controls
                    </button>
                    <button className="action-button landing-hero-action" onClick={() => setActiveDialog('proof')} type="button">
                      Open validation view
                    </button>
                  </div>
                </div>

                <div className="landing-command-intro-side">
                  <article className="report-card landing-command-card landing-command-card-hero">
                    <span className="surface-label">Status summary</span>
                    <h3>
                      {proofVariant
                        ? `${proofVariant.feasible ? 'PASS' : 'FAIL'} at stage ${proofVariant.stage}`
                        : 'Official proof unavailable'}
                    </h3>
                    <p className="surface-copy compact">
                      The current snapshot combines a {data.block_count}-block development layout, measured search lift of {formatDelta(data.search.delta)}, and an official result that remains {proofVariant?.feasible ? 'feasible' : 'auditable'} while {officialObjectiveDelta <= 0 ? 'improving on' : 'remaining close to'} the delegated baseline.
                    </p>
                  </article>
                  <div className="landing-command-signal-grid">
                    <article className="report-card landing-signal-card">
                      <span className="surface-label">Why it wins</span>
                      <h3>{formatDelta(data.search.delta)} development lift</h3>
                      <p className="surface-copy compact">Search repairs crowded neighborhoods instead of accepting the first feasible packing.</p>
                    </article>
                    <article className="report-card landing-signal-card">
                      <span className="surface-label">Why trust it</span>
                      <h3>{officialSummary ? formatDelta(officialObjectiveDelta) : 'N/A'} vs delegated</h3>
                      <p className="surface-copy compact">Replay, stage result, and validation details remain available as adjacent supporting views.</p>
                    </article>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </section>
      </>
      ) : null}

      {activeLandingTab === 'panorama' ? (
      <section className="surface landing-command-surface">
        <div className="landing-command-atmosphere" aria-hidden="true">
          <span className="landing-command-orb landing-command-orb-a" />
          <span className="landing-command-orb landing-command-orb-b" />
          <span className="landing-command-grid-veil" />
        </div>
        <section className="landing-panorama-shell" aria-label="Landing information panorama">
          <div className="landing-panorama-header">
            <div>
              <span className="surface-label">Data panorama</span>
              <h2>A compact view of the active system.</h2>
            </div>
          </div>
          <div className="landing-panorama-selector" role="tablist" aria-label="Panorama views">
            <button className={`landing-panorama-tab${activePanorama === 'yard' ? ' active' : ''}`} onClick={() => setActivePanorama('yard')} role="tab" aria-selected={activePanorama === 'yard'} type="button">
              Yard
            </button>
            <button className={`landing-panorama-tab${activePanorama === 'objective' ? ' active' : ''}`} onClick={() => setActivePanorama('objective')} role="tab" aria-selected={activePanorama === 'objective'} type="button">
              Objective
            </button>
            <button className={`landing-panorama-tab${activePanorama === 'search' ? ' active' : ''}`} onClick={() => setActivePanorama('search')} role="tab" aria-selected={activePanorama === 'search'} type="button">
              Search
            </button>
            <button className={`landing-panorama-tab${activePanorama === 'proof' ? ' active' : ''}`} onClick={() => setActivePanorama('proof')} role="tab" aria-selected={activePanorama === 'proof'} type="button">
              Validation
            </button>
            <button className={`landing-panorama-tab${activePanorama === 'judge' ? ' active' : ''}`} onClick={() => setActivePanorama('judge')} role="tab" aria-selected={activePanorama === 'judge'} type="button">
              Route
            </button>
          </div>
          <div className="landing-panorama-spotlight">
            {activePanorama === 'yard' ? (
            <article className="report-card landing-panorama-card landing-panorama-card-yard">
              <div className="landing-panorama-card-topline">
                <span className="surface-label">Panorama 01</span>
                <span className="landing-panorama-index">Yard</span>
              </div>
              <h3>Readable layout before numbers</h3>
              <p className="surface-copy compact">
                The active yard view emphasizes spatial readability while the search incumbent improves density only where congestion and retrieval risk remain controlled.
              </p>
              <div className="headline-strip muted-strip">
                <KpiPill label="Best score" value={data.search_solution.objective_value.toFixed(4)} tone={data.search.delta >= 0 ? 'good' : 'warn'} />
                <KpiPill label="Risk" value={data.search_solution.objective_breakdown.retrieval_risk_penalty.toFixed(2)} tone="neutral" />
                <KpiPill label="Congestion" value={data.search_solution.objective_breakdown.congestion_penalty.toFixed(2)} tone="neutral" />
              </div>
              <div className="action-row">
                <button className="action-button" onClick={() => setActiveDialog('organization')} type="button">
                  Open organization
                </button>
              </div>
            </article>
            ) : null}

            {activePanorama === 'objective' ? (
            <article className="report-card landing-panorama-card landing-panorama-card-objective">
              <div className="landing-panorama-card-topline">
                <span className="surface-label">Panorama 02</span>
                <span className="landing-panorama-index">Objective</span>
              </div>
              <h3>Two objective spaces, one solver story</h3>
              <p className="surface-copy compact">
                Development search rewards area use and penalizes lateness, retrieval risk, and congestion. The official checker then scores tardiness, bay imbalance, and preferred-bay loss.
              </p>
              <div className="landing-panorama-chip-row" aria-hidden="true">
                <span className="landing-panorama-chip">Area use</span>
                <span className="landing-panorama-chip">Lateness</span>
                <span className="landing-panorama-chip">Retrieval risk</span>
                <span className="landing-panorama-chip">Congestion</span>
                <span className="landing-panorama-chip">Bay imbalance</span>
                <span className="landing-panorama-chip">Preferred-bay loss</span>
              </div>
              <div className="headline-strip muted-strip">
                <KpiPill label="Official delta" value={officialSummary ? formatDelta(officialObjectiveDelta) : 'N/A'} tone={officialObjectiveDelta <= 0 ? 'good' : 'neutral'} />
                <KpiPill label="Runtime ratio" value={officialSummary ? `${runtimeRatio.toFixed(2)}x` : 'N/A'} />
              </div>
              <div className="action-row">
                <button className="action-button" onClick={() => setActiveDialog('equations')} type="button">
                  Open equations
                </button>
              </div>
            </article>
            ) : null}

            {activePanorama === 'search' ? (
            <article className="report-card landing-panorama-card landing-panorama-card-search">
              <div className="landing-panorama-card-topline">
                <span className="surface-label">Panorama 03</span>
                <span className="landing-panorama-index">Search</span>
              </div>
              <h3>Search behavior under time pressure</h3>
              <p className="surface-copy compact">
                The search loop remains visible through accepted repairs, feasibility rate, and the point at which the incumbent stops improving.
              </p>
              <div className="headline-strip muted-strip">
                <KpiPill label="Iterations" value={`${data.search.iterations}`} />
                <KpiPill label="Accepted" value={`${acceptedMoves}/${data.search.history.length}`} />
                <KpiPill label="Feasible share" value={`${(feasibilityRate * 100).toFixed(0)}%`} />
              </div>
              <div className="action-row">
                <button className="action-button" onClick={() => setActiveDialog('history')} type="button">
                  Open history
                </button>
                <button className="action-button" onClick={() => setActiveDialog('walkthrough')} type="button">
                  Open walkthrough
                </button>
              </div>
            </article>
            ) : null}

            {activePanorama === 'proof' ? (
            <article className="report-card landing-panorama-card landing-panorama-card-proof">
              <div className="landing-panorama-card-topline">
                <span className="surface-label">Panorama 04</span>
                <span className="landing-panorama-index">Validation</span>
              </div>
              <h3>Official validation in one glance</h3>
              <p className="surface-copy compact">
                Keep the released checker close at hand: pass or fail, stage reached, runtime, and the delta against the delegated baseline all stay visible before the replay opens fullscreen.
              </p>
              {officialSummary && proofVariant ? (
                <div className="landing-panorama-preview landing-panorama-proof-preview">
                  <div className="landing-panorama-preview-badge" aria-hidden="true">Replay snapshot</div>
                  <OfficialSolvePlayback
                    autoPlay={false}
                    assignments={proofVariant.assignments ?? []}
                    bays={officialSummary.bays}
                    interactive={false}
                    label="Official validation preview"
                    runtimeSeconds={proofVariant.runtime_seconds}
                  />
                </div>
              ) : null}
              <div className="headline-strip muted-strip">
                <KpiPill label="Status" value={proofVariant?.feasible ? 'PASS' : 'FAIL'} tone={proofVariant?.feasible ? 'good' : 'bad'} />
                <KpiPill label="Stage" value={proofVariant ? `${proofVariant.stage}` : 'N/A'} />
                <KpiPill label="Runtime" value={proofVariant ? formatCompactSeconds(proofVariant.runtime_seconds) : 'N/A'} />
                <KpiPill label="Delta" value={officialSummary ? formatDelta(officialObjectiveDelta) : 'N/A'} tone={officialObjectiveDelta <= 0 ? 'good' : 'warn'} />
              </div>
              <div className="action-row">
                <button className="action-button" onClick={() => setActiveDialog('proof')} type="button">
                  Open validation view
                </button>
              </div>
            </article>
            ) : null}

            {activePanorama === 'judge' ? (
            <article className="report-card landing-panorama-card landing-panorama-card-judge">
              <div className="landing-panorama-card-topline">
                <span className="surface-label">Panorama 05</span>
                <span className="landing-panorama-index">Route</span>
              </div>
              <h3>Presentation flow as the stitched summary</h3>
              <p className="surface-copy compact">
                This route consolidates the main sequence: organization first, equations when needed, validation for released-checker results, and replay for bay-time evidence.
              </p>
              <div className="landing-panorama-chip-row" aria-hidden="true">
                <span className="landing-panorama-chip">Organization</span>
                <span className="landing-panorama-chip">Equations</span>
                <span className="landing-panorama-chip">Validation</span>
                <span className="landing-panorama-chip">Replay</span>
                <span className="landing-panorama-chip">Brief</span>
              </div>
              <div className="action-row">
                <button className="action-button" onClick={() => setActiveDialog('brief')} type="button">
                  Open overview brief
                </button>
              </div>
            </article>
            ) : null}
          </div>
        </section>
      </section>
      ) : null}

      {activeLandingTab === 'development' ? (
      <section className="surface section-surface showcase-surface">
        <div className="section-header section-header-tight">
          <div>
            <h2>Read the yard before the score.</h2>
          </div>
          <SegmentedControl<SolutionTab>
            label="Development solution"
            options={[
              { label: 'Search incumbent', value: 'search' },
              { label: 'Constructive baseline', value: 'constructive' },
            ]}
            value={solutionTab}
            onChange={setSolutionTab}
          />
        </div>
        <div className="showcase-grid">
          <div className="showcase-stage showcase-stage-development">
            <div className="showcase-stage-header showcase-stage-header-development">
              <div>
                <span className="surface-label">Active yard state</span>
                <h3>{solutionTab === 'search' ? 'Search incumbent layout' : 'Constructive baseline layout'}</h3>
              </div>
              <p className="surface-copy compact showcase-caption">
                One large yard and one current answer keep the spatial state visible without duplicated comparison panels.
              </p>
            </div>
            <div className="showcase-stage-shell showcase-stage-shell-development showcase-yard-shell">
              <DevelopmentYard solution={activeDevelopmentSolution} yard={data.yard} scale={24} />
            </div>
          </div>
          <aside className="showcase-sidebar">
            <section className="report-card showcase-script-rail showcase-script-rail-development">
              <div>
                <span className="surface-label">Reading rail</span>
                <h3>Layout interpretation</h3>
              </div>
              <article className="showcase-summary-card showcase-script-node showcase-script-node-development">
                <span className="surface-label">Beat 01</span>
                <p className="surface-copy compact">
                  {solutionTab === 'search'
                    ? 'The search result reopens crowded neighborhoods so the final layout remains workable instead of merely denser.'
                    : 'The constructive result establishes feasibility while still revealing congestion and retrieval pressure.'}
                </p>
              </article>
              <article className="showcase-summary-card showcase-script-node showcase-script-node-development">
                <span className="surface-label">Beat 02</span>
                <p className="surface-copy compact">
                  Risk and congestion provide context for why preserved space can be preferable to uniform density.
                </p>
              </article>
              <article className="showcase-summary-card showcase-script-node showcase-script-node-development">
                <span className="surface-label">Beat 03</span>
                <p className="surface-copy compact">
                  The final arrangement preserves readable access, concentrates density where it is safe, and keeps the layout operationally interpretable.
                </p>
              </article>
            </section>
            <div className="showcase-metric-grid">
              <KpiPill label="Objective" value={activeDevelopmentSolution.objective_value.toFixed(4)} tone={developmentDeltaFromBaseline >= 0 ? 'good' : 'warn'} />
              <KpiPill label="Delta vs baseline" value={formatDelta(developmentDeltaFromBaseline)} tone={developmentDeltaFromBaseline >= 0 ? 'good' : 'warn'} />
              <KpiPill label="Risk" value={activeDevelopmentSolution.objective_breakdown.retrieval_risk_penalty.toFixed(2)} tone={activeDevelopmentSolution.objective_breakdown.retrieval_risk_penalty <= data.constructive.objective_breakdown.retrieval_risk_penalty ? 'good' : 'warn'} />
              <KpiPill label="Congestion" value={activeDevelopmentSolution.objective_breakdown.congestion_penalty.toFixed(2)} tone={activeDevelopmentSolution.objective_breakdown.congestion_penalty <= data.constructive.objective_breakdown.congestion_penalty ? 'good' : 'warn'} />
            </div>
          </aside>
        </div>
      </section>
      ) : null}

      {activeLandingTab === 'replay' ? (
      <section className="surface section-surface showcase-surface">
        <div className="section-header section-header-tight">
          <div>
            <span className="surface-label">Official solve replay</span>
          </div>
        </div>
        {officialSummary ? (
          <section className="report-card landing-official-info-box" aria-label="Official replay variants">
            <div className="landing-official-info-grid">
              <article className="landing-official-info-card">
                <span className="landing-official-info-icon landing-official-info-icon-search" aria-hidden="true">
                  <svg viewBox="0 0 32 32" focusable="false">
                    <circle cx="16" cy="16" r="11" />
                    <path d="M10 16h12M16 10v12" />
                  </svg>
                </span>
                <span className="surface-label">Official search</span>
                <p className="surface-copy compact">Our improved result under the official evaluator.</p>
              </article>
              <article className="landing-official-info-card">
                <span className="landing-official-info-icon landing-official-info-icon-native" aria-hidden="true">
                  <svg viewBox="0 0 32 32" focusable="false">
                    <rect x="7" y="7" width="18" height="18" rx="6" />
                    <path d="M10 18c2-4 4-6 6-6s4 2 6 6" />
                  </svg>
                </span>
                <span className="surface-label">Native constructive</span>
                <p className="surface-copy compact">Our base constructive result before search repair.</p>
              </article>
              <article className="landing-official-info-card">
                <span className="landing-official-info-icon landing-official-info-icon-baseline" aria-hidden="true">
                  <svg viewBox="0 0 32 32" focusable="false">
                    <path d="M8 22h16" />
                    <path d="M10 16h12" />
                    <path d="M12 10h8" />
                  </svg>
                </span>
                <span className="surface-label">Delegated baseline</span>
                <p className="surface-copy compact">The baseline reference we compare against.</p>
              </article>
            </div>
          </section>
        ) : null}
        {officialSummary && landingOfficialVariant ? (
          <>
            <div className="showcase-grid">
              <div className="showcase-stage showcase-stage-official">
                <div className="showcase-stage-header showcase-stage-header-official">
                  <div>
                    <span className="surface-label">Competition-facing replay</span>
                    <h3>{landingOfficialLabel}</h3>
                  </div>
                  <p className="surface-copy compact showcase-caption">
                    This released quality-case result contains {officialAssignmentCount} official assignments across {officialBayCount} bays, with the bay-time state showing where the search schedule separates from the delegated baseline.
                  </p>
                </div>
                <div className="showcase-stage-shell showcase-stage-shell-official showcase-replay-shell">
                  <div className="showcase-stage-marker showcase-stage-marker-official" aria-hidden="true">
                    <span className="showcase-stage-marker-pill">Validation lens</span>
                    <span className="showcase-stage-marker-copy">Bay-time evidence under the released checker</span>
                  </div>
                  <OfficialSolvePlayback
                    autoPlay={false}
                    assignments={landingOfficialVariant.assignments ?? []}
                    bays={officialSummary.bays}
                    interactive
                    label=""
                    runtimeSeconds={landingOfficialVariant.runtime_seconds}
                  />
                </div>
              </div>
              <aside className="showcase-sidebar">
                <article className="report-card showcase-summary-card replay-reference-card">
                  <div>
                    <span className="surface-label">Bay reference</span>
                    <h3>What one bay looks like</h3>
                  </div>
                  <img className="replay-reference-image" src={bayImage} alt="Bay reference illustration" />
                  <p className="surface-copy compact">
                    This reference image gives visual context for the work area shown in the replay, where each bay acts as a bounded shipyard workspace with its own geometry and timing.
                  </p>
                </article>
                <section className="report-card showcase-script-rail showcase-script-rail-official">
                  <div>
                    <span className="surface-label">Replay rail</span>
                    <h3>Replay summary</h3>
                  </div>
                  <article className="showcase-summary-card showcase-script-node showcase-script-node-official">
                    <span className="surface-label">Beat 01</span>
                    <p className="surface-copy compact">
                      The replay makes the sequence explicit: blocks enter, exit, and release bay space through a directly inspectable timeline.
                    </p>
                  </article>
                  <article className="showcase-summary-card showcase-script-node showcase-script-node-official">
                    <span className="surface-label">Beat 02</span>
                    <p className="surface-copy compact">
                      The key result indicators remain visible throughout the replay: feasibility, stage {landingOfficialVariant.stage}, runtime {formatCompactSeconds(landingOfficialVariant.runtime_seconds)}, and official objective delta {formatDelta(landingOfficialDelta)} versus the delegated baseline.
                    </p>
                  </article>
                  <article className="showcase-summary-card showcase-script-node showcase-script-node-official">
                    <span className="surface-label">Beat 03</span>
                    <p className="surface-copy compact">
                      On {officialSummary.instance}, official search is {landingOfficialVariant.feasible ? 'feasible' : 'not feasible'}, reaches stage {landingOfficialVariant.stage}, and {landingOfficialDelta <= 0 ? 'improves the delegated baseline by' : 'trails the delegated baseline by'} {formatDelta(landingOfficialDelta)} under the released checker.
                    </p>
                  </article>
                </section>
                <article className="report-card showcase-summary-card replay-close-card">
                  <span className="surface-label">Replay takeaway</span>
                  <p className="surface-copy compact">
                    This replay is not a storyboard mockup. It is the released quality-case solution that stays {landingOfficialVariant.feasible ? 'feasible' : 'infeasible'}, completes in {formatCompactSeconds(landingOfficialVariant.runtime_seconds)}, and improves the delegated baseline by {formatDelta(landingOfficialDelta)}.
                  </p>
                </article>
              </aside>
            </div>
          </>
        ) : (
          <p className="surface-copy compact">{data.official.error ?? 'Official comparison unavailable in this snapshot.'}</p>
        )}
      </section>
      ) : null}

      {activeLandingTab === 'analysis' ? (
      <section className="surface section-surface analysis-surface">
        <div className="analysis-shell">
          <section className="report-card analysis-hero">
            <div className="analysis-hero-copy">
              <span className="surface-label">Deep analysis</span>
              <h2>How YardMind solves the OGC 2026 shipyard puzzle.</h2>
              <p className="surface-copy">
                The OGC 2026 problem couples bay assignment, geometry, orientation, and timing in one decision process. This live snapshot keeps the bay-time story readable, while the released official checker remains the source of truth for the full geometric and operational constraints behind each placement.
              </p>
            </div>
            <div className="headline-strip muted-strip analysis-kpi-strip">
              <KpiPill label="Blocks" value={`${data.block_count}`} />
              <KpiPill label="Iterations" value={`${data.search.iterations}`} />
              <KpiPill label="Feasible share" value={formatPercent(feasibilityRate)} tone={feasibilityRate >= 0.8 ? 'good' : 'warn'} />
              <KpiPill label="Moved blocks" value={`${movedBlocks}/${data.allocation_trace.length}`} tone={movedBlockShare > 0 ? 'good' : 'neutral'} />
              <KpiPill label="Official status" value={proofVariant ? (proofVariant.feasible ? 'PASS' : 'FAIL') : 'Pending'} tone={proofVariant ? (proofVariant.feasible ? 'good' : 'bad') : 'neutral'} />
            </div>
          </section>

          <div className="analysis-grid">
            <section className="report-card analysis-problem-card">
              <div className="analysis-section-heading">
                <span className="surface-label">Problem-to-solver map</span>
                <h3>The four official decisions and where we handle them</h3>
                <p className="surface-copy compact">
                  This section maps the product directly to the competition problem: not just where blocks fit, but which bay they use, when they move, and how that plan survives the released evaluator.
                </p>
              </div>
              <div className="analysis-decision-grid">
                <article className="analysis-decision-card">
                  <span className="analysis-card-index">01</span>
                  <span className="surface-label">Bay assignment</span>
                  <h3>Choose the bay without losing balance.</h3>
                  <p className="surface-copy compact">
                    We do not treat bay choice as a cosmetic label. The solver uses it to control congestion early and then checks the official balance and preferred-bay terms during validation.
                  </p>
                </article>
                <article className="analysis-decision-card">
                  <span className="analysis-card-index">02</span>
                  <span className="surface-label">Placement and orientation</span>
                  <h3>Validate full geometry, then show the readable abstraction.</h3>
                  <p className="surface-copy compact">
                    The constructive phase builds a collision-free footprint, then search reopens only crowded neighborhoods. The official problem is polygon-and-layer based with explicit orientation choices; the live replay compresses those validated placements into readable bay cards so the movement story stays legible. In this snapshot, {movedBlocks === 0 ? 'the constructive arrangement already aligned with the target structure.' : `${movedBlocks} blocks were repositioned to improve access or reduce conflict pressure.`}
                  </p>
                </article>
                <article className="analysis-decision-card">
                  <span className="analysis-card-index">03</span>
                  <span className="surface-label">Entry and exit timing</span>
                  <h3>Schedule movement, not just occupancy.</h3>
                  <p className="surface-copy compact">
                    Replay and validation keep ENTRY and EXIT visible because the challenge is bay-time feasibility. The solver has to leave enough crane-access structure for blocks to enter and leave without interference.
                  </p>
                </article>
                <article className="analysis-decision-card">
                  <span className="analysis-card-index">04</span>
                  <span className="surface-label">Objective tradeoff</span>
                  <h3>Optimize a proxy, then verify the official score.</h3>
                  <p className="surface-copy compact">
                    Development search rewards area use and penalizes lateness, retrieval risk, and congestion. The released evaluator then confirms the real target: tardiness, bay imbalance, and preferred-bay loss.
                  </p>
                </article>
              </div>
            </section>

            <aside className="analysis-sidebar">
              <section className="report-card analysis-pipeline-card">
                <div className="analysis-section-heading">
                  <span className="surface-label">Algorithm pipeline</span>
                  <h3>Feasible first, selective repair second</h3>
                </div>
                <div className="analysis-stage-list">
                  <article className="analysis-stage-card">
                    <div className="analysis-stage-topline">
                      <span className="analysis-stage-index">Stage 1</span>
                      <span className="surface-label">Constructive seed</span>
                    </div>
                    <p className="surface-copy compact">
                      The pipeline starts from a complete yard state with objective {data.constructive.objective_value.toFixed(4)} so a feasible incumbent exists before neighborhood search begins.
                    </p>
                  </article>
                  <article className="analysis-stage-card">
                    <div className="analysis-stage-topline">
                      <span className="analysis-stage-index">Stage 2</span>
                      <span className="surface-label">Destroy / repair loop</span>
                    </div>
                    <p className="surface-copy compact">
                      Search runs {data.search.iterations} iterations, most often destroys with <strong>{dominantDestroy}</strong> and repairs with <strong>{dominantRepair}</strong>, keeps feasibility on {formatPercent(feasibilityRate)} of candidates, and accepts {acceptedMoves} incumbent change{acceptedMoves === 1 ? '' : 's'}.
                    </p>
                  </article>
                  <article className="analysis-stage-card">
                    <div className="analysis-stage-topline">
                      <span className="analysis-stage-index">Stage 3</span>
                      <span className="surface-label">Official validation</span>
                    </div>
                    <p className="surface-copy compact">
                      The final answer is validated by the released evaluator. In this snapshot, {officialSummary?.instance ?? 'the official view'} is {proofVariant ? `${proofVariant.feasible ? 'PASS' : 'FAIL'} at stage ${proofVariant.stage}` : 'pending'}, with runtime {proofVariant ? formatCompactSeconds(proofVariant.runtime_seconds) : 'n/a'} and official objective delta {officialSummary ? formatDelta(officialObjectiveDelta) : 'n/a'} versus delegated.
                    </p>
                  </article>
                  <article className="analysis-stage-card">
                    <div className="analysis-stage-topline">
                      <span className="analysis-stage-index">Stage 4</span>
                      <span className="surface-label">Presentation abstraction</span>
                    </div>
                    <p className="surface-copy compact">
                      The frontend intentionally renders the official result as simplified bay rectangles with ENTRY and EXIT timing. That abstraction is for explanation only; orientation, layer overlap, bay containment, and crane-feasibility remain enforced by the official evaluator rather than approximated in the replay surface.
                    </p>
                  </article>
                </div>
                <div className="action-row analysis-action-row">
                  <button className="action-button" onClick={() => setActiveDialog('equations')} type="button">
                    Open equations
                  </button>
                  <button className="action-button" onClick={() => setActiveDialog('history')} type="button">
                    Open history
                  </button>
                  <button className="action-button" onClick={() => setActiveDialog('proof')} type="button">
                    Open validation view
                  </button>
                </div>
              </section>
            </aside>
          </div>

          <section className="report-card analysis-evidence-shell">
            <div className="analysis-section-heading">
              <span className="surface-label">Benchmark evidence</span>
              <h3>Why this remains credible beyond a static demo layout</h3>
              <p className="surface-copy compact">
                These cards summarize the repeated-run evidence bundled into the frontend snapshot, making robustness and benchmark behavior visible without opening raw logs.
              </p>
            </div>
            <div className="analysis-evidence-grid">
              <article className="analysis-evidence-card">
                <span className="surface-label">Development runs</span>
                <h3>{developmentEvidence ? `${developmentEvidence.improved_runs}/${developmentEvidence.runs}` : 'n/a'} runs improved</h3>
                <div className="headline-strip muted-strip">
                  <KpiPill label="Constructive mean" value={developmentEvidence ? developmentEvidence.constructive_mean.toFixed(4) : 'n/a'} />
                  <KpiPill label="Search mean" value={developmentEvidence ? developmentEvidence.search_mean.toFixed(4) : 'n/a'} tone={developmentEvidence && developmentEvidence.search_mean >= developmentEvidence.constructive_mean ? 'good' : 'neutral'} />
                </div>
                <p className="surface-copy compact">
                  {developmentEvidence
                    ? `Across ${developmentEvidence.runs} development runs, search improved the constructive seed in ${formatPercent(developmentImprovementRate ?? 0)} of runs and reached a best score of ${developmentEvidence.search_best.toFixed(4)}.`
                    : 'Repeated development-run evidence is not available in this snapshot.'}
                </p>
              </article>
              <article className="analysis-evidence-card">
                <span className="surface-label">Proof-case official evidence</span>
                <h3>{proofCaseEvidence ? formatOptionalDelta(proofCaseEvidence.search_vs_delegated_delta_mean) : 'n/a'} vs delegated</h3>
                <div className="headline-strip muted-strip">
                  <KpiPill label="Search feasible" value={proofCaseEvidence ? `${proofCaseEvidence.search_feasible_runs}/${proofCaseEvidence.runs}` : 'n/a'} tone={proofCaseEvidence && proofCaseEvidence.search_feasible_runs === proofCaseEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Feasible rate" value={proofCaseEvidence ? formatPercent(proofCaseFeasibleRate ?? 0) : 'n/a'} tone={proofCaseEvidence && proofCaseEvidence.search_feasible_runs === proofCaseEvidence.runs ? 'good' : 'warn'} />
                </div>
                <p className="surface-copy compact">
                  {proofCaseEvidence
                    ? `On the harder proof instance, official search stays feasible in ${proofCaseEvidence.search_feasible_runs} of ${proofCaseEvidence.runs} runs and improves the delegated baseline from ${formatOptionalFixed(proofCaseEvidence.delegated_objective_mean)} to ${formatOptionalFixed(proofCaseEvidence.search_objective_mean)}, a mean delta of ${formatOptionalDelta(proofCaseEvidence.search_vs_delegated_delta_mean)}.`
                    : 'Proof-case official evidence is not available in this snapshot.'}
                </p>
              </article>
              <article className="analysis-evidence-card">
                <span className="surface-label">Quality-case official evidence</span>
                <h3>{qualityCaseDelta === null ? 'n/a' : formatDelta(qualityCaseDelta)} mean delta</h3>
                <div className="headline-strip muted-strip">
                  <KpiPill label="Search mean" value={qualityCaseEvidence ? formatOptionalFixed(qualityCaseEvidence.search_objective_mean) : 'n/a'} />
                  <KpiPill label="Public runtime" value={publicSampleEvidence ? formatOptionalSeconds(publicSampleEvidence.search_runtime_mean) : 'n/a'} />
                </div>
                <p className="surface-copy compact">
                  {qualityCaseEvidence
                    ? `On the released quality case, official search moves the mean objective from ${formatOptionalFixed(qualityCaseEvidence.delegated_objective_mean)} to ${formatOptionalFixed(qualityCaseEvidence.search_objective_mean)} and beats both delegated and native constructive by ${formatOptionalDelta(qualityCaseEvidence.search_vs_delegated_delta_mean)}.`
                    : 'Quality-case official evidence is not available in this snapshot.'}
                </p>
              </article>
              <article className="analysis-evidence-card">
                <span className="surface-label">Internal robustness checks</span>
                <h3>{hiddenOverloadedBayDelta !== null && hiddenTightWindowDelta !== null ? `${formatDelta(hiddenOverloadedBayDelta)} / ${formatDelta(hiddenTightWindowDelta)}` : 'n/a'} hidden-case deltas</h3>
                <div className="headline-strip muted-strip">
                  <KpiPill label="Overloaded bay" value={hiddenOverloadedBayEvidence ? formatOptionalDelta(hiddenOverloadedBayEvidence.search_vs_delegated_delta_mean) : 'n/a'} tone={hiddenOverloadedBayEvidence && hiddenOverloadedBayEvidence.search_vs_delegated_delta_mean !== null && hiddenOverloadedBayEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'neutral'} />
                  <KpiPill label="Tight window" value={hiddenTightWindowEvidence ? formatOptionalDelta(hiddenTightWindowEvidence.search_vs_delegated_delta_mean) : 'n/a'} tone={hiddenTightWindowEvidence && hiddenTightWindowEvidence.search_vs_delegated_delta_mean !== null && hiddenTightWindowEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'neutral'} />
                </div>
                <p className="surface-copy compact">
                  {hiddenOverloadedBayEvidence && hiddenTightWindowEvidence
                    ? `Internal official-format stress cases show the same pattern as the released benchmarks: the overloaded-bay family improves from ${formatOptionalFixed(hiddenOverloadedBayEvidence.delegated_objective_mean)} to ${formatOptionalFixed(hiddenOverloadedBayEvidence.search_objective_mean)}, while the tight-window cascade improves from ${formatOptionalFixed(hiddenTightWindowEvidence.delegated_objective_mean)} to ${formatOptionalFixed(hiddenTightWindowEvidence.search_objective_mean)} and leaves native constructive infeasible in ${hiddenTightWindowEvidence.runs - hiddenTightWindowEvidence.native_feasible_runs} of ${hiddenTightWindowEvidence.runs} runs.`
                    : 'Internal hidden-case evidence is not available in this snapshot.'}
                </p>
              </article>
            </div>
          </section>
        </div>
      </section>
      ) : null}

      <FullscreenDialog
        open={activeDialog === 'brief'}
        title="Overview brief"
        subtitle="Concise project summary and baseline comparison"
        onClose={() => setActiveDialog(null)}
      >
        <JudgeBriefDialogContent
          developmentDelta={data.search.delta}
          officialObjectiveDelta={officialObjectiveDelta}
          proofVariant={proofVariant}
          progressSummary={progressSummary}
          runtimeRatio={runtimeRatio}
        />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'controls'}
        title="Demo controls"
        subtitle="Access validation, organization, presentation, and trace surfaces as needed"
        onClose={() => setActiveDialog(null)}
      >
        <DemoControlsDialogContent onSelect={setActiveDialog} />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'judge'}
        title="Presentation flow"
        subtitle="A structured sequence across organization, equations, and validation"
        onClose={() => setActiveDialog(null)}
        hideClose={kioskMode}
      >
        <JudgeModeDialogContent
          autoAdvanceDefault={judgeAutoAdvance}
          officialSummary={officialSummary}
          officialObjectiveDelta={officialObjectiveDelta}
          proofVariant={proofVariant}
          progressSummary={progressSummary}
          reportEvidence={data.report_evidence}
          runtimeRatio={runtimeRatio}
        />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'equations'}
        title="Full equations"
        subtitle="Development proxy and official competition objective"
        onClose={() => setActiveDialog(null)}
      >
        <EquationDialogContent data={data} officialSummary={officialSummary} />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'history'}
        title="Complete search history"
        subtitle="All iterations from the current snapshot"
        onClose={() => setActiveDialog(null)}
      >
        <HistoryDialogContent history={data.search.history} />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'organization'}
        title="Space organization view"
        subtitle="How the algorithm structures the yard instead of only filling it"
        onClose={() => setActiveDialog(null)}
      >
        <SpaceOrganizationDialogContent
          allocationTrace={data.allocation_trace}
          progressSummary={progressSummary}
          solution={data.search_solution}
          yard={data.yard}
        />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'proof'}
        title="Validation view"
        subtitle="Official evaluator result, objective terms, and solve replay"
        onClose={() => setActiveDialog(null)}
      >
        <ProofDialogContent
          officialSummary={officialSummary}
          runtimeRatio={runtimeRatio}
          officialObjectiveDelta={officialObjectiveDelta}
          proofVariant={proofVariant}
          progressSummary={progressSummary}
        />
      </FullscreenDialog>

      <FullscreenDialog
        open={activeDialog === 'walkthrough'}
        title="Algorithm walkthrough"
        subtitle="Structured execution summary"
        onClose={() => setActiveDialog(null)}
      >
        <WalkthroughDialogContent lines={walkthroughLines} />
      </FullscreenDialog>
    </main>
  )
}

function SplashScreen({
  data,
  ready,
  targetView,
  onDismiss,
}: {
  data: DemoSnapshot | null
  ready: boolean
  targetView: DialogView
  onDismiss: () => void
}) {
  const [phase, setPhase] = useState<'voyage' | 'reveal' | 'closing'>('voyage')
  const [isClosing, setIsClosing] = useState(false)
  const splashOfficialSummary = data?.official.summary ?? null
  const splashProofVariant = splashOfficialSummary?.official_search ?? splashOfficialSummary?.native_constructive ?? null
  const splashVariantLabel = splashOfficialSummary ? 'Official search' : 'Development search'
  const splashInstance = splashOfficialSummary?.instance ?? data?.instance_name ?? 'Preparing live snapshot'
  const splashBlocks = data?.block_count ?? 0
  const splashDeltaValue = data?.search.delta ?? null
  const splashObjective = splashProofVariant?.objective ?? data?.search_solution.objective_value ?? 0
  const animatedBlocks = useAnimatedNumber(splashBlocks, ready)
  const animatedLift = useAnimatedNumber(Math.abs(splashDeltaValue ?? 0), ready)
  const animatedObjective = useAnimatedNumber(splashObjective, ready, 1300)
  const animatedStage = useAnimatedNumber(splashProofVariant?.stage ?? 0, ready, 900)
  const splashTargetLabel = targetView ? splashTargetLabels[targetView] : 'landing overview'
  const splashPanoramaItems = ready
    ? [
        { label: 'Scenario', value: splashInstance, note: 'The active instance currently driving the live demo' },
        { label: 'Load', value: `${Math.round(animatedBlocks)}`, note: 'How many shipyard blocks this snapshot is organizing' },
        {
          label: 'Search gain',
          value: splashDeltaValue !== null ? `${splashDeltaValue >= 0 ? '+' : '-'}${animatedLift.toFixed(4)}` : 'Loading',
          note: 'Measured improvement of search over the development baseline',
        },
        {
          label: splashProofVariant ? 'Validation score' : 'Best score',
          value: ready ? animatedObjective.toFixed(4) : 'Loading',
          note: splashProofVariant ? 'Released-checker score on the active validation path' : 'Development score on the current yard layout',
        },
        {
          label: splashProofVariant ? 'Validation stage' : 'Status',
          value: splashProofVariant ? `${Math.round(animatedStage)}` : 'Live',
          note: splashProofVariant ? 'Stage reached by the official evaluation path' : 'Development snapshot ready',
        },
        { label: 'Next view', value: splashTargetLabel, note: 'The first surface shown after the intro' },
      ]
    : [
        { label: 'Scenario', value: 'Preparing', note: 'Loading the current yard snapshot' },
        { label: 'Load', value: '0', note: 'Waiting for live block data' },
        { label: 'Search gain', value: 'Loading', note: 'The development delta appears when data is ready' },
        { label: 'Validation score', value: 'Loading', note: 'The official or development score appears when ready' },
        { label: 'Validation stage', value: '...', note: 'The official stage appears when the summary loads' },
        { label: 'Next view', value: splashTargetLabel, note: 'The intro leads into the same first surface' },
      ]
  const splashStoryBeats = ready
    ? [
        {
          label: 'Beat 01',
          title: 'Layout first',
          copy: 'The opening frame emphasizes layout structure: access remains readable, congestion remains visible, and density is treated as a controlled tradeoff.',
        },
        {
          label: 'Beat 02',
          title: 'Validation context',
          copy: splashProofVariant
            ? `The official checker remains visible: ${splashProofVariant.feasible ? 'PASS' : 'FAIL'} at stage ${splashProofVariant.stage}, with score and runtime shown together instead of collapsed into one number.`
            : 'The validation view keeps the official checker, runtime, and objective terms visible together.',
        },
        {
          label: 'Beat 03',
          title: 'Replay context',
          copy: 'The replay closes the sequence with bay-time changes, block movement, and the comparison against the delegated baseline.',
        },
      ]
    : [
        {
          label: 'Beat 01',
          title: 'Layout first',
          copy: 'The intro opens with the spatial layout before equations or replay.',
        },
        {
          label: 'Beat 02',
          title: 'Validation context',
          copy: 'The validation view loads the official checker, objective terms, and runtime together.',
        },
        {
          label: 'Beat 03',
          title: 'Replay context',
          copy: 'The replay closes the demo with visible bay-time evidence instead of another wall of text.',
        },
      ]
  const splashTone: 'neutral' | 'good' | 'warn' | 'bad' = splashProofVariant
    ? splashProofVariant.feasible
      ? splashOfficialSummary && splashProofVariant.objective <= splashOfficialSummary.delegated_baseline.objective
        ? 'good'
        : 'warn'
      : 'bad'
    : splashDeltaValue === null
      ? 'neutral'
      : splashDeltaValue >= 0
        ? 'good'
        : 'warn'
  const splashStatus = splashProofVariant
    ? `${splashVariantLabel} ${splashProofVariant.feasible ? 'PASS' : 'FAIL'} · stage ${splashProofVariant.stage}`
    : ready
      ? 'Snapshot ready'
      : 'Loading data'
  const splashTargetStatus = targetView ? `Opening ${splashTargetLabel}` : 'Opening landing overview'

  useEffect(() => {
    if (isClosing) {
      return
    }

    const revealTimer = window.setTimeout(() => setPhase('reveal'), 1650)

    return () => {
      window.clearTimeout(revealTimer)
    }
  }, [isClosing])

  useEffect(() => {
    if (!isClosing) {
      return
    }

    const timer = window.setTimeout(() => onDismiss(), 520)
    return () => window.clearTimeout(timer)
  }, [isClosing, onDismiss])

  function beginDismiss() {
    setPhase('closing')
    setIsClosing(true)
  }

  return (
    <main className={`splash-screen splash-theme-${splashTone} splash-phase-${phase}${isClosing ? ' closing' : ''}`} role="presentation">
      <div className="splash-atmosphere" aria-hidden="true">
        <div className="splash-orb splash-orb-a" />
        <div className="splash-orb splash-orb-b" />
        <div className="splash-grid" />
      </div>

      <section className="splash-panel">
        <div className="splash-badge-row">
          <span className="surface-label">YardMind Live Demo</span>
          <span className={`splash-status${ready ? ' ready' : ''}`}>{ready ? splashStatus : 'Loading data'}</span>
          <span className="splash-target-pill">{splashTargetStatus}</span>
        </div>

        <div className="splash-hero">
          <div>
            <p className="splash-kicker">{ready ? `${splashInstance} · ${splashBlocks} blocks live` : 'Port arrival. Yard intelligence. Verified optimization.'}</p>
            <h1 className="splash-title">
              <span>Yard</span>
              <span>Mind</span>
            </h1>
            <p className="splash-copy">
              {ready
                ? `YardMind is a feasibility-first retrieval-aware solver: the development objective rewards area use while penalizing lateness, retrieval risk, and congestion, while the official path checks tardiness, bay imbalance, and preferred-bay loss. Next surface: ${splashTargetLabel}.`
                : 'A cinematic view of ship flow, yard organization, and official replay before the technical surfaces appear.'}
            </p>
          </div>

          <div className="splash-stage" aria-hidden="true">
            <img className="splash-stage-image" src={shipyardImage} alt="" />
            <div className="splash-beam" />
            <div className="splash-waterline" />
            <div className="splash-ship">
              <span className="splash-keel-stripe" />
              <span className="splash-stern" />
              <span className="splash-deck" />
              <span className="splash-deckhouse" />
              <span className="splash-funnel" />
              <span className="splash-mast" />
              <span className="splash-bridge" />
              <span className="splash-bridge-window splash-bridge-window-a" />
              <span className="splash-bridge-window splash-bridge-window-b" />
              <span className="splash-container splash-container-a" />
              <span className="splash-container splash-container-b" />
              <span className="splash-container splash-container-c" />
              <span className="splash-container splash-container-d" />
              <span className="splash-container splash-container-e" />
              <span className="splash-container splash-container-f" />
              <span className="splash-bow" />
              <span className="splash-hull" />
            </div>
            <div className="splash-yard-glow">
              <span className="splash-yard-stack splash-yard-stack-a" />
              <span className="splash-yard-stack splash-yard-stack-b" />
              <span className="splash-yard-stack splash-yard-stack-c" />
            </div>
            <div className="splash-flow-line splash-flow-line-a" />
            <div className="splash-flow-line splash-flow-line-b" />
            <div className="splash-reveal-shell">
              <div className="splash-replay-frame">
                <span className="splash-replay-rail splash-replay-rail-a" />
                <span className="splash-replay-rail splash-replay-rail-b" />
                <span className="splash-replay-rail splash-replay-rail-c" />
                <span className="splash-replay-head splash-replay-head-a" />
                <span className="splash-replay-head splash-replay-head-b" />
              </div>
              <div className="splash-yard-grid-mini">
                <span className="splash-yard-node splash-yard-node-a" />
                <span className="splash-yard-node splash-yard-node-b" />
                <span className="splash-yard-node splash-yard-node-c" />
                <span className="splash-yard-node splash-yard-node-d" />
              </div>
            </div>
          </div>
        </div>

        <div className="splash-footer">
          <div className="headline-strip muted-strip splash-footer-strip" aria-hidden="true">
            <KpiPill label="Blocks" value={ready ? `${Math.round(animatedBlocks)}` : '0'} />
            <KpiPill
              label="Search lift"
              value={ready && splashDeltaValue !== null ? `${splashDeltaValue >= 0 ? '+' : '-'}${animatedLift.toFixed(4)}` : 'Loading'}
              tone={ready && splashDeltaValue !== null ? splashDeltaValue >= 0 ? 'good' : 'warn' : 'neutral'}
            />
            <KpiPill
              label={splashProofVariant ? 'Objective' : 'Best score'}
              value={ready ? animatedObjective.toFixed(4) : 'Loading'}
            />
            <KpiPill
              label={splashProofVariant ? 'Stage' : 'Status'}
              value={ready ? splashProofVariant ? `${Math.round(animatedStage)}` : 'Live' : '...'}
              tone={splashProofVariant ? splashProofVariant.feasible ? 'good' : 'bad' : 'neutral'}
            />
          </div>
          <button className="action-button splash-enter-button" onClick={beginDismiss} type="button">
            {ready ? `Start ${splashTargetLabel}` : 'Start demo'}
          </button>
        </div>

        <section className="splash-panorama-shell" aria-label="Splash value panorama">
          <div className="splash-panorama-heading">
            <span className="surface-label">Data pulse</span>
          </div>
          <div className="splash-panorama-window">
            <div className="splash-panorama-track">
              {[...splashPanoramaItems, ...splashPanoramaItems].map((item, index) => (
                <article className="splash-panorama-card" key={`${item.label}-${index}`} aria-hidden={index >= splashPanoramaItems.length}>
                  <span className="surface-label">{item.label}</span>
                  <strong>{item.value}</strong>
                  <p className="surface-copy compact">{item.note}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="splash-story-shell" aria-label="Splash presentation story rail">
          <div className="splash-story-heading">
            <span className="surface-label">Presentation route</span>
            <h3>Core sequence</h3>
          </div>
          <div className="splash-story-grid">
            {splashStoryBeats.map((beat) => (
              <article className="splash-story-card" key={beat.label}>
                <span className="surface-label">{beat.label}</span>
                <h3>{beat.title}</h3>
                <p className="surface-copy compact">{beat.copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="splash-objective-shell" aria-label="Splash official objective strip">
          <div className="splash-objective-heading">
            <span className="surface-label">Official objective</span>
            <h3>Released score terms remain visible in the intro.</h3>
          </div>
          <div className="splash-objective-grid">
            <div className="splash-objective-formula-card">
              <OfficialObjectiveFormula compact />
            </div>
            <div className="headline-strip muted-strip splash-objective-strip">
              <KpiPill label="Z1 tardiness" value={splashProofVariant ? splashProofVariant.obj1.toFixed(4) : 'Loading'} />
              <KpiPill label="Z2 imbalance" value={splashProofVariant ? splashProofVariant.obj2.toFixed(4) : 'Loading'} />
              <KpiPill label="Z3 preference loss" value={splashProofVariant ? splashProofVariant.obj3.toFixed(4) : 'Loading'} />
            </div>
          </div>
        </section>
      </section>
    </main>
  )
}

function JudgeBriefDialogContent({
  developmentDelta,
  officialObjectiveDelta,
  proofVariant,
  progressSummary,
  runtimeRatio,
}: {
  developmentDelta: number
  officialObjectiveDelta: number
  proofVariant: OfficialVariant | null
  progressSummary: DemoProgressSummary
  runtimeRatio: number
}) {
  return (
    <div className="dialog-stack">
      <DemoProgressStrip label="Demo progress" summary={progressSummary} />
      <section className="dialog-card">
        <span className="surface-label">Project summary</span>
        <h3>Core project statements</h3>
        <div className="report-grid compact-report-grid">
          <article className="report-card compact-launch-card">
            <span className="surface-label">Point 1</span>
            <h3>Baseline comparison</h3>
            <p className="surface-copy compact">
              We do not stop at baseline feasibility. The demo shows measured search lift of {formatDelta(developmentDelta)} on the development proxy and {formatDelta(officialObjectiveDelta)} versus the delegated baseline on the official objective.
            </p>
          </article>
          <article className="report-card compact-launch-card">
            <span className="surface-label">Point 2</span>
            <h3>Verification surface</h3>
            <p className="surface-copy compact">
              The validation result remains visible: {proofVariant ? `${proofVariant.feasible ? 'PASS' : 'FAIL'} at stage ${proofVariant.stage}` : 'the official checker view is ready'}, with replay, runtime, and term breakdown shown directly rather than hidden behind one aggregate score.
            </p>
          </article>
          <article className="report-card compact-launch-card">
            <span className="surface-label">Point 3</span>
            <h3>Technical focus</h3>
            <p className="surface-copy compact">
              YardMind is retrieval-aware. It evaluates placements by what they do to future moves, then improves incumbents with local repair neighborhoods rather than treating packing as a one-shot greedy fill.
            </p>
          </article>
          <article className="report-card compact-launch-card">
            <span className="surface-label">Point 4</span>
            <h3>Time-limited behavior</h3>
            <p className="surface-copy compact">
              Yes. The solver is anytime: it produces a feasible answer first, then improves it. The current snapshot runs at {proofVariant ? `${runtimeRatio.toFixed(2)}x` : 'N/A'} the delegated runtime ratio while keeping the official validation result auditable.
            </p>
          </article>
        </div>
      </section>
    </div>
  )
}

function KpiPill({ label, value, tone = 'neutral' }: { label: string; value: string; tone?: 'neutral' | 'good' | 'warn' | 'bad' }) {
  return (
    <article className={`kpi-pill kpi-pill-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function DemoProgressStrip({ label, summary }: { label: string; summary: DemoProgressSummary }) {
  return (
    <section className="dialog-card scene-progress-shell">
      <div className="headline-strip muted-strip splash-footer-strip scene-progress-strip">
        <div className="scene-progress-lead">
          <span className="surface-label">{label}</span>
          <p className="surface-copy compact">Persistent status across the active views.</p>
        </div>
        <KpiPill label="Instance" value={summary.instance} />
        <KpiPill label="Blocks" value={`${summary.blockCount}`} />
        <KpiPill label="Search lift" value={formatDelta(summary.searchLift)} tone={summary.searchLift >= 0 ? 'good' : 'warn'} />
        <KpiPill label="Objective" value={summary.objective === null ? 'Pending' : summary.objective.toFixed(4)} />
        <KpiPill label="Runtime" value={summary.runtimeSeconds === null ? 'Pending' : formatCompactSeconds(summary.runtimeSeconds)} />
        <KpiPill label="Stage" value={summary.stage === null ? 'Pending' : `${summary.stage}`} />
        <KpiPill label="Status" value={summary.status} tone={summary.statusTone ?? 'neutral'} />
      </div>
    </section>
  )
}

function JudgeEvidenceCard({
  label,
  title,
  metrics,
  copy,
}: {
  label: string
  title: string
  metrics: ReactNode
  copy: string
}) {
  return (
    <article className="report-card showcase-summary-card">
      <span className="surface-label">{label}</span>
      <h3>{title}</h3>
      <div className="headline-strip">{metrics}</div>
      <p className="surface-copy compact">{copy}</p>
    </article>
  )
}

function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: { label: string; value: T }[]
  value: T
  onChange: (value: T) => void
}) {
  return (
    <div aria-label={label} className="segmented-control" role="tablist">
      {options.map((option) => (
        <button
          aria-selected={option.value === value}
          className={`segment-button${option.value === value ? ' active' : ''}`}
          key={option.value}
          onClick={() => onChange(option.value)}
          role="tab"
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

function DevelopmentYard({
  solution,
  yard,
  scale = 26,
  showLabels = true,
}: {
  solution: DevelopmentSolution
  yard: DemoSnapshot['yard']
  scale?: number
  showLabels?: boolean
}) {
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
              rx="10"
              fill={developmentPalette[index % developmentPalette.length]}
              fillOpacity="0.9"
            />
            {showLabels ? (
              <>
                <text x={x + 8} y={y + 18} className="svg-label strong small">
                  {placement.block_id}
                </text>
                <text x={x + 8} y={y + 32} className="svg-label small">
                  t={placement.start_time}-{placement.end_time}
                </text>
              </>
            ) : null}
          </g>
        )
      })}
    </svg>
  )
}

function SpaceOrganizationFigure({
  solution,
  yard,
}: {
  solution: DevelopmentSolution
  yard: DemoSnapshot['yard']
}) {
  const scale = 26
  const width = yard.width * scale
  const height = yard.height * scale
  const accessLaneWidth = Math.max(scale * 1.2, width * 0.16)
  const reserveHeight = Math.max(scale * 1.25, height * 0.2)

  return (
    <svg className="yard-svg organization-figure" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Space organization figure">
      <rect x="0" y="0" width={width} height={height} className="yard-frame" rx="18" />
      <rect x="0" y="0" width={accessLaneWidth} height={height} className="zone-access" rx="18" />
      <rect x={accessLaneWidth} y="0" width={Math.max(width - accessLaneWidth, 0)} height={Math.max(height - reserveHeight, 0)} className="zone-core" rx="18" />
      <rect x={accessLaneWidth} y={height - reserveHeight} width={Math.max(width - accessLaneWidth, 0)} height={reserveHeight} className="zone-reserve" rx="18" />

      <text x="12" y="20" className="svg-label strong small">Access edge</text>
      <text x={accessLaneWidth + 10} y="20" className="svg-label strong small">Compact storage core</text>
      <text x={accessLaneWidth + 10} y={height - 10} className="svg-label strong small">Late-flex reserve</text>

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
              rx="10"
              fill={developmentPalette[index % developmentPalette.length]}
              fillOpacity="0.9"
              stroke="rgba(248, 251, 253, 0.56)"
              strokeWidth="1.5"
            />
            <text x={x + 8} y={y + 18} className="svg-label strong small">
              {placement.block_id}
            </text>
            <text x={x + 8} y={y + 32} className="svg-label small">
              t={placement.start_time}-{placement.end_time}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function OrganizationComparisonFigure({ yard }: { yard: DemoSnapshot['yard'] }) {
  const scale = 22
  const panelWidth = yard.width * scale
  const panelHeight = yard.height * scale
  const gap = 36
  const totalWidth = panelWidth * 2 + gap

  const clutterBlocks = [
    { x: 18, y: 18, width: 82, height: 52 },
    { x: 108, y: 26, width: 68, height: 48 },
    { x: 34, y: 82, width: 74, height: 54 },
    { x: 118, y: 92, width: 76, height: 44 },
    { x: 24, y: 146, width: 94, height: 52 },
    { x: 126, y: 152, width: 66, height: 48 },
  ]

  return (
    <svg className="organization-comparison" viewBox={`0 0 ${totalWidth} ${panelHeight + 44}`} role="img" aria-label="Before and after yard organization comparison">
      <text x="8" y="18" className="svg-label strong small">Naive dense filling</text>
      <text x={panelWidth + gap + 8} y="18" className="svg-label strong small">YardMind organized allocation</text>

      <g className="ship-figure">
        <rect x="0" y={panelHeight + 14} width="78" height="18" rx="8" className="ship-body" />
        <polygon points="78,14 110,23 78,32" className="ship-body" />
        <rect x="18" y={panelHeight + 8} width="14" height="8" rx="2" className="ship-deck" />
        <text x="0" y={panelHeight + 42} className="svg-label strong small">Ship arrivals</text>
      </g>

      <rect x="0" y="28" width={panelWidth} height={panelHeight} className="yard-frame" rx="18" />
      <rect x={panelWidth + gap} y="28" width={panelWidth} height={panelHeight} className="yard-frame" rx="18" />

      {clutterBlocks.map((block, index) => (
        <rect
          key={`clutter-${index}`}
          x={block.x}
          y={block.y + 28}
          width={block.width}
          height={block.height}
          rx="10"
          fill={developmentPalette[index % developmentPalette.length]}
          fillOpacity="0.9"
        />
      ))}

      <rect x={panelWidth + gap} y="28" width="52" height={panelHeight} className="zone-access" rx="18" />
      <rect x={panelWidth + gap + 52} y="28" width={panelWidth - 52} height={panelHeight - 52} className="zone-core" rx="18" />
      <rect x={panelWidth + gap + 52} y={panelHeight - 24} width={panelWidth - 52} height="52" className="zone-reserve" rx="18" />

      <path d={`M ${panelWidth + 8} ${panelHeight / 2 + 28} C ${panelWidth + 18} ${panelHeight / 2 + 16}, ${panelWidth + gap - 18} ${panelHeight / 2 + 16}, ${panelWidth + gap - 8} ${panelHeight / 2 + 28}`} className="organization-arrow" />
      <polygon points={`${panelWidth + gap - 8},${panelHeight / 2 + 28} ${panelWidth + gap - 20},${panelHeight / 2 + 22} ${panelWidth + gap - 18},${panelHeight / 2 + 36}`} className="organization-arrow-head" />
      <path d={`M 110 ${panelHeight + 23} C 150 ${panelHeight + 23}, 170 ${panelHeight - 18}, 212 ${panelHeight - 18}`} className="allocation-arrow" />
      <polygon points={`212,${panelHeight - 18} 198,${panelHeight - 25} 200,${panelHeight - 11}`} className="allocation-arrow-head" />

      <text x={panelWidth + gap + 10} y="48" className="svg-label strong small">Access edge</text>
      <text x={panelWidth + gap + 64} y="48" className="svg-label strong small">Compact core</text>
      <text x={panelWidth + gap + 64} y={panelHeight + 14} className="svg-label strong small">Reserve band</text>
    </svg>
  )
}

function OrganizationFlowFigure() {
  return (
    <svg
      className="organization-flow-figure"
      viewBox="0 0 1280 360"
      role="img"
      aria-label="Ship arrival to organized yard flow"
    >
      <defs>
        <linearGradient id="shipHullGradient" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="#1e3a5f" />
          <stop offset="55%" stopColor="#245b93" />
          <stop offset="100%" stopColor="#16324f" />
        </linearGradient>
        <linearGradient id="shipWaterGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="rgba(121, 197, 219, 0.28)" />
          <stop offset="100%" stopColor="rgba(24, 58, 79, 0.04)" />
        </linearGradient>
      </defs>

      <text x="32" y="34" className="svg-label strong">Incoming ship</text>
      <ellipse cx="154" cy="228" rx="136" ry="20" className="ship-water-shadow" />
      <g className="ship-figure-live">
        <path d="M 28 220 C 72 214, 120 212, 196 212 L 252 212 C 274 212, 292 202, 312 188 L 328 188 L 294 232 L 60 232 C 42 232, 32 228, 28 220 Z" className="ship-hull" />
        <path d="M 40 220 C 84 216, 132 214, 206 214 L 284 214" className="ship-waterline" />
        <rect x="74" y="174" width="34" height="38" rx="6" className="ship-bridge" />
        <rect x="108" y="162" width="24" height="50" rx="6" className="ship-bridge" />
        <rect x="122" y="142" width="6" height="26" rx="3" className="ship-mast" />
        <rect x="119" y="138" width="12" height="6" rx="3" className="ship-mast" />
        <rect x="86" y="204" width="28" height="8" rx="3" className="ship-window-band" />
        <rect x="136" y="174" width="42" height="18" rx="5" className="ship-container ship-container-a ship-container-live ship-container-live-1" />
        <rect x="182" y="174" width="36" height="18" rx="5" className="ship-container ship-container-b ship-container-live ship-container-live-2" />
        <rect x="222" y="174" width="30" height="18" rx="5" className="ship-container ship-container-c ship-container-live ship-container-live-3" />
        <rect x="150" y="154" width="34" height="16" rx="5" className="ship-container ship-container-b ship-container-live ship-container-live-4" />
        <rect x="188" y="154" width="28" height="16" rx="5" className="ship-container ship-container-d ship-container-live ship-container-live-5" />
        <rect x="222" y="154" width="24" height="16" rx="5" className="ship-container ship-container-a ship-container-live ship-container-live-6" />
      </g>
      <path d="M 18 232 C 62 242, 118 244, 188 240 C 248 236, 288 228, 330 232" className="ship-wave" />
      <path d="M 30 246 C 84 252, 136 252, 196 248 C 252 244, 292 240, 326 244" className="ship-wave soft" />
      <text x="36" y="252" className="svg-label small">Blocks arrive as a constrained wave with time windows and handling limits.</text>

      <path d="M 292 188 C 336 188, 354 188, 392 188" className="flow-arrow" />
      <polygon points="392,188 372,178 374,198" className="flow-arrow-head" />

      <rect x="412" y="72" width="238" height="224" rx="28" className="flow-panel" />
      <text x="438" y="112" className="svg-label strong">1. Feasible first</text>
      <text x="438" y="146" className="svg-label small">Constructive placement respects bounds, overlap, and timing.</text>
      <rect x="438" y="176" width="46" height="46" rx="10" className="flow-block flow-block-a flow-block-live flow-block-live-1" />
      <rect x="490" y="176" width="64" height="36" rx="10" className="flow-block flow-block-b flow-block-live flow-block-live-2" />
      <rect x="438" y="228" width="78" height="32" rx="10" className="flow-block flow-block-c flow-block-live flow-block-live-3" />
      <rect x="528" y="220" width="64" height="40" rx="10" className="flow-block flow-block-d flow-block-live flow-block-live-4" />

      <path d="M 666 188 C 706 188, 724 188, 760 188" className="flow-arrow" />
      <polygon points="760,188 740,178 742,198" className="flow-arrow-head" />

      <rect x="780" y="72" width="238" height="224" rx="28" className="flow-panel" />
      <text x="806" y="112" className="svg-label strong">2. Repair congestion</text>
      <text x="806" y="146" className="svg-label small">Search reopens crowded zones and reallocates risky blocks.</text>
      <path d="M 842 230 C 874 192, 906 170, 962 168" className="organization-arrow" />
      <polygon points="962,168 944,162 948,180" className="organization-arrow-head" />
      <circle cx="848" cy="232" r="13" className="flow-accent" />
      <circle cx="886" cy="192" r="13" className="flow-accent" />
      <circle cx="964" cy="168" r="13" className="flow-accent" />
      <text x="806" y="258" className="svg-label small">The move is deliberate: clear access, reduce conflict, keep room for later arrivals.</text>

      <path d="M 1034 188 C 1074 188, 1092 188, 1128 188" className="flow-arrow" />
      <polygon points="1128,188 1108,178 1110,198" className="flow-arrow-head" />

      <rect x="1140" y="72" width="108" height="224" rx="24" className="yard-frame" />
      <rect x="1140" y="72" width="22" height="224" rx="20" className="zone-access" />
      <rect x="1162" y="72" width="86" height="166" rx="18" className="zone-core" />
      <rect x="1162" y="238" width="86" height="58" rx="18" className="zone-reserve" />
      <rect x="1172" y="94" width="30" height="44" rx="8" className="flow-block flow-block-a" />
      <rect x="1208" y="94" width="26" height="34" rx="8" className="flow-block flow-block-b" />
      <rect x="1172" y="146" width="62" height="40" rx="8" className="flow-block flow-block-c" />
      <text x="1140" y="34" className="svg-label strong">3. Readable yard</text>
      <text x="1110" y="328" className="svg-label small">Access side, compact core, and reserve band are visible at a glance.</text>
    </svg>
  )
}

function OrganizationMoveTable({
  allocationTrace,
}: {
  allocationTrace: AllocationTraceRow[]
}) {
  return (
    <div className="table-shell">
      <table className="trace-table compact-table">
        <thead>
          <tr>
            <th>Block</th>
            <th>Constructive</th>
            <th>Search</th>
            <th>Status</th>
            <th>Access</th>
            <th>Conflict</th>
            <th>Core fit</th>
            <th>Net proxy</th>
            <th>Why</th>
          </tr>
        </thead>
        <tbody>
          {allocationTrace.map((row) => (
            <tr key={row.block_id}>
              <td>{row.block_id}</td>
              <td>{`(${row.from_x}, ${row.from_y})`}</td>
              <td>{`(${row.to_x}, ${row.to_y})`}</td>
              <td>{row.moved ? 'Moved' : 'Kept'}</td>
              <td className={row.access_delta > 0 ? 'signal-good' : row.access_delta < 0 ? 'signal-warn' : ''}>{formatDelta(row.access_delta)}</td>
              <td className={row.conflict_delta > 0 ? 'signal-good' : row.conflict_delta < 0 ? 'signal-warn' : ''}>{formatDelta(row.conflict_delta)}</td>
              <td className={row.core_delta > 0 ? 'signal-good' : row.core_delta < 0 ? 'signal-warn' : ''}>{formatDelta(row.core_delta)}</td>
              <td className={row.signal_score > 0 ? 'signal-good' : row.signal_score < 0 ? 'signal-warn' : ''}>{formatDelta(row.signal_score)}</td>
              <td>{row.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function OfficialSolvePlayback({
  label,
  bays,
  assignments,
  runtimeSeconds,
  autoPlay,
  interactive = true,
}: {
  label: string
  bays: OfficialBay[]
  assignments: OfficialAssignment[]
  runtimeSeconds: number
  autoPlay: boolean
  interactive?: boolean
}) {
  const bounds = useMemo(() => getTimelineBounds(assignments), [assignments])
  const [currentTime, setCurrentTime] = useState(bounds.start)
  const [isPlaying, setIsPlaying] = useState(interactive && autoPlay && bounds.end > bounds.start)

  useEffect(() => {
    setCurrentTime(bounds.start)
    setIsPlaying(interactive && autoPlay && bounds.end > bounds.start)
  }, [autoPlay, bounds.end, bounds.start, interactive, label])

  useEffect(() => {
    if (!interactive || !isPlaying || bounds.end <= bounds.start) {
      return
    }

    const timer = window.setTimeout(() => {
      setCurrentTime((time) => (time >= bounds.end ? bounds.start : time + 1))
    }, 1000)

    return () => window.clearTimeout(timer)
  }, [bounds.end, bounds.start, currentTime, isPlaying])

  const playbackTime = interactive ? currentTime : bounds.start
  const activeAssignments = getAssignmentsAtTime(assignments, playbackTime)
  const operations = getOperationsAtTime(assignments, playbackTime)
  const activeOperationBayIds = new Set(operations.map((operation) => operation.bay_id))
  const activeBayCount = new Set(activeAssignments.map((assignment) => assignment.bay_id)).size

  return (
    <div className={`playback-shell${interactive ? '' : ' compact-playback'}`}>
      <div className="playback-toolbar">
        <div className="playback-heading-block">
          <div>
            <span className="surface-label">Competition-facing replay</span>
            {label ? <p className="surface-copy compact playback-title">{label}</p> : null}
          </div>
          <p className="playback-meta">
            Step {playbackTime} of {bounds.end} · runtime {formatCompactSeconds(runtimeSeconds)}
          </p>
        </div>
        {interactive ? (
          <div className="action-row compact-actions playback-control-row">
            <button className="action-button" disabled={isPlaying} onClick={() => setIsPlaying(true)} type="button">
              Play
            </button>
            <button className="action-button" disabled={!isPlaying} onClick={() => setIsPlaying(false)} type="button">
              Pause
            </button>
            <button
              className="action-button"
              onClick={() => setCurrentTime((time) => (time <= bounds.start ? bounds.end : time - 1))}
              type="button"
            >
              Prev
            </button>
            <button
              className="action-button"
              onClick={() => setCurrentTime((time) => (time >= bounds.end ? bounds.start : time + 1))}
              type="button"
            >
              Next
            </button>
          </div>
        ) : (
          <p className="surface-copy compact playback-preview-note">Preview only. Open the fullscreen replay stage to play this flow.</p>
        )}
      </div>
      {interactive ? (
        <div className="playback-timeline-shell">
          <div className="playback-timeline-meta">
            <span className="surface-label">Timeline scrubber</span>
            <p className="surface-copy compact">Drag the replay when you want to pause on a specific crane action or bay transition.</p>
          </div>
          <input
            aria-label="Official solve playback time"
            className="timeline-slider"
            max={bounds.end}
            min={bounds.start}
            onChange={(event) => setCurrentTime(Number(event.target.value))}
            type="range"
            value={currentTime}
          />
        </div>
      ) : null}
      <div className="headline-strip muted-strip playback-kpi-strip">
        <KpiPill label="Active blocks" value={`${activeAssignments.length}`} />
        <KpiPill label="Operations now" value={`${operations.length}`} />
        <KpiPill label="Active bays" value={`${activeBayCount}`} />
      </div>
      <div className="bay-stack playback-bay-grid">
        {bays.map((bay) => (
          <article className={`bay-surface playback-bay-surface${activeOperationBayIds.has(bay.bay_id) ? ' bay-surface-active playback-bay-surface-active' : ''}`} key={`${label}-${bay.bay_id}`}>
            <div className="bay-heading">
              <div>
                <span className="surface-label">Bay {bay.bay_id}</span>
                <p className="surface-copy compact bay-caption">
                  {activeOperationBayIds.has(bay.bay_id) ? 'Active crane zone' : 'Stable at this step'}
                </p>
              </div>
              <span className="bay-size">
                {bay.width} x {bay.height}
              </span>
            </div>
            <OfficialBayView
              bay={bay}
              assignments={activeAssignments.filter((assignment) => assignment.bay_id === bay.bay_id)}
            />
          </article>
        ))}
      </div>
      <div className="event-row playback-event-shell">
        {operations.length > 0 ? (
          operations.map((operation) => (
            <span className={`event-pill event-pill-${operation.kind.toLowerCase()} event-pill-live`} key={`${operation.kind}-${operation.block_id}-${operation.bay_id}`}>
              {operation.kind} block {operation.block_id} in bay {operation.bay_id}
            </span>
          ))
        ) : (
          <span className="event-pill event-pill-idle">No crane move at this time</span>
        )}
      </div>
    </div>
  )
}

function OfficialBayView({ bay, assignments }: { bay: OfficialBay; assignments: OfficialAssignment[] }) {
  const scale = Math.max(14, Math.min(20, Math.floor(210 / Math.max(bay.width, 1))))
  const width = bay.width * scale
  const height = bay.height * scale

  return (
    <svg className="yard-svg official" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Official bay ${bay.bay_id}`}>
      <rect x="0" y="0" width={width} height={height} className="yard-frame" rx="14" />
      {assignments.map((assignment, index) => {
        const x = assignment.x * scale
        const y = height - (assignment.y + assignment.height) * scale
        return (
          <g className="official-block-live" key={`${assignment.block_id}-${index}`}>
            <rect
              x={x}
              y={y}
              width={assignment.width * scale}
              height={assignment.height * scale}
              rx="8"
              fill={officialPalette[index % officialPalette.length]}
              fillOpacity="0.9"
            />
            <text x={x + 6} y={y + 16} className="svg-label strong small">
              B{assignment.block_id}
            </text>
            <text x={x + 6} y={y + 30} className="svg-label small">
              {assignment.entry_time}-{assignment.exit_time ?? '?'}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function FullscreenDialog({
  open,
  title,
  subtitle,
  onClose,
  hideClose = false,
  children,
}: {
  open: boolean
  title: string
  subtitle: string
  onClose: () => void
  hideClose?: boolean
  children: ReactNode
}) {
  useEffect(() => {
    if (!open || hideClose) {
      return
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [hideClose, onClose, open])

  if (!open) {
    return null
  }

  return (
    <div
      aria-modal="true"
      className="dialog-backdrop"
      onClick={hideClose ? undefined : onClose}
      role="dialog"
    >
      <div className="dialog-surface" onClick={(event) => event.stopPropagation()}>
        {hideClose ? null : (
          <button aria-label="Close dialog" className="action-button dialog-close-button" onClick={onClose} type="button">
            Close
          </button>
        )}
        <div className="dialog-header">
          <div>
            <span className="surface-label">{subtitle}</span>
            <h2>{title}</h2>
          </div>
        </div>
        <div className="dialog-content">{children}</div>
      </div>
    </div>
  )
}

function EquationDialogContent({
  data,
  officialSummary,
}: {
  data: DemoSnapshot
  officialSummary: DemoSnapshot['official']['summary']
}) {
  return (
    <div className="dialog-stack">
      <section className="dialog-card">
        <span className="surface-label">Development objective</span>
        <h3>Current YardMind search score</h3>
        <p className="surface-copy compact">
          This is the current development objective that the local search loop maximizes. Positive
          delta means improvement because the score rises as layouts become better.
        </p>
        <div className="equation-card">
          <ReportEquationBlock
            ariaLabel="Development score formula"
            label="Development score"
            caption="The search loop maximizes yard utilization while subtracting the three forward-looking penalty terms."
            latex={'\\mathrm{Score} = U_{\\mathrm{area}} - P_{\\mathrm{late}} - P_{\\mathrm{risk}} - P_{\\mathrm{congestion}}'}
          />
        </div>
        <div className="table-shell">
          <table className="trace-table compact-table">
            <thead>
              <tr>
                <th>Term</th>
                <th>Meaning</th>
                <th>Incumbent</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>area_utilization</td>
                <td>How efficiently the yard footprint is used.</td>
                <td>{data.search_solution.objective_breakdown.area_utilization.toFixed(4)}</td>
              </tr>
              <tr>
                <td>lateness_penalty</td>
                <td>Penalty for delayed handling.</td>
                <td>{data.search_solution.objective_breakdown.lateness_penalty.toFixed(4)}</td>
              </tr>
              <tr>
                <td>retrieval_risk_penalty</td>
                <td>Penalty for making future retrieval difficult.</td>
                <td>{data.search_solution.objective_breakdown.retrieval_risk_penalty.toFixed(4)}</td>
              </tr>
              <tr>
                <td>congestion_penalty</td>
                <td>Penalty for local obstruction and density.</td>
                <td>{data.search_solution.objective_breakdown.congestion_penalty.toFixed(4)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="dialog-card">
        <span className="surface-label">Official objective</span>
        <h3>Competition objective</h3>
        <p className="surface-copy compact">
          This is the report-facing objective surface for the official problem. The competition
          minimizes tardiness, bay imbalance, and preference loss through a weighted sum.
        </p>
        <div className="equation-card">
          <ReportEquationBlock
            ariaLabel="Official tardiness term"
            label="Tardiness term"
            caption="Lower is better: every delayed block adds to total tardiness."
            latex={'Z_1 = \\sum_i T_i'}
          />
          <ReportEquationBlock
            ariaLabel="Official balance term"
            label="Balance term"
            caption="This penalizes the worst weighted difference between any two bays."
            latex={'\\begin{aligned} Z_2 &= \\max_{j_1 \\neq j_2} \\Bigl| u_{j_1} \\sum_{i \\in N(j_1)} L_i \\\\ &\\quad - u_{j_2} \\sum_{i \\in N(j_2)} L_i \\Bigr| \\end{aligned}'}
          />
          <ReportEquationBlock
            ariaLabel="Official preference term"
            label="Preference term"
            caption="This measures how far each block is assigned from its best admissible bay."
            latex={'\\begin{aligned} Z_3 &= \\sum_{j \\in M} \\sum_{i \\in N(j)} \\\\ &\\quad \\left(S_i^{\\max} - S_{ij}\\right) \\end{aligned}'}
          />
          <ReportEquationBlock
            ariaLabel="Official weighted objective"
            label="Weighted objective"
            caption="The official evaluator minimizes one weighted scalar objective J built from the three terms above."
            emphasis
            latex={'\\min J = w_1 Z_1 + w_2 Z_2 + w_3 Z_3'}
          />
        </div>
        <div className="report-grid">
          <article className="report-card">
            <span className="surface-label">Notation</span>
            <p className="surface-copy compact">
              T_i is block tardiness, u_j is bay weight, L_i is workload, and S_ij measures how well
              block i matches bay j relative to its best admissible bay.
            </p>
          </article>
          <article className="report-card">
            <span className="surface-label">Interpretation</span>
            <p className="surface-copy compact">
              Z1 controls time performance, Z2 controls workload balance across bays, and Z3 controls
              how far the assignment drifts from preferred bays.
            </p>
          </article>
        </div>
        <div className="table-shell">
          <table className="trace-table compact-table">
            <thead>
              <tr>
                <th>Term</th>
                <th>Meaning</th>
                <th>Official search</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Z1</td>
                <td>Total tardiness term.</td>
                <td>{officialSummary ? officialSummary.official_search.obj1.toFixed(4) : 'N/A'}</td>
              </tr>
              <tr>
                <td>Z2</td>
                <td>Maximum weighted bay load imbalance.</td>
                <td>{officialSummary ? officialSummary.official_search.obj2.toFixed(4) : 'N/A'}</td>
              </tr>
              <tr>
                <td>Z3</td>
                <td>Loss against preferred bay assignments.</td>
                <td>{officialSummary ? officialSummary.official_search.obj3.toFixed(4) : 'N/A'}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="dialog-card">
        <span className="surface-label">Current values</span>
        <h3>Current snapshot summary</h3>
        <div className="report-grid">
          <article className="report-card">
            <span className="surface-label">Development search</span>
            <p className="surface-copy compact">
              Constructive objective: {data.constructive.objective_value.toFixed(4)}. Search incumbent:
              {' '}{data.search_solution.objective_value.toFixed(4)}. Improvement: {formatDelta(data.search.delta)}.
            </p>
          </article>
          <article className="report-card">
            <span className="surface-label">Official search</span>
            <p className="surface-copy compact">
              Search objective: {officialSummary ? officialSummary.official_search.objective.toFixed(4) : 'N/A'}.
              Native objective: {officialSummary ? officialSummary.native_constructive.objective.toFixed(4) : 'N/A'}.
              Delegated objective: {officialSummary ? officialSummary.delegated_baseline.objective.toFixed(4) : 'N/A'}.
            </p>
          </article>
        </div>
      </section>
    </div>
  )
}

function ProofDialogContent({
  officialSummary,
  runtimeRatio,
  officialObjectiveDelta,
  proofVariant,
  progressSummary,
}: {
  officialSummary: DemoSnapshot['official']['summary']
  runtimeRatio: number
  officialObjectiveDelta: number
  proofVariant: OfficialVariant | null
  progressSummary: DemoProgressSummary
}) {
  if (!officialSummary || !proofVariant) {
    return (
      <div className="dialog-stack">
        <section className="dialog-card">
          <span className="surface-label">Official snapshot</span>
          <h3>Proof view unavailable</h3>
          <p className="surface-copy compact">Official comparison data is missing from the current demo snapshot.</p>
        </section>
      </div>
    )
  }

  const [proofTab, setProofTab] = useState<'snapshot' | 'terms'>('snapshot')

  return (
    <div className="dialog-stack proof-scene-stack">
      <DemoProgressStrip label="Demo progress" summary={progressSummary} />
      <section className="dialog-card proof-hero-card proof-scene-hero">
        <div className="proof-scene-heading">
          <div>
            <span className="surface-label">Validation view</span>
            <h3>Official result overview</h3>
          </div>
          <SegmentedControl
            label="Validation surface"
            onChange={setProofTab}
            options={[
              { label: 'Snapshot', value: 'snapshot' },
              { label: 'Terms', value: 'terms' },
            ]}
            value={proofTab}
          />
        </div>
        <div className="proof-toolbar">
          <p className="surface-copy compact proof-toolbar-copy">
            Keep the validation view on one surface at a time: result summary or objective terms.
          </p>
        </div>
      </section>

      <section className={`dialog-card proof-stage-card proof-stage-card-${proofTab}`}>
        {proofTab === 'snapshot' ? (
          <>
            <span className="surface-label">Official snapshot</span>
            <h3>Pass/fail, objective, and runtime</h3>
            <div className="headline-strip">
              <KpiPill label="Official status" value={proofVariant.feasible ? 'PASS' : 'FAIL'} tone={proofVariant.feasible ? 'good' : 'bad'} />
              <KpiPill label="Stage" value={`${proofVariant.stage}`} />
              <KpiPill label="Objective" value={proofVariant.objective.toFixed(4)} />
              <KpiPill label="Runtime" value={formatCompactSeconds(proofVariant.runtime_seconds)} />
              <KpiPill label="Search vs delegated" value={formatDelta(officialObjectiveDelta)} tone={officialObjectiveDelta <= 0 ? 'good' : 'warn'} />
              <KpiPill label="Runtime ratio" value={`${runtimeRatio.toFixed(2)}x`} />
            </div>
            <p className="surface-copy compact proof-stage-copy">
              This proof surface summarizes whether official search passes, the objective it achieves, and the runtime cost relative to the delegated baseline.
            </p>
          </>
        ) : null}

        {proofTab === 'terms' ? (
          <>
            <span className="surface-label">Official objective terms</span>
            <h3>Current official search breakdown</h3>
            <div className="headline-strip">
              <KpiPill label="Z1 tardiness" value={proofVariant.obj1.toFixed(4)} />
              <KpiPill label="Z2 imbalance" value={proofVariant.obj2.toFixed(4)} />
              <KpiPill label="Z3 preference loss" value={proofVariant.obj3.toFixed(4)} />
            </div>
            <div className="equation-card">
              <div className="equation-display math-display emphasis">
                <OfficialObjectiveFormula />
              </div>
            </div>
          </>
        ) : null}

      </section>
    </div>
  )
}

function SpaceOrganizationDialogContent({
  allocationTrace,
  progressSummary,
  solution,
  yard,
}: {
  allocationTrace: AllocationTraceRow[]
  progressSummary: DemoProgressSummary
  solution: DevelopmentSolution
  yard: DemoSnapshot['yard']
}) {
  const allocationStages = [
    {
      title: 'Ship arrives',
      copy: 'Incoming blocks are treated as a constrained wave rather than isolated rectangles.',
    },
    {
      title: 'Constructive baseline',
      copy: 'The first pass places every block feasibly, while still leaving dense zones near access.',
    },
    {
      title: 'Search repair',
      copy: 'Destroy-and-repair reopens crowded zones and reallocates risky placements.',
    },
    {
      title: 'Readable yard',
      copy: 'The final state preserves access, compresses the core, and leaves flexible reserve space.',
    },
  ]

  const [organizationTab, setOrganizationTab] = useState<'comparison' | 'flow' | 'layout' | 'trace'>('flow')

  return (
    <div className="dialog-stack organization-dialog-stack organization-scene-stack">
      <DemoProgressStrip label="Demo progress" summary={progressSummary} />
      <section className="dialog-card proof-hero-card organization-scene-hero">
        <div className="proof-scene-heading">
          <div>
            <span className="surface-label">Space organization</span>
            <h3>Why the layout story adds more than a final score</h3>
          </div>
          <SegmentedControl
            label="Organization surface"
            onChange={setOrganizationTab}
            options={[
              { label: 'Ship Flow', value: 'flow' },
              { label: 'Before / After', value: 'comparison' },
              { label: 'Final Layout', value: 'layout' },
              { label: 'Move Trace', value: 'trace' },
            ]}
            value={organizationTab}
          />
        </div>
        <div className="organization-toolbar">
          <p className="surface-copy compact proof-toolbar-copy">
            Each organization surface isolates one aspect of the layout: ship-to-yard flow, before-vs-after contrast, final layout, or detailed move trace.
          </p>
        </div>
      </section>

      <section className={`dialog-card organization-stage-card organization-stage-card-${organizationTab}`}>
        <div className="organization-scene-header">
          <div>
            <span className="surface-label">Fullscreen diagram</span>
            <h3>{organizationTab === 'comparison'
              ? 'From dense wall to organized allocation'
              : organizationTab === 'flow'
                ? 'How a ship turns into an organized yard state'
                : organizationTab === 'layout'
                  ? 'Algorithm-guided use of space'
                  : 'Which blocks moved and why'}</h3>
          </div>
        </div>
        {organizationTab === 'comparison' ? (
          <>
            <p className="surface-copy compact organization-stage-copy">
              The comparison view contrasts a dense wall on the left with a layout on the right that preserves an access edge, a compact core, and readable reserve space.
            </p>
            <div className="organization-stage-shell organization-stage-shell-comparison">
              <div className="showcase-stage-marker showcase-stage-marker-development organization-scene-marker" aria-hidden="true">
                <span className="showcase-stage-marker-pill">Allocation contrast</span>
                <span className="showcase-stage-marker-copy">Contrast uniform density with structured space</span>
              </div>
              <OrganizationComparisonFigure yard={yard} />
            </div>
            <div className="organization-stage-notes">
              <article className="report-card organization-card">
                <span className="surface-label">Access edge</span>
                <p className="surface-copy compact">The lighter side zone remains open so retrieval remains interpretable rather than buried behind density.</p>
              </article>
              <article className="report-card organization-card">
                <span className="surface-label">Compact core</span>
                <p className="surface-copy compact">Stable placements are packed together where utilization is high and adjacency is controlled.</p>
              </article>
              <article className="report-card organization-card">
                <span className="surface-label">Reserve band</span>
                <p className="surface-copy compact">Late-flex space remains visible for later arrivals and tighter windows.</p>
              </article>
            </div>
          </>
        ) : null}

        {organizationTab === 'flow' ? (
          <>
            <p className="surface-copy compact organization-stage-copy">
              This flow shows the full allocation sequence: arrivals form a constrained wave, constructive establishes feasibility, and search repairs crowding before the yard reaches its final state.
            </p>
            <div className="organization-stage-shell organization-stage-shell-flow">
              <div className="showcase-stage-marker showcase-stage-marker-development organization-scene-marker" aria-hidden="true">
                <span className="showcase-stage-marker-pill">Flow story</span>
                <span className="showcase-stage-marker-copy">Arrival, feasibility, repair, and final layout state</span>
              </div>
              <OrganizationFlowFigure />
            </div>
            <div className="allocation-sequence-grid organization-stage-notes">
              {allocationStages.map((stage, index) => (
                <article className="report-card allocation-stage-card" key={stage.title} style={{ animationDelay: `${index * 120}ms` }}>
                  <div className="allocation-stage-index">0{index + 1}</div>
                  <strong>{stage.title}</strong>
                  <p className="surface-copy compact">{stage.copy}</p>
                </article>
              ))}
            </div>
          </>
        ) : null}

        {organizationTab === 'layout' ? (
          <>
            <p className="surface-copy compact organization-stage-copy">
              The final yard provides the exact spatial explanation: feasibility is enforced first, then retrieval risk and congestion guide repairs in difficult zones.
            </p>
            <div className="organization-stage-shell organization-stage-shell-layout">
              <div className="showcase-stage-marker showcase-stage-marker-development organization-scene-marker" aria-hidden="true">
                <span className="showcase-stage-marker-pill">Layout reading</span>
                <span className="showcase-stage-marker-copy">Use the final yard to explain access edges, compact core, and reserve space</span>
              </div>
              <SpaceOrganizationFigure solution={solution} yard={yard} />
            </div>
            <div className="report-grid organization-stage-notes">
              <article className="report-card">
                <span className="surface-label">1. Feasible first</span>
                <p className="surface-copy compact">Every candidate is filtered by yard bounds, time overlap, and spacing feasibility before scoring begins.</p>
              </article>
              <article className="report-card">
                <span className="surface-label">2. Retrieval-aware scoring</span>
                <p className="surface-copy compact">Positions are judged by area use, lateness, retrieval risk, and congestion rather than density alone.</p>
              </article>
              <article className="report-card">
                <span className="surface-label">3. Repair difficult zones</span>
                <p className="surface-copy compact">Search removes risky clusters and rebuilds them so the final layout is organized, not merely full.</p>
              </article>
            </div>
          </>
        ) : null}

        {organizationTab === 'trace' ? (
          <>
            <p className="surface-copy compact organization-stage-copy">
              The move table translates the diagram into the exact blocks moved, the gain signals, and the associated reasons.
            </p>
            <div className="organization-trace-shell organization-stage-shell organization-stage-shell-trace">
              <OrganizationMoveTable allocationTrace={allocationTrace} />
            </div>
          </>
        ) : null}
      </section>
    </div>
  )
}

function JudgeModeDialogContent({
  autoAdvanceDefault,
  officialSummary,
  officialObjectiveDelta,
  proofVariant,
  progressSummary,
  reportEvidence,
  runtimeRatio,
}: {
  autoAdvanceDefault: boolean
  officialSummary: DemoSnapshot['official']['summary']
  officialObjectiveDelta: number
  proofVariant: OfficialVariant | null
  progressSummary: DemoProgressSummary
  reportEvidence: ReportEvidence | null
  runtimeRatio: number
}) {
  const judgeSteps = [
    {
      id: 'organization',
      label: 'Space organization',
      title: 'Readable yard structure',
      copy: 'The opening step establishes why the algorithm does not simply maximize density.',
    },
    {
      id: 'equations',
      label: 'Equations',
      title: 'Optimization target',
      copy: 'The second step connects the visual layout to the formal objective definition.',
    },
    {
      id: 'proof',
      label: 'Proof',
      title: 'Official evidence',
      copy: 'The validation step summarizes public stability, hard-case recovery, and the quality-case improvement of 49 objective points.',
    },
    {
      id: 'win',
      label: 'Why we win',
      title: 'Project conclusion',
      copy: 'The closing frame consolidates readable yard structure, explicit objective math, and validated official results.',
    },
  ] as const
  const [activeStep, setActiveStep] = useState<(typeof judgeSteps)[number]['id']>('organization')
  const [autoAdvance, setAutoAdvance] = useState(autoAdvanceDefault)
  const activeStepIndex = judgeSteps.findIndex((step) => step.id === activeStep)
  const currentStep = judgeSteps[activeStepIndex] ?? judgeSteps[0]
  const judgeProgress = ((activeStepIndex + 1) / judgeSteps.length) * 100
  const developmentEvidence = reportEvidence?.development ?? null
  const publicOfficialEvidence = reportEvidence?.official?.public_sample ?? null
  const proofCaseOfficialEvidence = reportEvidence?.official?.proof_case ?? null
  const qualityCaseOfficialEvidence = reportEvidence?.official?.quality_case ?? null
  const hiddenOverloadedBayOfficialEvidence = reportEvidence?.official?.hidden_overloaded_bay ?? null
  const hiddenTightWindowOfficialEvidence = reportEvidence?.official?.hidden_tight_window ?? null
  const [judgeProofTab, setJudgeProofTab] = useState<'summary' | 'development' | 'stability' | 'rescue' | 'quality' | 'internal'>('summary')

  useEffect(() => {
    setAutoAdvance(autoAdvanceDefault)
  }, [autoAdvanceDefault])

  useEffect(() => {
    if (activeStep !== 'proof') {
      setJudgeProofTab('summary')
    }
  }, [activeStep])

  useEffect(() => {
    if (!autoAdvance) {
      return
    }

    const timer = window.setInterval(() => {
      setActiveStep((current) => {
        const currentIndex = judgeSteps.findIndex((step) => step.id === current)
        const nextIndex = (currentIndex + 1) % judgeSteps.length
        return judgeSteps[nextIndex].id
      })
    }, 5000)

    return () => window.clearInterval(timer)
  }, [autoAdvance, judgeSteps])

  return (
    <div className="dialog-stack">
      <DemoProgressStrip label="Demo progress" summary={progressSummary} />
      <section className="dialog-card proof-hero-card judge-sequence-shell">
        <div className="judge-sequence-hero">
          <div className="judge-sequence-hero-copy">
            <span className="surface-label">Presentation flow</span>
            <h3>Structured walkthrough across the main proof surfaces</h3>
            <p className="surface-copy compact">
              This view behaves as a storyboard rather than a settings panel. Each step isolates one claim before advancing.
            </p>
          </div>
          <div className="judge-sequence-controls">
            <button className="action-button" type="button" onClick={() => {
              setAutoAdvance(false)
              setActiveStep(judgeSteps[Math.max(activeStepIndex - 1, 0)].id)
            }}>
              Previous
            </button>
            <button className="action-button" type="button" onClick={() => setAutoAdvance(!autoAdvance)}>
              {autoAdvance ? 'Pause auto' : 'Start auto'}
            </button>
            <button className="action-button" type="button" onClick={() => {
              setAutoAdvance(false)
              setActiveStep(judgeSteps[Math.min(activeStepIndex + 1, judgeSteps.length - 1)].id)
            }}>
              Next
            </button>
          </div>
        </div>

        <div className="judge-sequence-storyboard">
          <aside className="judge-sequence-rail">
            <div className="judge-step-tabs" role="tablist" aria-label="Presentation steps">
              {judgeSteps.map((step, index) => (
                <button
                  key={step.id}
                  className={`judge-step-tab${step.id === activeStep ? ' active' : ''}`}
                  onClick={() => {
                    setAutoAdvance(false)
                    setActiveStep(step.id)
                  }}
                  role="tab"
                  type="button"
                  aria-selected={step.id === activeStep}
                >
                  <span className="judge-step-number">0{index + 1}</span>
                  <span className="judge-step-tab-copy">
                    <strong>{step.label}</strong>
                    <span>{step.title}</span>
                  </span>
                </button>
              ))}
            </div>
          </aside>

          <div className="judge-sequence-main">
            <div className="judge-progress-track" aria-hidden="true">
              <div className={`judge-progress-fill${autoAdvance ? ' autoplay' : ''}`} style={{ width: `${judgeProgress}%` }} />
            </div>
            <article className="report-card judge-spotlight-card judge-spotlight-card-live" key={activeStep}>
              <div className="judge-spotlight-eyebrow">
                <span className="surface-label">Step 0{activeStepIndex + 1}</span>
                <span className={`judge-live-pill${autoAdvance ? ' autoplay' : ''}`}>{autoAdvance ? 'Autoplay live' : 'Manual live'}</span>
              </div>
              <h3>{currentStep.title}</h3>
              <p className="surface-copy compact">{currentStep.copy}</p>
            </article>
          </div>
        </div>
      </section>

      {activeStep === 'organization' ? (
        <section className="dialog-card judge-stage-panel judge-stage-panel-live judge-stage-panel-organization">
          <span className="surface-label">Space organization</span>
          <h3>Ship-to-yard flow</h3>
          <div className="proof-stage-shell">
            <OrganizationFlowFigure />
          </div>
        </section>
      ) : null}

      {activeStep === 'equations' ? (
        <section className="dialog-card judge-stage-panel judge-stage-panel-live judge-stage-panel-equations">
          <span className="surface-label">Objective surface</span>
          <h3>Official optimization target</h3>
          <div className="equation-card">
            <div className="equation-display math-display emphasis">
              <OfficialObjectiveFormula />
            </div>
          </div>
        </section>
      ) : null}

      {activeStep === 'proof' ? (
        <section className="dialog-card judge-stage-panel judge-stage-panel-live judge-stage-panel-proof">
          <span className="surface-label">Proof snapshot</span>
          <h3>One proof surface at a time</h3>
          <div className="proof-toolbar">
            <p className="surface-copy compact proof-toolbar-copy">
              The validation section isolates one claim at a time: summary, development stability, public stability, rescue case, quality case, or internal robustness.
            </p>
            <SegmentedControl
              label="Validation surface"
              onChange={setJudgeProofTab}
              options={[
                { label: 'Summary', value: 'summary' },
                { label: 'Dev Runs', value: 'development' },
                { label: 'Public', value: 'stability' },
                { label: 'Rescue', value: 'rescue' },
                { label: 'Quality', value: 'quality' },
                { label: 'Internal', value: 'internal' },
              ]}
              value={judgeProofTab}
            />
          </div>

          {judgeProofTab === 'summary' ? (
            proofVariant && officialSummary ? (
              <JudgeEvidenceCard
                label="Summary"
                title="Official result summary"
                metrics={(
                  <>
                    <KpiPill label="Official status" value={proofVariant.feasible ? 'PASS' : 'FAIL'} tone={proofVariant.feasible ? 'good' : 'bad'} />
                    <KpiPill label="Stage" value={`${proofVariant.stage}`} />
                    <KpiPill label="Objective" value={proofVariant.objective.toFixed(4)} />
                    <KpiPill label="Runtime" value={formatCompactSeconds(proofVariant.runtime_seconds)} />
                    <KpiPill label="Search vs delegated" value={formatDelta(officialObjectiveDelta)} tone={officialObjectiveDelta <= 0 ? 'good' : 'warn'} />
                    <KpiPill label="Runtime ratio" value={`${runtimeRatio.toFixed(2)}x`} />
                  </>
                )}
                copy={`The official run is ${proofVariant.feasible ? 'feasible' : 'infeasible'}, reaches stage ${proofVariant.stage}, and changes the delegated baseline by ${formatDelta(officialObjectiveDelta)}.`}
              />
            ) : (
              <p className="surface-copy compact">Official proof data is unavailable in the current snapshot.</p>
            )
          ) : null}

          {judgeProofTab === 'development' && developmentEvidence ? (
            <JudgeEvidenceCard
              label="Development evidence"
              title="Repeated-run development evidence"
              metrics={(
                <>
                  <KpiPill label="Runs" value={`${developmentEvidence.runs}`} />
                  <KpiPill label="Improved runs" value={`${developmentEvidence.improved_runs}/${developmentEvidence.runs}`} tone={developmentEvidence.improved_runs === developmentEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search mean" value={developmentEvidence.search_mean.toFixed(4)} tone={developmentEvidence.search_mean >= developmentEvidence.constructive_mean ? 'good' : 'warn'} />
                  <KpiPill label="Mean lift" value={formatDelta(developmentEvidence.search_mean - developmentEvidence.constructive_mean)} tone={developmentEvidence.search_mean >= developmentEvidence.constructive_mean ? 'good' : 'warn'} />
                  <KpiPill label="Best search" value={developmentEvidence.search_best.toFixed(4)} tone="good" />
                </>
              )}
              copy={`The benchmark artifacts show repeated improvement: search wins ${developmentEvidence.improved_runs} of ${developmentEvidence.runs} runs, averaging ${developmentEvidence.search_mean.toFixed(4)} versus the constructive mean of ${developmentEvidence.constructive_mean.toFixed(4)}.`}
            />
          ) : null}

          {judgeProofTab === 'stability' && publicOfficialEvidence ? (
            <JudgeEvidenceCard
              label="Public stability"
              title="Public-sample stability"
              metrics={(
                <>
                  <KpiPill label="Runs" value={`${publicOfficialEvidence.runs}`} />
                  <KpiPill label="Search feasible" value={`${publicOfficialEvidence.search_feasible_runs}/${publicOfficialEvidence.runs}`} tone={publicOfficialEvidence.search_feasible_runs === publicOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search vs delegated" value={formatOptionalDelta(publicOfficialEvidence.search_vs_delegated_delta_mean)} tone={publicOfficialEvidence.search_vs_delegated_delta_mean !== null && publicOfficialEvidence.search_vs_delegated_delta_mean <= 0 ? 'good' : 'warn'} />
                  <KpiPill label="Search <= delegated" value={`${publicOfficialEvidence.search_better_or_equal_than_delegated_runs}/${publicOfficialEvidence.runs}`} tone={publicOfficialEvidence.search_better_or_equal_than_delegated_runs === publicOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search mean obj" value={formatOptionalFixed(publicOfficialEvidence.search_objective_mean)} tone={publicOfficialEvidence.search_vs_native_delta_mean !== null && publicOfficialEvidence.search_vs_native_delta_mean <= 0 ? 'good' : 'warn'} />
                  <KpiPill label="Search mean time" value={formatOptionalSeconds(publicOfficialEvidence.search_runtime_mean)} tone={publicOfficialEvidence.search_faster_than_delegated_runs === publicOfficialEvidence.runs ? 'good' : 'warn'} />
                </>
              )}
              copy={`The public official sample is the stability check: search stays feasible in ${publicOfficialEvidence.search_feasible_runs} of ${publicOfficialEvidence.runs} runs, averages ${formatOptionalFixed(publicOfficialEvidence.search_objective_mean)} against delegated ${formatOptionalFixed(publicOfficialEvidence.delegated_objective_mean)}, and behaves like a repeatable baseline rather than a one-off separator.`}
            />
          ) : null}

          {judgeProofTab === 'rescue' && proofCaseOfficialEvidence ? (
            <JudgeEvidenceCard
              label="Rescue case"
              title="Hard-case feasibility recovery"
              metrics={(
                <>
                  <KpiPill label="Instance" value={proofCaseOfficialEvidence.instance} />
                  <KpiPill label="Search feasible" value={`${proofCaseOfficialEvidence.search_feasible_runs}/${proofCaseOfficialEvidence.runs}`} tone={proofCaseOfficialEvidence.search_feasible_runs === proofCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Native feasible" value={`${proofCaseOfficialEvidence.native_feasible_runs}/${proofCaseOfficialEvidence.runs}`} tone={proofCaseOfficialEvidence.native_feasible_runs === proofCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search <= delegated" value={`${proofCaseOfficialEvidence.search_better_or_equal_than_delegated_runs}/${proofCaseOfficialEvidence.runs}`} tone={proofCaseOfficialEvidence.search_better_or_equal_than_delegated_runs === proofCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search mean obj" value={formatOptionalFixed(proofCaseOfficialEvidence.search_objective_mean)} tone={proofCaseOfficialEvidence.search_vs_delegated_delta_mean !== null && proofCaseOfficialEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'warn'} />
                  <KpiPill label="Search vs delegated" value={formatOptionalDelta(proofCaseOfficialEvidence.search_vs_delegated_delta_mean)} tone={proofCaseOfficialEvidence.search_vs_delegated_delta_mean !== null && proofCaseOfficialEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'warn'} />
                </>
              )}
              copy={`This is the hard rescue case: native constructive can fail, while official search stays feasible in ${proofCaseOfficialEvidence.search_feasible_runs} of ${proofCaseOfficialEvidence.runs} runs and averages ${formatOptionalFixed(proofCaseOfficialEvidence.search_objective_mean)} versus native ${formatOptionalFixed(proofCaseOfficialEvidence.native_objective_mean)}.`}
            />
          ) : null}

          {judgeProofTab === 'quality' && qualityCaseOfficialEvidence ? (
            <JudgeEvidenceCard
              label="Quality case"
              title="Quality-case improvement over a feasible native run"
              metrics={(
                <>
                  <KpiPill label="Instance" value={qualityCaseOfficialEvidence.instance} />
                  <KpiPill label="Search feasible" value={`${qualityCaseOfficialEvidence.search_feasible_runs}/${qualityCaseOfficialEvidence.runs}`} tone={qualityCaseOfficialEvidence.search_feasible_runs === qualityCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Native feasible" value={`${qualityCaseOfficialEvidence.native_feasible_runs}/${qualityCaseOfficialEvidence.runs}`} tone={qualityCaseOfficialEvidence.native_feasible_runs === qualityCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search <= native" value={`${qualityCaseOfficialEvidence.search_better_or_equal_than_native_runs}/${qualityCaseOfficialEvidence.runs}`} tone={qualityCaseOfficialEvidence.search_better_or_equal_than_native_runs === qualityCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search <= delegated" value={`${qualityCaseOfficialEvidence.search_better_or_equal_than_delegated_runs}/${qualityCaseOfficialEvidence.runs}`} tone={qualityCaseOfficialEvidence.search_better_or_equal_than_delegated_runs === qualityCaseOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search mean obj" value={formatOptionalFixed(qualityCaseOfficialEvidence.search_objective_mean)} tone={qualityCaseOfficialEvidence.search_vs_native_delta_mean !== null && qualityCaseOfficialEvidence.search_vs_native_delta_mean < 0 ? 'good' : 'warn'} />
                  <KpiPill label="Search vs native" value={formatOptionalDelta(qualityCaseOfficialEvidence.search_vs_native_delta_mean)} tone={qualityCaseOfficialEvidence.search_vs_native_delta_mean !== null && qualityCaseOfficialEvidence.search_vs_native_delta_mean < 0 ? 'good' : 'warn'} />
                </>
              )}
              copy={`This is the quality case: native is already feasible, but official search still improves it, averaging ${formatOptionalFixed(qualityCaseOfficialEvidence.search_objective_mean)} versus native ${formatOptionalFixed(qualityCaseOfficialEvidence.native_objective_mean)} with delta ${formatOptionalDelta(qualityCaseOfficialEvidence.search_vs_native_delta_mean)}.`}
            />
          ) : null}

          {judgeProofTab === 'internal' && hiddenOverloadedBayOfficialEvidence && hiddenTightWindowOfficialEvidence ? (
            <JudgeEvidenceCard
              label="Internal robustness"
              title="Official-format hidden stress families"
              metrics={(
                <>
                  <KpiPill label="Overloaded delta" value={formatOptionalDelta(hiddenOverloadedBayOfficialEvidence.search_vs_delegated_delta_mean)} tone={hiddenOverloadedBayOfficialEvidence.search_vs_delegated_delta_mean !== null && hiddenOverloadedBayOfficialEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'warn'} />
                  <KpiPill label="Overloaded feasible" value={`${hiddenOverloadedBayOfficialEvidence.search_feasible_runs}/${hiddenOverloadedBayOfficialEvidence.runs}`} tone={hiddenOverloadedBayOfficialEvidence.search_feasible_runs === hiddenOverloadedBayOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Tight-window delta" value={formatOptionalDelta(hiddenTightWindowOfficialEvidence.search_vs_delegated_delta_mean)} tone={hiddenTightWindowOfficialEvidence.search_vs_delegated_delta_mean !== null && hiddenTightWindowOfficialEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'warn'} />
                  <KpiPill label="Native feasible" value={`${hiddenTightWindowOfficialEvidence.native_feasible_runs}/${hiddenTightWindowOfficialEvidence.runs}`} tone={hiddenTightWindowOfficialEvidence.native_feasible_runs === hiddenTightWindowOfficialEvidence.runs ? 'good' : 'warn'} />
                  <KpiPill label="Search mean obj" value={formatOptionalFixed(hiddenTightWindowOfficialEvidence.search_objective_mean)} tone={hiddenTightWindowOfficialEvidence.search_vs_delegated_delta_mean !== null && hiddenTightWindowOfficialEvidence.search_vs_delegated_delta_mean < 0 ? 'good' : 'warn'} />
                  <KpiPill label="Search mean time" value={formatOptionalSeconds(hiddenTightWindowOfficialEvidence.search_runtime_mean)} />
                </>
              )}
              copy={`The internal robustness suite uses official-format hidden cases rather than presentation-only examples. Search cuts the overloaded-bay mean from ${formatOptionalFixed(hiddenOverloadedBayOfficialEvidence.delegated_objective_mean)} to ${formatOptionalFixed(hiddenOverloadedBayOfficialEvidence.search_objective_mean)}, then cuts the tight-window mean from ${formatOptionalFixed(hiddenTightWindowOfficialEvidence.delegated_objective_mean)} to ${formatOptionalFixed(hiddenTightWindowOfficialEvidence.search_objective_mean)} while native constructive is feasible in only ${hiddenTightWindowOfficialEvidence.native_feasible_runs} of ${hiddenTightWindowOfficialEvidence.runs} runs.`}
            />
          ) : null}
        </section>
      ) : null}

      {activeStep === 'win' ? (
        <section className="dialog-card judge-stage-panel judge-stage-panel-live judge-stage-panel-win">
          <span className="surface-label">Closing claim</span>
          <h3>Project conclusion</h3>
          <div className="report-grid">
            <article className="report-card">
              <span className="surface-label">Claim 1</span>
              <p className="surface-copy compact">We show how blocks are allocated into a readable yard, not only that a final score exists.</p>
            </article>
            <article className="report-card">
              <span className="surface-label">Claim 2</span>
              <p className="surface-copy compact">We expose the actual optimization equations, so the scoring story is explicit instead of aesthetic.</p>
            </article>
            <article className="report-card">
              <span className="surface-label">Claim 3</span>
              <p className="surface-copy compact">We close on official feasibility, term breakdown, runtime, and replay, which makes the output auditable.</p>
            </article>
          </div>
          <div className="headline-strip muted-strip">
            <KpiPill label="Core themes" value="Structure + Math + Proof" tone="good" />
            <KpiPill label="Demo mode" value={autoAdvance ? 'Hands-off' : 'Manual'} />
            <KpiPill label="Story order" value="Org -> Eq -> Proof" />
          </div>
        </section>
      ) : null}
    </div>
  )
}

function HistoryDialogContent({ history }: { history: SearchHistoryRecord[] }) {
  return (
    <div className="dialog-stack">
      <section className="dialog-card">
        <span className="surface-label">All iterations</span>
        <h3>Search history</h3>
        <div className="table-shell full-height-table">
          <table className="trace-table compact-table">
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
              {history.map((record) => (
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
      </section>
    </div>
  )
}

function OfficialObjectiveFormula({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`objective-formula${compact ? ' compact' : ''}`}>
      <MathFormula
        ariaLabel="Official objective minimize J equals w1 Z1 plus w2 Z2 plus w3 Z3"
        className="objective-formula-line"
        displayMode={!compact}
        latex={'\\min J = w_1 Z_1 + w_2 Z_2 + w_3 Z_3'}
      />
      <p className="equation-caption">
        w1, w2, and w3 are the official instance weights; Z1, Z2, and Z3 are tardiness,
        imbalance, and preference-loss terms.
      </p>
    </div>
  )
}

function ReportEquationBlock({
  label,
  caption,
  latex,
  ariaLabel,
  emphasis = false,
}: {
  label: string
  caption: string
  latex: string
  ariaLabel: string
  emphasis?: boolean
}) {
  return (
    <article className={`report-equation-block${emphasis ? ' emphasis' : ''}`}>
      <span className="report-equation-label">{label}</span>
      <div className="equation-display math-display report-equation-line">
        <MathFormula ariaLabel={ariaLabel} className="report-katex-formula" displayMode latex={latex} />
      </div>
      <p className="equation-caption">{caption}</p>
    </article>
  )
}

function MathFormula({
  latex,
  ariaLabel,
  displayMode = false,
  className = '',
}: {
  latex: string
  ariaLabel: string
  displayMode?: boolean
  className?: string
}) {
  const html = useMemo(
    () =>
      katex.renderToString(latex, {
        displayMode,
        output: 'html',
        strict: 'ignore',
        throwOnError: false,
      }),
    [displayMode, latex],
  )

  return (
    <div
      aria-label={ariaLabel}
      className={`katex-formula${displayMode ? ' display' : ' inline'}${className ? ` ${className}` : ''}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

function WalkthroughDialogContent({ lines }: { lines: WalkthroughLine[] }) {
  return (
    <div className="dialog-stack">
      <section className="dialog-card terminal-card">
        <span className="surface-label">Execution summary</span>
        <h3>What the solver does</h3>
        <div className="terminal-window">
          {lines.map((line, index) => (
            <div className={`terminal-line ${line.kind}`} key={`${line.kind}-${index}`}>
              <span className="terminal-prefix">{line.kind === 'command' ? '>' : line.kind === 'note' ? '#' : ''}</span>
              <span>{line.text}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

function DemoControlsDialogContent({ onSelect }: { onSelect: (value: DialogView) => void }) {
  const launchGroups = [
    {
      label: 'Presentation route',
      title: 'Presentation walkthrough',
      copy: 'A structured route across the main presentation surfaces with minimal manual steering.',
      preview: ['Overview brief', 'Presentation flow', 'Closing summary'],
      primary: { label: 'Open presentation flow', view: 'judge' as const },
      secondary: [{ label: 'Open overview brief', view: 'brief' as const }],
      accentClass: 'demo-launch-card-presentation',
    },
    {
      label: 'Organization',
      title: 'Yard structure and flow',
      copy: 'This route focuses on how ship flow becomes a readable yard state.',
      preview: ['Ship flow', 'Before / after', 'Fullscreen yard'],
      primary: { label: 'Open ship flow', view: 'organization' as const },
      secondary: [],
      accentClass: 'demo-launch-card-organization',
    },
    {
      label: 'Validation',
      title: 'Official validation surfaces',
      copy: 'This route focuses on official terms and direct evaluator-facing results.',
      preview: ['Validation tabs', 'Official snapshot', 'Equations'],
      primary: { label: 'Open validation view', view: 'proof' as const },
      secondary: [{ label: 'Open equations', view: 'equations' as const }],
      accentClass: 'demo-launch-card-proof',
    },
    {
      label: 'Technical detail',
      title: 'Trace and walkthrough',
      copy: 'This route exposes the underlying iterations and execution trace.',
      preview: ['Search history', 'Execution walkthrough'],
      primary: { label: 'Open walkthrough', view: 'walkthrough' as const },
      secondary: [{ label: 'Open history', view: 'history' as const }],
      accentClass: 'demo-launch-card-technical',
    },
  ]

  return (
    <div className="dialog-stack">
      <section className="dialog-card demo-controls-shell">
        <div className="demo-controls-heading">
          <div>
            <span className="surface-label">Launch surfaces</span>
            <h3>Open detail views as needed</h3>
          </div>
          <p className="surface-copy compact">
            This launch deck separates presentation flow, yard structure, proof, and technical detail into distinct routes.
          </p>
        </div>
        <div className="report-grid compact-report-grid demo-launch-grid">
          {launchGroups.map((group) => (
            <article className={`report-card compact-launch-card demo-launch-card ${group.accentClass}`} key={group.title}>
              <div className="demo-launch-topline">
                <span className="surface-label">{group.label}</span>
                <span className="demo-launch-badge" aria-hidden="true">Preview</span>
              </div>
              <h3>{group.title}</h3>
              <p className="surface-copy compact">{group.copy}</p>
              <div className="demo-launch-preview-row" aria-hidden="true">
                {group.preview.map((item) => (
                  <span className="demo-launch-preview-pill" key={item}>{item}</span>
                ))}
              </div>
              <div className="action-row demo-launch-actions">
                <button className="action-button landing-hero-action landing-hero-action-primary" onClick={() => onSelect(group.primary.view)} type="button">
                  {group.primary.label}
                </button>
                {group.secondary.map((action) => (
                  <button className="action-button landing-hero-action" key={action.label} onClick={() => onSelect(action.view)} type="button">
                    {action.label}
                  </button>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

export default App
