
import type {
  CreateRunRequest,
  CreateRunResponse,
  RunSummary,
  PipelineEvent,
  TaskSummary,
  TaskInspector,
  ValidationOutcome,
} from '../types/api'

// Backend API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Common API request handler
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const errorMessage = await response.text()
    throw new Error(
      errorMessage || `API Error: ${response.status}`
    )
  }

  return response.json() as Promise<T>
}

// 1. Create a pipeline run
export function createRun(
  data: CreateRunRequest
): Promise<CreateRunResponse> {
  return apiRequest<CreateRunResponse>('/api/runs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// 2. Get pipeline run details
export function getRun(
  runId: string
): Promise<RunSummary> {
  return apiRequest<RunSummary>(
    `/api/runs/${encodeURIComponent(runId)}`
  )
}

// 3. Get all generated tasks
export function getTasks(): Promise<TaskSummary[]> {
  return apiRequest<TaskSummary[]>('/api/tasks')
}

// 4. Get individual task details
export function getTask(
  taskId: string
): Promise<TaskInspector> {
  return apiRequest<TaskInspector>(
    `/api/tasks/${encodeURIComponent(taskId)}`
  )
}

// 5. Validate a generated task
export function validateTask(
  taskId: string
): Promise<ValidationOutcome[]> {
  return apiRequest<ValidationOutcome[]>(
    `/api/tasks/${encodeURIComponent(taskId)}/validate`,
    {
      method: 'POST',
    }
  )
}

// 6. Export a task as ZIP
export async function exportTask(
  taskId: string
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskId)}/export`
  )

  if (!response.ok) {
    throw new Error(`Export failed: ${response.status}`)
  }

  return response.blob()
}

// 7. Subscribe to live pipeline events using SSE
export function subscribeToRunEvents(
  runId: string,
  onEvent: (event: PipelineEvent) => void,
  onError?: () => void
): EventSource {
  const eventSource = new EventSource(
    `${API_BASE_URL}/api/runs/${encodeURIComponent(runId)}/events`
  )

  eventSource.onmessage = (message: MessageEvent) => {
    try {
      const event = JSON.parse(
        message.data
      ) as PipelineEvent

      onEvent(event)
    } catch (error) {
      console.error('Failed to parse pipeline event:', error)
    }
  }

  eventSource.onerror = () => {
    onError?.()
  }

  return eventSource
}
