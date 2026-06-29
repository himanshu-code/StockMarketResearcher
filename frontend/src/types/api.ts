// TypeScript interfaces mirroring the FastAPI backend schemas

// ── Request / Response ─────────────────────────────────────────────────────

export interface ResearchRequest {
  ticker: string
}

export interface ResearchSubmitResponse {
  job_id: string
  message: string
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed'

export interface ResearchJobResponse {
  job_id: string
  ticker: string
  status: JobStatus
  report: string | null
  error: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface ResearchReportItem {
  job_id: string
  ticker: string
  status: JobStatus
  report: string
  created_at: string
  updated_at: string
}

// ── SSE Events ─────────────────────────────────────────────────────────────

export type SentimentLabel = 'positive' | 'negative' | 'neutral'

export interface AgentStartedData {
  job_id: string
  ticker: string
}

export interface ResearcherData {
  job_id: string
  iteration: number
  ticker: string
  market_data: {
    current_price?: number
    percentage_change?: number
    currency?: string
    trend?: string
    high_52w?: number
    low_52w?: number
  }
  news_sentiment: {
    label?: SentimentLabel
    score?: number
    positive_headlines?: number
    negative_headlines?: number
    neutral_headlines?: number
    top_headlines?: string[]
  }
  fundamentals: {
    company_name?: string
    sector?: string
    industry?: string
    market_cap?: number
    revenue?: number
    net_income?: number
    fiscal_year?: number
    currency?: string
  }
  status?: string
}

export interface CritiqueData {
  job_id: string
  iteration: number
  approved: boolean
  critique: string
  missing: string[]
}

export interface ReportReadyData {
  job_id: string
  ticker: string
  report: string
}

export interface AgentFailedData {
  job_id: string
  error: string
}

export type SSEEventType =
  | 'agent_started'
  | 'researcher'
  | 'critic'
  | 'report'
  | 'agent_done'
  | 'report_ready'
  | 'agent_failed'

export interface SSEEvent<T = unknown> {
  seq: number
  event: SSEEventType
  data: T
  created_at: string
}

// ── Agent step model for UI ─────────────────────────────────────────────────

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface AgentStep {
  key: string
  label: string
  status: StepStatus
  iteration?: number
  message?: string
}
