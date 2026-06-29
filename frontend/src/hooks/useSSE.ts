import { useEffect, useRef, useState, useCallback } from 'react'
import type {
  AgentStep,
  CritiqueData,
  JobStatus,
  ResearcherData,
  SentimentLabel,
  StepStatus,
} from '../types/api'

const INITIAL_STEPS: AgentStep[] = [
  { key: 'researcher', label: 'Research Agent', status: 'pending' },
  { key: 'critic', label: 'Critic Agent', status: 'pending' },
  { key: 'report', label: 'Report Generation', status: 'pending' },
]

interface SSEState {
  steps: AgentStep[]
  jobStatus: JobStatus
  report: string | null
  error: string | null
  /** Inferred from news_sentiment.label in the researcher event */
  sentiment: SentimentLabel | null
  /** Raw market data from the researcher event */
  marketData: ResearcherData['market_data'] | null
  logLines: string[]
}

/**
 * Connects to the SSE stream for a job and parses all events into UI-friendly state.
 * Automatically closes the connection when the job reaches a terminal state.
 */
export function useSSE(jobId: string | null): SSEState {
  const [state, setState] = useState<SSEState>({
    steps: INITIAL_STEPS,
    jobStatus: 'queued',
    report: null,
    error: null,
    sentiment: null,
    marketData: null,
    logLines: [],
  })

  const esRef = useRef<EventSource | null>(null)

  const appendLog = useCallback((line: string) => {
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false })
    setState(prev => ({ ...prev, logLines: [...prev.logLines, `[${ts}] ${line}`] }))
  }, [])

  const setStep = useCallback((key: string, status: StepStatus, extra?: Partial<AgentStep>) => {
    setState(prev => ({
      ...prev,
      steps: prev.steps.map(s => (s.key === key ? { ...s, status, ...extra } : s)),
    }))
  }, [])

  useEffect(() => {
    if (!jobId) return

    // Close any previous connection
    esRef.current?.close()

    const es = new EventSource(`/research/${jobId}/stream`)
    esRef.current = es

    es.addEventListener('agent_started', () => {
      setState(prev => ({ ...prev, jobStatus: 'running' }))
      appendLog('Analysis started...')
      setStep('researcher', 'running')
    })

    es.addEventListener('researcher', (e: MessageEvent) => {
      try {
        const data: ResearcherData = JSON.parse(e.data)
        setStep('researcher', 'completed', {
          iteration: data.iteration,
          message: `Iteration ${data.iteration} complete`,
        })
        setStep('critic', 'running')
        appendLog(`Research agent completed (iteration ${data.iteration})`)
        // Capture market & sentiment data for the UI
        setState(prev => ({
          ...prev,
          sentiment: data.news_sentiment?.label ?? prev.sentiment,
          marketData: data.market_data ?? prev.marketData,
        }))
      } catch {
        appendLog('researcher event received')
      }
    })

    es.addEventListener('critic', (e: MessageEvent) => {
      try {
        const data: CritiqueData = JSON.parse(e.data)
        if (data.approved) {
          setStep('critic', 'completed', { message: 'Approved' })
          setStep('report', 'running')
          appendLog(`Critic approved research (iteration ${data.iteration})`)
        } else {
          setStep('critic', 'completed', {
            message: `Retry needed — ${data.missing?.join(', ') || 'unspecified'}`,
          })
          // Reset researcher for retry
          setStep('researcher', 'running', { message: `Retrying (iteration ${data.iteration + 1})` })
          appendLog(
            `Critic requested retry: ${data.critique?.slice(0, 80)}${data.critique?.length > 80 ? '…' : ''}`,
          )
        }
      } catch {
        appendLog('critic event received')
      }
    })

    es.addEventListener('report', () => {
      setStep('report', 'running')
      appendLog('Generating final report...')
    })

    es.addEventListener('report_ready', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        setStep('report', 'completed')
        setState(prev => ({ ...prev, jobStatus: 'completed', report: data.report }))
        appendLog('Report ready ✓')
      } catch {
        appendLog('report_ready event received')
      }
      es.close()
    })

    es.addEventListener('agent_done', () => {
      appendLog('All agents finished.')
    })

    es.addEventListener('agent_failed', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        setState(prev => ({ ...prev, jobStatus: 'failed', error: data.error }))
        appendLog(`Error: ${data.error}`)
      } catch {
        appendLog('agent_failed event received')
      }
      es.close()
    })

    es.onerror = () => {
      appendLog('Stream connection lost.')
      es.close()
    }

    return () => {
      es.close()
    }
  }, [jobId, appendLog, setStep])

  return state
}
