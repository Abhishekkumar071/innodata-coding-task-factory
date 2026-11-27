

import { useState } from 'react'
import ReactDiffViewer from 'react-diff-viewer-continued'
import type {
  TaskInspector as TaskInspectorData,
  ValidationMode,
} from '../../types/api'

type InspectorTab =
  | 'toml'
  | 'instructions'
  | 'solution'
  | 'tests'
  | 'validation'

const mockTask: TaskInspectorData = {
  task_toml: `[task]
id = "task-001"
axis = "parameter-validation"
difficulty = "easy"
title = "Validate CLI Parameter Inputs"`,

  instruction_md: `# Task: Validate CLI Parameter Inputs

## Objective
Improve parameter validation in the Click command-line application.

## Requirements
- Validate user-provided parameter values.
- Reject None and empty string inputs with a clear error message.
- Preserve existing behaviour for valid inputs.

## Expected Result
Invalid parameter values should be rejected correctly.`,

 solution_patch: `diff --git a/src/click/core.py b/src/click/core.py
index 1234567..abcdef0 100644
--- a/src/click/core.py
+++ b/src/click/core.py
@@ -100,2 +100,6 @@
 def validate_parameter(value):
+    if value is None:
+        raise BadParameter("A value is required")
+    if isinstance(value, str) and not value.strip():
+        raise BadParameter("A value cannot be empty")
     return value`,

  feature_test_code: `def test_parameter_rejects_none():
    with pytest.raises(BadParameter):
        validate_parameter(None)


def test_parameter_rejects_invalid_value():
    with pytest.raises(BadParameter):
        validate_parameter("")`,

  fail_to_pass: [
    'test_parameter_rejects_none',
    'test_parameter_rejects_invalid_value',
  ],

  pass_to_pass: [
    'test_parameter_accepts_valid_value',
    'test_existing_command_behaviour',
  ],

  validations: [
    {
      task_id: 'task-001',
      mode: 'stage1_base',
      reward: null,
      passed_feature: 0,
      total_feature: 2,
      passed_regression: 2,
      total_regression: 2,
      duration_sec: 1.24,
      log_path: 'sample/logs/stage1_base.log',
    },
    {
      task_id: 'task-001',
      mode: 'stage1_oracle',
      reward: 0.9,
      passed_feature: 2,
      total_feature: 2,
      passed_regression: 2,
      total_regression: 2,
      duration_sec: 2.15,
      log_path: 'sample/logs/stage1_oracle.log',
    },
  ],

  package_path: 'sample/tasks/task-001',
}

const oldCode = `def validate_parameter(value):
    return value`

const newCode = `def validate_parameter(value):
    if value is None:
        raise BadParameter("A value is required")
    if isinstance(value, str) and not value.strip():
        raise BadParameter("A value cannot be empty")
    return value`

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

function getTabContent(tab: InspectorTab) {
  switch (tab) {
    case 'toml':
      return mockTask.task_toml
    case 'instructions':
      return mockTask.instruction_md
    case 'tests':
      return mockTask.feature_test_code
    default:
      return ''
  }
}

export default function TaskInspector() {
  const [activeTab, setActiveTab] = useState<InspectorTab>('toml')

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
                  task-001
                </h2>

                <span className="rounded-md border border-green-500/20 bg-green-500/10 px-2.5 py-1 text-xs font-semibold text-green-400">
                  EASY
                </span>
              </div>

              <p className="mt-2 text-base font-medium text-slate-200">
                Validate CLI Parameter Inputs
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Axis: parameter-validation
              </p>
            </div>

            <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/10">
              <span className="text-xl font-bold text-blue-400">T</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 border-t border-slate-700/70 pt-5 sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Feature Tests</p>
              <p className="mt-1 text-xl font-semibold text-white">2</p>
            </div>

            <div>
              <p className="text-xs text-slate-500">Regression Tests</p>
              <p className="mt-1 text-xl font-semibold text-white">2</p>
            </div>

            <div>
              <p className="text-xs text-slate-500">Validation Runs</p>
              <p className="mt-1 text-xl font-semibold text-white">2</p>
            </div>

            <div>
              <p className="text-xs text-slate-500">Oracle Reward</p>
              <p className="mt-1 text-xl font-semibold text-green-400">90%</p>
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

            <table className="w-full min-w-[700px] text-left text-sm">
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
                {mockTask.validations.map((result) => (
                  <tr key={result.mode}>
                    <td className="px-3 py-4 text-slate-200">
                      {modeLabels[result.mode]}
                    </td>

                    <td className="px-3 py-4 text-slate-300">
                      {result.reward === null
                        ? '—'
                        : `${(result.reward * 100).toFixed(0)}%`}
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
          </div>
        ) : activeTab === 'solution' ? (
          <div className="p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-slate-300">
                Solution Patch Comparison
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                Compare the original code with the modified code.
              </p>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-700">
              <ReactDiffViewer
                oldValue={oldCode}
                newValue={newCode}
                splitView={true}
                useDarkTheme={true}
                leftTitle="Original Code"
                rightTitle="Modified Code"
              />
            </div>

            <div className="mt-4">
              <p className="mb-2 text-xs font-medium text-slate-400">
                Unified Solution Patch
              </p>
              <pre className="max-h-[300px] overflow-auto rounded-lg border border-slate-800 bg-slate-950 p-4 text-sm leading-6 text-slate-300">
                <code>{mockTask.solution_patch}</code>
              </pre>
            </div>
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
                    : 'PYTHON'}
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
                    ? 'instructions.md'
                    : 'feature_tests.py'}
                </span>

                <span className="text-[10px] uppercase tracking-wider text-slate-600">
                Read only
                </span>
            </div>

            <div className="flex overflow-x-auto">
                <div className="select-none border-r border-slate-800 px-4 py-4 text-right font-mono text-xs leading-7 text-slate-600">
                {getTabContent(activeTab).split('\n').map((_, index) => (
                    <div key={index}>{index + 1}</div>
                ))}
                </div>

                <pre className="max-h-[500px] min-w-0 flex-1 overflow-auto p-4 font-mono text-[13px] leading-7 text-slate-300">
                <code>{getTabContent(activeTab)}</code>
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

          <ul className="space-y-2">
            {mockTask.fail_to_pass.map((test) => (
              <li
                key={test}
                className="break-all font-mono text-xs text-slate-400"
              >
                {test}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h3 className="mb-3 font-semibold text-white">
            Pass-to-Pass Tests
          </h3>

          <ul className="space-y-2">
            {mockTask.pass_to_pass.map((test) => (
              <li
                key={test}
                className="break-all font-mono text-xs text-slate-400"
              >
                {test}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Package Path */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <p className="text-sm text-slate-400">Package Path</p>
        <p className="mt-2 break-all font-mono text-sm text-slate-300">
          {mockTask.package_path}
        </p>
      </div>

    </section>
  )
}
