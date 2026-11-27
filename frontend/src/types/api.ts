
export type TaskAxis =
  | 'parameter-validation'
  | 'command-routing'
  | 'formatting-termui'
  | 'context-envvar'
  | 'testing-completion'

export type TaskDifficulty = 'easy' | 'medium' | 'hard'

export type RunStatus = 'queued' | 'running' | 'completed' | 'failed'

export type PipelineStage =
  | 'analyze'
  | 'ideate'
  | 'synthesize'
  | 'precheck'
  | 'harbor_nop'
  | 'harbor_oracle'
  | 'mutate'

export interface CreateRunRequest {
  repo: string
  base_commit: string
  count: number
  axes?: TaskAxis[]
  run_harbor: boolean
  run_mutations?: boolean
}

export interface CreateRunResponse {
  run_id: string
  status: 'queued'
}

export interface RunSummary {
  run_id: string
  repo: string
  base_commit: string
  status: RunStatus
  tasks_generated: number
  created_at: string
  completed_at: string | null
}

export interface PipelineEvent {
  stage: PipelineStage
  task_id: string
  message: string
  timestamp: string
}

export interface TaskSummary {
  task_id: string
  axis: TaskAxis
  title: string
  difficulty: TaskDifficulty
  repair_attempts: number
  nop_reward: number | null
  oracle_reward: number | null
  mutation_killed: number
  mutation_total: number
}

export type ValidationMode =
  | 'stage1_base'
  | 'stage1_oracle'
  | 'harbor_nop'
  | 'harbor_oracle'
  | 'mutant'

export interface ValidationOutcome {
  task_id: string
  mode: ValidationMode
  reward: number | null
  passed_feature: number
  total_feature: number
  passed_regression: number
  total_regression: number
  duration_sec: number
  log_path: string
}

export interface TaskInspector {
  task_toml: string
  instruction_md: string
  solution_patch: string
  feature_test_code: string
  fail_to_pass: string[]
  pass_to_pass: string[]
  validations: ValidationOutcome[]
  package_path: string
}
