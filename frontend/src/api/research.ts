import type {
  ResearchSubmitResponse,
  ResearchJobResponse,
  ResearchReportItem,
} from '../types/api'
import { apiClient } from './client'

/** Start a new research job for the given ticker. */
export async function postResearch(ticker: string): Promise<ResearchSubmitResponse> {
  const { data } = await apiClient.post<ResearchSubmitResponse>('/research', { ticker })
  return data
}

/** Get the current state of a research job (status, report, error). */
export async function getResearch(jobId: string): Promise<ResearchJobResponse> {
  const { data } = await apiClient.get<ResearchJobResponse>(`/research/${jobId}`)
  return data
}

/** List all completed research reports (in-memory, resets on server restart). */
export async function getReports(): Promise<ResearchReportItem[]> {
  const { data } = await apiClient.get<ResearchReportItem[]>('/reports')
  return data
}
