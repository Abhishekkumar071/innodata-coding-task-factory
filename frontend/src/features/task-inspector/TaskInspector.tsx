
import { useEffect, useState } from 'react'
import type {
  TaskInspector as TaskInspectorData,
  TaskSummary,
  ValidationMode,
} from '../../types/api'
import { getTask } from '../../services/api'

interface TaskInspectorProps {
  task: TaskSummary | null
}

type InspectorTab =
  | 'toml'
  | 'instructions'
  | 'solution'
  | 'tests'
  | 'validation'

interface LoadedTask {
  taskId: string
  data: TaskInspectorData
}

interface TaskError {
  taskId: string
  message: string
}

const tabs: { value: InspectorTab; label: string }[] = [
  { value: 'toml', label: 'Task TOML' },
  { value: 'instructions', label: 'Instructions' },
  { value: 'solution', label: 'Solution Patch' },
  { value: 'tests', label: 'Feature Tests' },
  { value: 'validation', label: 'Validation Results' },
]

const modeLabels: Record<ValidationMode, string> = {
  stage1_base: 'Stage 1 Base',
  stage1_oracle: 'Stage 1 Oracle',
  harbor_nop: 'Harbor NOP',
  harbor_oracle: 'Harbor Oracle',
  mutant: 'Mutant',
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

function getTabContent(
  tab: InspectorTab,
  data: TaskInspectorData
): string {
  switch (tab) {
    case 'toml':
      return data.task_toml
    case 'instructions':
      return data.instruction_md
    case 'solution':
      return data.solution_patch
    case 'tests':
      return data.feature_test_code
    case 'validation':
      return ''
  }
}

export default function TaskInspector({ task }: TaskInspectorProps) {
  const [activeTab, setActiveTab] = useState<InspectorTab>('toml')
  const [loadedTask, setLoadedTask] = useState<LoadedTask | null>(null)
  const [taskError, setTaskError] = useState<TaskError | null>(null)

  useEffect(() => {
    const taskId = task?.task_id

    if (!taskId) {
      return
    }

    let isActive = true

    getTask(taskId)
      .then((data) => {
        if (isActive) {
          setLoadedTask({
            taskId,
            data,
          })
          setTaskError(null)
        }
      })
      .catch((err: unknown) => {
        if (isActive) {
          setTaskError({
            taskId,
            message:
              err instanceof Error
                ? err.message
                : 'Unable to load task details from the backend.',
          })
        }
      })

    return () => {
      isActive = false
    }
  }, [task?.task_id])

  if (!task) {
    return (
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-10 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-blue-400/20 bg-blue-400/[0.08] text-xl font-bold text-blue-300">
          T
        </div>

        <h2 className="mt-4 text-base font-semibold text-white">
          No Task Selected
        </h2>

        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-400">
          Open the Variations page and select a task using its Inspect
          button to view its files and validation details.
        </p>
      </section>
    )
  }

  const isCurrentTaskLoaded = loadedTask?.taskId === task.task_id
  const currentError =
    taskError?.taskId === task.task_id ? taskError.message : null

  if (!isCurrentTaskLoaded && !currentError) {
    return (
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-10 text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-blue-400" />

        <p className="mt-4 text-sm font-medium text-slate-300">
          Loading task details...
        </p>

        <p className="mt-2 text-xs text-slate-500">
          Fetching task {task.task_id} from the backend.
        </p>
      </section>
    )
  }

  if (currentError) {
    return (
      <section className="rounded-xl border border-red-400/20 bg-slate-900 p-8 text-center">
        <h2 className="text-base font-semibold text-red-300">
          Unable to load task details
        </h2>

        <p className="mt-3 break-words text-sm text-slate-400">
          {currentError}
        </p>

        <p className="mt-3 text-xs text-slate-500">
          Task ID: {task.task_id}
        </p>
      </section>
    )
  }

  if (!loadedTask || loadedTask.taskId !== task.task_id) {
    return null
  }

  const data = loadedTask.data

  const oracleValidation = data.validations.find(
    (result) =>
      result.mode === 'harbor_oracle' ||
      result.mode === 'stage1_oracle'
  )

  const featureTestCount = data.fail_to_pass.length
  const regressionTestCount = data.pass_to_pass.length
  const validationCount = data.validations.length

  return (
    <section className="space-y-6">
      {/* Selected Task Overview */}
      <div className="relative overflow-hidden rounded-xl border border-slate-700/80 bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950/40 p-5 sm:p-6">
        <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-blue-500/5 blur-3xl" />

        <div className="relative">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                Currently Selected Task
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-3">
                <h2 className="font-mono text-2xl font-bold text-blue-400">
                  {task.task_id}
                </h2>

                <span
                  className={`rounded-md border px-2.5 py-1 text-xs font-semibold uppercase ${getDifficultyStyle(task.difficulty)}`}
                >
                  {task.difficulty}
                </span>
              </div>

              <p className="mt-2 text-base font-medium text-slate-200">
                {task.title}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Axis: {task.axis}
              </p>
            </div>

            <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/10">
              <span className="text-xl font-bold text-blue-400">T</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 border-t border-slate-700/70 pt-5 sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Fail-to-Pass Tests</p>
              <p className="mt-1 text-xl font-semibold text-white">
                {featureTestCount}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-500">Pass-to-Pass Tests</p>
              <p className="mt-1 text-xl font-semibold text-white">
                {regressionTestCount}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-500">Validation Runs</p>
              <p className="mt-1 text-xl font-semibold text-white">
                {validationCount}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-500">Oracle Reward</p>
              <p className="mt-1 text-xl font-semibold text-green-400">
                {formatReward(oracleValidation?.reward ?? null)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* File Tabs and Content */}
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <div className="flex gap-1 overflow-x-auto border-b border-slate-700/80 bg-slate-950/50 px-3 pt-3">
          {tabs.map((tab, index) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setActiveTab(tab.value)}
              className={`relative shrink-0 rounded-t-lg px-4 py-3 text-sm font-medium transition-all duration-200 ${
                activeTab === tab.value
                  ? 'border border-b-0 border-blue-500/30 bg-slate-900 text-blue-400'
                  : 'border border-transparent text-slate-400 hover:bg-slate-800/70 hover:text-slate-200'
              }`}
            >
              <span className="mr-2 text-[10px] text-slate-500">
                0{index + 1}
              </span>

              {tab.label}

              {activeTab === tab.value && (
                <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-blue-500" />
              )}
            </button>
          ))}
        </div>

        {activeTab === 'validation' ? (
          <div className="overflow-x-auto p-5">
            <h3 className="mb-4 text-base font-semibold text-white">
              Validation Results
            </h3>

            {data.validations.length === 0 ? (
              <p className="rounded-lg border border-slate-800 bg-slate-950/50 p-5 text-sm text-slate-400">
                No validation results are available for this task yet.
              </p>
            ) : (
              <>
                <table className="w-full min-w-[800px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-3 py-3">Validation Mode</th>
                      <th className="px-3 py-3">Reward</th>
                      <th className="px-3 py-3">Feature Tests</th>
                      <th className="px-3 py-3">Regression Tests</th>
                      <th className="px-3 py-3">Duration</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-800">
                    {data.validations.map((result, index) => (
                      <tr key={`${result.mode}-${index}`}>
                        <td className="px-3 py-4 text-slate-200">
                          {modeLabels[result.mode]}
                        </td>

                        <td className="px-3 py-4 text-slate-300">
                          {formatReward(result.reward)}
                        </td>

                        <td className="px-3 py-4 text-slate-300">
                          {result.passed_feature}/{result.total_feature}
                        </td>

                        <td className="px-3 py-4 text-slate-300">
                          {result.passed_regression}/{result.total_regression}
                        </td>

                        <td className="px-3 py-4 text-slate-300">
                          {result.duration_sec.toFixed(2)}s
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div className="mt-6">
                  <h4 className="mb-3 text-sm font-semibold text-white">
                    Harbor Trial Log Paths
                  </h4>

                  <div className="space-y-3">
                    {data.validations.map((result, index) => (
                      <div
                        key={`${result.mode}-log-${index}`}
                        className="rounded-lg border border-slate-800 bg-slate-950/50 p-3"
                      >
                        <p className="text-xs font-medium text-slate-300">
                          {modeLabels[result.mode]}
                        </p>

                        <p className="mt-2 break-all font-mono text-xs text-blue-300">
                          {result.log_path}
                        </p>
                      </div>
                    ))}
                  </div>

                  <p className="mt-3 text-xs leading-5 text-slate-500">
                    The current API response provides log paths but does not
                    provide raw Harbor log contents.
                  </p>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-white">
                  {tabs.find((tab) => tab.value === activeTab)?.label}
                </h3>

                <p className="mt-1 text-xs text-slate-500">
                  Task Inspector / {activeTab}
                </p>
              </div>

              <span className="rounded-md border border-slate-700 bg-slate-800/70 px-2.5 py-1 text-[11px] font-medium text-slate-400">
                {activeTab === 'toml'
                  ? 'TOML'
                  : activeTab === 'instructions'
                    ? 'MARKDOWN'
                    : 'PYTHON / DIFF'}
              </span>
            </div>

            <div className="overflow-hidden rounded-xl border border-slate-700/80 bg-[#080e19]">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-400/80" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
                  <span className="h-2.5 w-2.5 rounded-full bg-green-400/80" />
                </div>

                <span className="font-mono text-[11px] text-slate-500">
                  {activeTab === 'toml'
                    ? 'task.toml'
                    : activeTab === 'instructions'
                      ? 'instruction.md'
                      : activeTab === 'solution'
                        ? 'solution.patch'
                        : 'feature_tests.py'}
                </span>

                <span className="text-[10px] uppercase tracking-wider text-slate-600">
                  Read only
                </span>
              </div>

              <div className="flex overflow-x-auto">
                <div className="select-none border-r border-slate-800 px-4 py-4 text-right font-mono text-xs leading-7 text-slate-600">
                  {getTabContent(activeTab, data)
                    .split('\n')
                    .map((_, index) => (
                      <div key={index}>{index + 1}</div>
                    ))}
                </div>

                <pre className="max-h-[500px] min-w-0 flex-1 overflow-auto p-4 font-mono text-[13px] leading-7 text-slate-300">
                  <code>{getTabContent(activeTab, data)}</code>
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Test Groups */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h3 className="mb-3 font-semibold text-white">
            Fail-to-Pass Tests
          </h3>

          {data.fail_to_pass.length === 0 ? (
            <p className="text-xs text-slate-500">
              No fail-to-pass tests provided.
            </p>
          ) : (
            <ul className="space-y-2">
              {data.fail_to_pass.map((test, index) => (
                <li
                  key={`${test}-${index}`}
                  className="break-all font-mono text-xs text-slate-400"
                >
                  {test}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h3 className="mb-3 font-semibold text-white">
            Pass-to-Pass Tests
          </h3>

          {data.pass_to_pass.length === 0 ? (
            <p className="text-xs text-slate-500">
              No pass-to-pass tests provided.
            </p>
          ) : (
            <ul className="space-y-2">
              {data.pass_to_pass.map((test, index) => (
                <li
                  key={`${test}-${index}`}
                  className="break-all font-mono text-xs text-slate-400"
                >
                  {test}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Package Path */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <p className="text-sm text-slate-400">Package Path</p>

        <p className="mt-2 break-all font-mono text-sm text-slate-300">
          {data.package_path}
        </p>
      </div>
    </section>
  )
}
