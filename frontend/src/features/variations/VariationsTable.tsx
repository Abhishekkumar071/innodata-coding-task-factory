

import type { TaskSummary, TaskAxis } from '../../types/api'

const mockTasks: TaskSummary[] = [
  {
    task_id: 'task-001',
    axis: 'parameter-validation',
    title: 'Validate CLI Parameter Inputs',
    difficulty: 'easy',
    repair_attempts: 1,
    nop_reward: 0.85,
    oracle_reward: 0.90,
    mutation_killed: 0,
    mutation_total: 0,
  },
  {
    task_id: 'task-002',
    axis: 'command-routing',
    title: 'Fix Command Routing Behaviour',
    difficulty: 'medium',
    repair_attempts: 2,
    nop_reward: 0.80,
    oracle_reward: 0.88,
    mutation_killed: 0,
    mutation_total: 0,
  },
  {
    task_id: 'task-003',
    axis: 'formatting-termui',
    title: 'Improve Terminal Output Formatting',
    difficulty: 'medium',
    repair_attempts: 1,
    nop_reward: 0.75,
    oracle_reward: 0.82,
    mutation_killed: 0,
    mutation_total: 0,
  },
  {
    task_id: 'task-004',
    axis: 'context-envvar',
    title: 'Handle Environment Variables',
    difficulty: 'hard',
    repair_attempts: 3,
    nop_reward: 0.90,
    oracle_reward: 0.92,
    mutation_killed: 0,
    mutation_total: 0,
  },
  {
    task_id: 'task-005',
    axis: 'testing-completion',
    title: 'Improve Test Completion Handling',
    difficulty: 'easy',
    repair_attempts: 1,
    nop_reward: 0.88,
    oracle_reward: 0.91,
    mutation_killed: 0,
    mutation_total: 0,
  },
]

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
  return reward === null ? '—' : `${(reward * 100).toFixed(0)}%`
}

const summaryCards = [
  {
    label: 'Total Tasks',
    value: mockTasks.length,
    description: 'Sample task records',
    icon: 'T',
    iconStyle: 'bg-blue-500/10 text-blue-400',
  },
  {
    label: 'Task Axes Covered',
    value: new Set(mockTasks.map((task) => task.axis)).size,
    description: 'Across five task categories',
    icon: 'A',
    iconStyle: 'bg-violet-500/10 text-violet-400',
  },
  {
    label: 'Total Repair Attempts',
    value: mockTasks.reduce(
      (total, task) => total + task.repair_attempts,
      0
    ),
    description: 'Recorded in sample data',
    icon: 'R',
    iconStyle: 'bg-emerald-500/10 text-emerald-400',
  },
]

export default function VariationsTable() {
  return (
    <section className="space-y-6">

      {/* Mock Data Notice */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-400/20 bg-amber-400/[0.06] p-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-400/10 text-amber-300">
          !
        </div>
        <div>
          <p className="text-sm font-semibold text-amber-300">
            Mock Data
          </p>
          <p className="mt-1 text-xs leading-5 text-amber-200/70 sm:text-sm">
            These five tasks are sample records for UI development.
            Actual task data will be loaded from the backend later.
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

              <div className={`flex h-11 w-11 items-center justify-center rounded-xl text-sm font-bold ${card.iconStyle}`}>
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

          <span className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400">
            {mockTasks.length} Sample Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[950px] text-left text-sm">

            <thead className="bg-[#080f1d]">
              <tr className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                <th className="px-5 py-4">Task ID</th>
                <th className="px-5 py-4">Title</th>
                <th className="px-5 py-4">Axis</th>
                <th className="px-5 py-4">Difficulty</th>
                <th className="px-5 py-4">Repair Attempts</th>
                <th className="px-5 py-4">NOP Reward</th>
                <th className="px-5 py-4">Oracle Reward</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/[0.05]">
              {mockTasks.map((task) => (
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

                  <td className="px-5 py-5 font-mono font-medium text-slate-300">
                    {formatReward(task.nop_reward)}
                  </td>

                  <td className="px-5 py-5 font-mono font-medium text-slate-300">
                    {formatReward(task.oracle_reward)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/[0.07] px-5 py-4 sm:px-6">
          <p className="text-xs text-slate-500">
            Showing {mockTasks.length} sample tasks
          </p>
          <p className="text-xs text-slate-600">
            Coding Task Factory
          </p>
        </div>
      </div>
    </section>
  )
}
