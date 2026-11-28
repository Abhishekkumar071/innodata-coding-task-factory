
import { useCallback, useEffect, useState } from 'react'
import type { TaskSummary, TaskAxis } from '../../types/api'
import { getTasks } from '../../services/api'

interface VariationsTableProps {
  onSelectTask: (task: TaskSummary) => void
}

const axisLabels: Record<TaskAxis, string> = {
  'parameter-validation': 'Parameter Validation',
  'command-routing': 'Command Routing',
  'formatting-termui': 'Formatting & TermUI',
  'context-envvar': 'Context & Environment',
  'testing-completion': 'Testing & Completion',
}

function getDifficultyStyle(difficulty: TaskSummary['difficulty']) {
  switch (difficulty) {
    case 'easy':
      return 'border-emerald-400/20 bg-emerald-400/[0.08] text-emerald-300'
    case 'medium':
      return 'border-amber-400/20 bg-amber-400/[0.08] text-amber-300'
    case 'hard':
      return 'border-red-400/20 bg-red-400/[0.08] text-red-300'
  }
}

function formatReward(reward: number | null) {
  return reward === null ? 'Pending' : `${(reward * 100).toFixed(0)}%`
}

function RewardBadge({ reward }: { reward: number | null }) {
  return (
    <span className="inline-flex rounded-full border border-blue-400/20 bg-blue-400/[0.08] px-2.5 py-1 text-xs font-semibold text-blue-300">
      {formatReward(reward)}
    </span>
  )
}

export default function VariationsTable({
  onSelectTask,
}: VariationsTableProps) {
  const [tasks, setTasks] = useState<TaskSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadTasks = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const data = await getTasks()
      setTasks(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load task data from the backend.'
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let isActive = true

    getTasks()
      .then((data) => {
        if (isActive) {
          setTasks(data)
        }
      })
      .catch((err: unknown) => {
        if (isActive) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load task data from the backend.'
          )
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [])

  const totalAxes = new Set(tasks.map((task) => task.axis)).size

  const totalRepairs = tasks.reduce(
    (total, task) => total + task.repair_attempts,
    0
  )

  const summaryCards = [
    {
      label: 'Total Tasks',
      value: tasks.length,
      description: 'Tasks received from backend',
      icon: 'T',
      iconStyle: 'bg-blue-500/10 text-blue-400',
    },
    {
      label: 'Task Axes Covered',
      value: totalAxes,
      description: 'Across five task categories',
      icon: 'A',
      iconStyle: 'bg-violet-500/10 text-violet-400',
    },
    {
      label: 'Total Repair Attempts',
      value: totalRepairs,
      description: 'Recorded repair attempts',
      icon: 'R',
      iconStyle: 'bg-emerald-500/10 text-emerald-400',
    },
  ]

  return (
    <section className="space-y-6">
      {/* Backend Data Status */}
      <div className="flex items-start gap-3 rounded-xl border border-blue-400/20 bg-blue-400/[0.06] p-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-400/10 text-blue-300">
          i
        </div>

        <div>
          <p className="text-sm font-semibold text-blue-300">
            Live Backend Data
          </p>

          <p className="mt-1 text-xs leading-5 text-blue-200/70 sm:text-sm">
            Task variations are loaded from the backend API. Only tasks
            returned by the API are displayed.
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className="group rounded-2xl border border-white/[0.08] bg-[#0e1728] p-5 transition duration-200 hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-[#111d31]"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">
                  {card.label}
                </p>

                <p className="mt-3 font-mono text-3xl font-bold tracking-tight text-white">
                  {card.value}
                </p>
              </div>

              <div
                className={`flex h-11 w-11 items-center justify-center rounded-xl text-sm font-bold ${card.iconStyle}`}
              >
                {card.icon}
              </div>
            </div>

            <p className="mt-4 border-t border-white/[0.06] pt-3 text-xs text-slate-500">
              {card.description}
            </p>
          </div>
        ))}
      </div>

      {/* Task Table */}
      <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0e1728] shadow-xl shadow-black/10">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.07] p-5 sm:px-6">
          <div>
            <h2 className="text-base font-semibold text-white">
              Generated Task Variations
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Task details and validation rewards
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400">
              {tasks.length} Tasks
            </span>

            <button
              type="button"
              onClick={() => void loadTasks()}
              disabled={isLoading}
              className="rounded-lg border border-white/[0.10] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/[0.08] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="p-10 text-center">
            <p className="text-sm font-medium text-slate-300">
              Loading task variations...
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Fetching task data from the backend.
            </p>
          </div>
        ) : error ? (
          <div className="p-10 text-center">
            <p className="text-sm font-semibold text-red-300">
              Unable to load task variations
            </p>

            <p className="mt-2 break-words text-xs text-slate-400">
              {error}
            </p>

            <button
              type="button"
              onClick={() => void loadTasks()}
              className="mt-5 rounded-lg border border-red-400/20 bg-red-400/[0.08] px-4 py-2 text-xs font-semibold text-red-300 transition hover:bg-red-400/[0.14]"
            >
              Try Again
            </button>
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-10 text-center">
            <p className="text-sm font-semibold text-slate-300">
              No tasks available yet
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Generated tasks will appear here after a pipeline run.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1250px] text-left text-sm">
              <thead className="bg-[#080f1d]">
                <tr className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-4">Task ID</th>
                  <th className="px-5 py-4">Title</th>
                  <th className="px-5 py-4">Axis</th>
                  <th className="px-5 py-4">Target Module(s)</th>
                  <th className="px-5 py-4">Difficulty</th>
                  <th className="px-5 py-4">Repair Attempts</th>
                  <th className="px-5 py-4">NOP Reward</th>
                  <th className="px-5 py-4">Oracle Reward</th>
                  <th className="px-5 py-4">Action</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-white/[0.05]">
                {tasks.map((task) => (
                  <tr
                    key={task.task_id}
                    className="transition-colors duration-150 hover:bg-white/[0.035]"
                  >
                    <td className="whitespace-nowrap px-5 py-5">
                      <span className="rounded-md border border-blue-400/15 bg-blue-400/[0.07] px-2.5 py-1.5 font-mono text-xs font-semibold text-blue-300">
                        {task.task_id}
                      </span>
                    </td>

                    <td className="px-5 py-5">
                      <span className="font-medium text-slate-200">
                        {task.title}
                      </span>
                    </td>

                    <td className="px-5 py-5 text-xs text-slate-400">
                      {axisLabels[task.axis]}
                    </td>

                    <td className="px-5 py-5 text-xs text-slate-500">
                      Not provided by API
                    </td>

                    <td className="px-5 py-5">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize ${getDifficultyStyle(task.difficulty)}`}
                      >
                        {task.difficulty}
                      </span>
                    </td>

                    <td className="px-5 py-5 font-mono text-slate-300">
                      {task.repair_attempts}
                    </td>

                    <td className="px-5 py-5">
                      <RewardBadge reward={task.nop_reward} />
                    </td>

                    <td className="px-5 py-5">
                      <RewardBadge reward={task.oracle_reward} />
                    </td>

                    <td className="px-5 py-5">
                      <button
                        type="button"
                        onClick={() => onSelectTask(task)}
                        className="rounded-lg border border-blue-400/20 bg-blue-400/[0.08] px-3 py-2 text-xs font-semibold text-blue-300 transition hover:bg-blue-400/[0.15]"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/[0.07] px-5 py-4 sm:px-6">
          <p className="text-xs text-slate-500">
            Showing {tasks.length} backend task(s)
          </p>

          <p className="text-xs text-slate-600">
            Coding Task Factory
          </p>
        </div>
      </div>
    </section>
  )
}
