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

/** Export a completed research report as a PDF. */
export async function exportReport(jobId: string, ticker: string): Promise<void> {
  const response = await apiClient.post(`/research/${jobId}/export`, {}, {
    responseType: 'blob',
  })
  const blob = new Blob([response.data], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${ticker.toUpperCase()}_report.pdf`)
  document.body.appendChild(link)
  link.click()
  link.parentNode?.removeChild(link)
  window.URL.revokeObjectURL(url)
}
