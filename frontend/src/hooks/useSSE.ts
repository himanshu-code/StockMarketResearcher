import { useEffect, useRef, useState, useCallback } from 'react'
import type {
  AgentStep,
  CritiqueData,
  JobStatus,
  ResearcherData,
  SentimentLabel,
  StepStatus,
} from '../types/api'
import { BASE_URL } from '../api/client'

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
  ticker: string | null
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
    ticker: null,
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

    // Bug 1 fix: strip trailing slash so we never produce "//research/…".
    // When BASE_URL is '/' (default dev), base becomes '' → '/research/{jobId}/stream' ✓
    // When BASE_URL is a full URL like 'https://api.example.com', it works as-is.
    const base = BASE_URL.replace(/\/$/, '')
    const streamUrl = `${base}/research/${jobId}/stream`

    const es = new EventSource(streamUrl)
    esRef.current = es

    // Bug 5 fix: connection-timeout guard. If EventSource never opens within 8s,
    // surface a failed state so the report page can show a retry button instead of
    // spinning "Connecting to analysis stream…" indefinitely.
    const connectionTimeout = setTimeout(() => {
      if (es.readyState !== EventSource.OPEN) {
        setState(prev =>
          prev.logLines.length === 0
            ? {
                ...prev,
                error:
                  'Could not connect to the analysis stream. The backend may be unavailable.',
                jobStatus: 'failed',
              }
            : prev,
        )
        es.close()
      }
    }, 8_000)

    // Clear the connection timeout as soon as the stream is established
    es.onopen = () => clearTimeout(connectionTimeout)

    es.addEventListener('agent_started', (e: MessageEvent) => {
      clearTimeout(connectionTimeout)
      let tickerName = ''
      try {
        const data = JSON.parse(e.data)
        tickerName = data.ticker || ''
      } catch {
        // ignore
      }
      setState(prev => ({
        ...prev,
        jobStatus: 'running',
        ticker: tickerName || prev.ticker,
      }))
      appendLog(tickerName ? `Analysis started for ${tickerName}...` : 'Analysis started...')
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
          ticker: data.ticker ?? prev.ticker,
        }))
      } catch {
        appendLog('researcher event received')
      }
    })

    // Bug 4 fix: backend now emits "critic" (matches LangGraph node name).
    // We register both "critic" and "critique" (old name) so this works against
    // any backend version without requiring a simultaneous redeploy.
    const handleCriticEvent = (e: MessageEvent) => {
      try {
        const data: CritiqueData = JSON.parse(e.data)
        if (data.approved) {
          setStep('critic', 'completed', { message: 'Approved' })
          setStep('report', 'running')
          appendLog(`Critic approved research (iteration ${data.iteration})`)
        } else {
          setStep('critic', 'pending', {
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
    }
    es.addEventListener('critic', handleCriticEvent)    // current backend
    es.addEventListener('critique', handleCriticEvent)  // backward-compat alias

    es.addEventListener('report', () => {
      setStep('report', 'running')
      appendLog('Generating final report...')
    })

    es.addEventListener('report_ready', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        setStep('report', 'completed')
        setState(prev => ({
          ...prev,
          jobStatus: 'completed',
          report: data.report,
          ticker: data.ticker ?? prev.ticker,
        }))
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

    // Bug 3 fix: do NOT call es.close() on every onerror — EventSource auto-reconnects
    // on transient network hiccups. Closing here would permanently kill the stream.
    // Only log the interruption so the user can see it in the progress panel.
    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) {
        appendLog('Stream connection closed.')
      } else {
        appendLog('Stream connection interrupted — reconnecting...')
      }
    }

    return () => {
      clearTimeout(connectionTimeout)
      es.close()
    }
  }, [jobId, appendLog, setStep])

  return state
}
