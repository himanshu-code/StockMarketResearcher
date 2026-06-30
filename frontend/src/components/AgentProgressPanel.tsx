import { useRef, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import LinearProgress from '@mui/material/LinearProgress'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked'
import ErrorIcon from '@mui/icons-material/Error'
import type { AgentStep, StepStatus } from '../types/api'

interface AgentProgressPanelProps {
  steps: AgentStep[]
  logLines: string[]
  ticker: string
}

function StatusIcon({ status }: { status: StepStatus }) {
  if (status === 'completed')
    return <CheckCircleIcon sx={{ fontSize: 18, color: '#00C805' }} />
  if (status === 'failed')
    return <ErrorIcon sx={{ fontSize: 18, color: '#FF3B30' }} />
  if (status === 'running')
    return (
      <span className="inline-block w-4 h-4 rounded-full border-2 border-accent-blue animate-spin border-t-transparent" />
    )
  return <RadioButtonUncheckedIcon sx={{ fontSize: 18, color: '#4B5563' }} />
}

function StatusChip({ status }: { status: StepStatus }) {
  const map: Record<StepStatus, { label: string; color: string; bg: string }> = {
    completed: { label: 'DONE', color: '#00C805', bg: 'rgba(0,200,5,0.12)' },
    running: { label: 'RUNNING', color: '#3D8BFF', bg: 'rgba(61,139,255,0.12)' },
    pending: { label: 'PENDING', color: '#4B5563', bg: 'rgba(75,85,99,0.12)' },
    failed: { label: 'FAILED', color: '#FF3B30', bg: 'rgba(255,59,48,0.12)' },
  }
  const cfg = map[status]
  return (
    <Chip
      label={cfg.label}
      size="small"
      sx={{
        fontSize: '0.65rem',
        fontWeight: 700,
        letterSpacing: '0.08em',
        color: cfg.color,
        backgroundColor: cfg.bg,
        border: `1px solid ${cfg.color}30`,
        height: 22,
      }}
    />
  )
}

export default function AgentProgressPanel({ steps, logLines, ticker }: AgentProgressPanelProps) {
  const logRef = useRef<HTMLDivElement>(null)

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logLines])

  const completedCount = steps.filter(s => s.status === 'completed').length
  const progress = (completedCount / steps.length) * 100

  return (
    <Box className="glass-card p-5 flex flex-col gap-5">
      {/* Header */}
      <Box className="flex items-center justify-between">
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Analyzing{' '}
            <span className="ticker-chip text-sm px-2 py-0.5">{ticker}</span>
          </Typography>
          <Typography variant="caption" className="text-text-muted">
            {completedCount} of {steps.length} steps complete
          </Typography>
        </Box>
        <Typography variant="caption" className="text-text-muted tabular-nums">
          {Math.round(progress)}%
        </Typography>
      </Box>

      {/* Progress bar */}
      <LinearProgress variant="determinate" value={progress} />

      <Box className="flex flex-col md:flex-row gap-5">
        {/* Step list */}
        <Box className="flex flex-col gap-3 min-w-[220px]">
          {steps.map((step, i) => (
            <Box key={step.key} className="flex items-start gap-3">
              {/* Connector line */}
              <Box className="flex flex-col items-center">
                <StatusIcon status={step.status} />
                {i < steps.length - 1 && (
                  <Box
                    className="w-px mt-1 flex-1"
                    sx={{
                      minHeight: 24,
                      backgroundColor: step.status === 'completed' ? '#00C80530' : '#2D343F',
                    }}
                  />
                )}
              </Box>
              <Box className="flex-1 pb-2">
                <Box className="flex items-center justify-between gap-2">
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#E1E2EB' }}>
                    {step.label}
                  </Typography>
                  <StatusChip status={step.status} />
                </Box>
                {step.message && (
                  <Typography variant="caption" className="text-text-muted block mt-0.5">
                    {step.message}
                  </Typography>
                )}
              </Box>
            </Box>
          ))}
        </Box>

        <Divider orientation="vertical" flexItem sx={{ borderColor: '#2D343F' }} />

        {/* Live log */}
        <Box className="flex-1 flex flex-col gap-2 min-w-0">
          <Typography variant="caption" className="text-text-muted uppercase tracking-wider">
            Live Log
          </Typography>
          <Box
            ref={logRef}
            className="terminal-log flex-1"
            sx={{ maxHeight: 220, minHeight: 120 }}
          >
            {logLines.length === 0 ? (
              <span className="opacity-40">Waiting for events...</span>
            ) : (
              logLines.map((line, i) => (
                <div key={i} className="leading-relaxed">
                  <span className="text-accent-green opacity-60 mr-2">›</span>
                  {line}
                </div>
              ))
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  )
}
