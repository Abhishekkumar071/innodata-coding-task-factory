

import { useState } from 'react'
import type { FormEvent } from 'react'
import type { PipelineStage, TaskAxis } from '../../types/api'

const taskAxes: { value: TaskAxis; label: string }[] = [
  { value: 'parameter-validation', label: 'Parameter Validation' },
  { value: 'command-routing', label: 'Command Routing' },
  { value: 'formatting-termui', label: 'Formatting & TermUI' },
  { value: 'context-envvar', label: 'Context & Environment Variables' },
  { value: 'testing-completion', label: 'Testing & Completion' },
]

const pipelineStages: { value: PipelineStage; label: string }[] = [
  { value: 'analyze', label: 'Analyze Repository' },
  { value: 'ideate', label: 'Generate Ideas' },
  { value: 'synthesize', label: 'Synthesize Tasks' },
  { value: 'precheck', label: 'Run Precheck' },
  { value: 'harbor_nop', label: 'Harbor NOP Validation' },
  { value: 'harbor_oracle', label: 'Harbor Oracle Validation' },
]

const cardClass =
  'rounded-2xl border border-white/[0.08] bg-[#0e1728] p-5 shadow-xl shadow-black/10 sm:p-6'

const inputClass =
  'w-full rounded-xl border border-white/[0.09] bg-[#080f1d] px-4 py-3 text-sm text-slate-200 outline-none transition placeholder:text-slate-600 hover:border-white/20 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 disabled:cursor-not-allowed disabled:opacity-50'

const labelClass =
  'mb-2 block text-sm font-medium text-slate-300'

export default function PipelineRunner() {
  const [repo, setRepo] = useState('pallets/click')
  const [baseCommit, setBaseCommit] = useState('')
  const [count, setCount] = useState(5)
  const [axes, setAxes] = useState<TaskAxis[]>(
    taskAxes.map((axis) => axis.value)
  )
  const [runHarbor, setRunHarbor] = useState(true)

  const [isRunning, setIsRunning] = useState(false)
  const [activeStage, setActiveStage] = useState(-1)
  const [completedStages, setCompletedStages] = useState<PipelineStage[]>([])
  const [error, setError] = useState('')
  const [isCompleted, setIsCompleted] = useState(false)

  const toggleAxis = (axis: TaskAxis) => {
    setAxes((current) =>
      current.includes(axis)
        ? current.filter((item) => item !== axis)
        : [...current, axis]
    )
  }
  const handleHarborChange = (checked: boolean) => {
    setRunHarbor(checked)
    setActiveStage(-1)
    setCompletedStages([])
    setIsCompleted(false)
    setError('')
  }
  const startMockPipeline = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (!repo.trim()) {
      setError('Please enter a repository name.')
      return
    }

    if (!/^[a-fA-F0-9]{40}$/.test(baseCommit.trim())) {
      setError('Please enter a valid 40-character Git commit SHA.')
      return
    }

    if (count < 1 || count > 5) {
      setError('Task count must be between 1 and 5.')
      return
    }

    if (axes.length === 0) {
      setError('Please select at least one task axis.')
      return
    }

    setIsRunning(true)
    setIsCompleted(false)
    setActiveStage(-1)
    setCompletedStages([])

    const stagesToRun = runHarbor
      ? pipelineStages
      : pipelineStages.slice(0, 4)

    for (let index = 0; index < stagesToRun.length; index++) {
      setActiveStage(index)

      await new Promise<void>((resolve) => {
        window.setTimeout(resolve, 900)
      })

      setCompletedStages((current) => [
        ...current,
        stagesToRun[index].value,
      ])
    }

    setIsRunning(false)
    setIsCompleted(true)
  }

  const progress = Math.round(
    (completedStages.length / (runHarbor ? 6 : 4)) * 100
  )

  return (
    <section className="space-y-6">

      {/* Mock Mode Notice */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-400/20 bg-amber-400/[0.06] p-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-400/10 text-amber-300">
          !
        </div>
        <div>
          <p className="text-sm font-semibold text-amber-300">
            Mock Mode
          </p>
          <p className="mt-1 text-xs leading-5 text-amber-200/70 sm:text-sm">
            Pipeline progress is currently simulated. Backend integration
            will be connected when the FastAPI server is ready.
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid items-start gap-6 xl:grid-cols-2">

        {/* Pipeline Configuration */}
        <form onSubmit={startMockPipeline} className={cardClass}>

          <div className="mb-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
                <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth="1.8">
                  <path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.64 5.64l2.12 2.12m8.48 8.48 2.12 2.12m0-12.72-2.12 2.12m-8.48 8.48-2.12 2.12" strokeLinecap="round" />
                  <circle cx="12" cy="12" r="4" />
                </svg>
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">
                  Pipeline Configuration
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Configure your task generation run
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-5">

            {/* Repository */}
            <div>
              <label className={labelClass}>
                GitHub Repository
              </label>
              <input
                value={repo}
                onChange={(event) => setRepo(event.target.value)}
                placeholder="pallets/click"
                disabled={isRunning}
                className={inputClass}
              />
            </div>

            {/* Base Commit */}
            <div>
              <label className={labelClass}>
                Base Commit SHA
              </label>
              <input
                value={baseCommit}
                onChange={(event) => setBaseCommit(event.target.value)}
                placeholder="Enter the pinned 40-character commit SHA"
                disabled={isRunning}
                className={`${inputClass} font-mono`}
              />
              <p className="mt-2 text-xs leading-5 text-slate-500">
                Use the exact commit SHA selected by the team.
              </p>
            </div>

            {/* Task Count */}
            <div>
              <label className={labelClass}>
                Number of Tasks
              </label>
              <select
                value={count}
                onChange={(event) => setCount(Number(event.target.value))}
                disabled={isRunning}
                className={inputClass}
              >
                {[1, 2, 3, 4, 5].map((number) => (
                  <option key={number} value={number} className="bg-[#0e1728]">
                    {number} {number === 1 ? 'Task' : 'Tasks'}
                  </option>
                ))}
              </select>
            </div>

            {/* Task Axes */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200">
                  Task Generation Axes
                </h3>
                <span className="text-xs text-slate-500">
                  {axes.length}/5 selected
                </span>
              </div>

              <div className="grid gap-2 sm:grid-cols-2">
                {taskAxes.map((axis) => {
                  const selected = axes.includes(axis.value)

                  return (
                    <label
                      key={axis.value}
                      className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition ${
                        selected
                          ? 'border-blue-500/30 bg-blue-500/[0.07]'
                          : 'border-white/[0.06] bg-[#080f1d] hover:border-white/15'
                      } ${isRunning ? 'cursor-not-allowed opacity-50' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => toggleAxis(axis.value)}
                        disabled={isRunning}
                        className="h-4 w-4 shrink-0 accent-blue-500"
                      />
                      <span className={`text-xs font-medium leading-5 ${
                        selected ? 'text-blue-200' : 'text-slate-400'
                      }`}>
                        {axis.label}
                      </span>
                    </label>
                  )
                })}
              </div>
            </div>

            {/* Harbor Validation */}
            <label className={`flex cursor-pointer items-center gap-3 rounded-xl border border-white/[0.07] bg-[#080f1d] p-4 transition hover:border-white/15 ${
              isRunning ? 'cursor-not-allowed opacity-50' : ''
            }`}>
              <input
                type="checkbox"
                checked={runHarbor}
                onChange={(event) => handleHarborChange(event.target.checked)}
                disabled={isRunning}
                className="h-4 w-4 shrink-0 accent-blue-500"
              />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-slate-200">
                  Run Harbor Validation
                </span>
                <span className="mt-1 block text-xs text-slate-500">
                  NOP + Oracle validation
                </span>
              </span>
              <span className="rounded-md bg-blue-500/10 px-2 py-1 text-[10px] font-semibold text-blue-300">
                OPTIONAL
              </span>
            </label>

            {/* Error */}
            {error && (
              <div className="rounded-xl border border-red-500/20 bg-red-500/[0.07] p-3 text-sm text-red-300">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isRunning}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/15 transition hover:bg-blue-500 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Pipeline Running...
                </>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14m-6-6 6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Run Pipeline
                </>
              )}
            </button>
          </div>
        </form>

        {/* Pipeline Progress */}
        <div className={`${cardClass} xl:sticky xl:top-28`}>

          <div className="mb-7 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
                <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth="1.8">
                  <path d="M4 18V6m5 12V10m5 8V4m5 14v-6" strokeLinecap="round" />
                </svg>
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">
                  Pipeline Progress
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Task generation and validation stages
                </p>
              </div>
            </div>

            <span className={`rounded-full border px-3 py-1 text-[10px] font-semibold ${
              isCompleted
                ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300'
                : isRunning
                  ? 'border-blue-400/20 bg-blue-400/10 text-blue-300'
                  : 'border-white/[0.08] bg-white/[0.04] text-slate-400'
            }`}>
              {isCompleted ? 'COMPLETED' : isRunning ? 'RUNNING' : 'WAITING'}
            </span>
          </div>

          {/* Progress Percentage */}
          <div className="rounded-xl border border-white/[0.06] bg-[#080f1d] p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">
                Overall Progress
              </span>
              <span className="font-mono text-lg font-bold text-blue-400">
                {progress}%
              </span>
            </div>

            <div
              className="h-2 overflow-hidden rounded-full bg-slate-800"
              role="progressbar"
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-600 to-cyan-400 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>

            <p className="mt-3 text-xs text-slate-500">
              {completedStages.length} of {runHarbor ? 6 : 4} stages completed
            </p>
          </div>

          {/* Pipeline Stages */}
          <div className="mt-7">
            <h3 className="mb-5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Execution Stages
            </h3>

            <div className="space-y-0">
              {pipelineStages
                .filter(
                  (stage) =>
                    runHarbor ||
                    !['harbor_nop', 'harbor_oracle'].includes(stage.value)
                )
                .map((stage, index) => {
                  const isDone = completedStages.includes(stage.value)
                  const isActive =
                    isRunning &&
                    pipelineStages[activeStage]?.value === stage.value

                  const isLast = index === (runHarbor ? 5 : 3)

                  return (
                    <div key={stage.value} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition ${
                          isDone
                            ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300'
                            : isActive
                              ? 'border-blue-400/40 bg-blue-500/15 text-blue-300'
                              : 'border-white/[0.08] bg-[#080f1d] text-slate-600'
                        }`}>
                          {isDone ? (
                            '✓'
                          ) : isActive ? (
                            <span className="h-3 w-3 animate-spin rounded-full border-2 border-blue-300/30 border-t-blue-300" />
                          ) : (
                            String(index + 1).padStart(2, '0')
                          )}
                        </div>

                        {!isLast && (
                          <div className={`min-h-8 w-px ${
                            isDone ? 'bg-emerald-400/30' : 'bg-white/[0.08]'
                          }`} />
                        )}
                      </div>

                      <div className="min-w-0 flex-1 pb-7">
                        <p className={`text-sm font-semibold ${
                          isDone
                            ? 'text-emerald-300'
                            : isActive
                              ? 'text-blue-300'
                              : 'text-slate-400'
                        }`}>
                          {stage.label}
                        </p>

                        <p className="mt-1 text-xs text-slate-600">
                          {isDone
                            ? 'Completed'
                            : isActive
                              ? 'Processing stage...'
                              : 'Waiting'}
                        </p>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>

          {/* Completion Message */}
          {isCompleted && (
            <div className="mt-2 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07] p-4">
              <p className="text-sm font-semibold text-emerald-300">
                Mock pipeline completed successfully.
              </p>
              <p className="mt-1 text-xs text-emerald-200/60">
                This is a simulated result. Actual execution will use the backend.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
