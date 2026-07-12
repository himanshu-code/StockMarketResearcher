'use client'

import { useParams, useRouter } from 'next/navigation'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import Alert from '@mui/material/Alert'
import RefreshIcon from '@mui/icons-material/Refresh'
import dynamic from 'next/dynamic'
import { useSSE } from '../../../hooks/useSSE'
import AgentProgressPanel from '../../../components/AgentProgressPanel'

// Dynamically import ReportViewer with SSR disabled to avoid hydration mismatches
// caused by Recharts' server-side rendering limitations.
const ReportViewer = dynamic(() => import('../../../components/ReportViewer'), { ssr: false })

export default function ReportPage() {
  const params = useParams<{ jobId: string }>()
  const jobId = params?.jobId
  const router = useRouter()

  const {
    steps,
    logLines,
    jobStatus,
    report,
    error,
    sentiment,
    marketData,
    ticker: sseTicker,
  } = useSSE(jobId ?? null)

  const ticker = sseTicker ?? jobId ?? ''

  // Bug 5 fix: the connection-timeout in useSSE surfaces jobStatus='failed' with an
  // error message when the stream never opens. We treat this case separately from a
  // job that ran and failed, giving the user a Retry button instead of a blank screen.
  const isConnectionError =
    jobStatus === 'failed' && logLines.length === 0

  return (
    <Box className="max-w-[1100px] mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
      {/* Back nav */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => router.push('/')}
        size="small"
        sx={{ color: '#BBCBB2', alignSelf: 'flex-start', '&:hover': { color: '#E1E2EB' } }}
      >
        New Search
      </Button>

      {/* Stream connection error — shown when EventSource never connected */}
      {isConnectionError && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
            py: 8,
            textAlign: 'center',
          }}
        >
          <Alert
            severity="error"
            sx={{
              backgroundColor: 'rgba(255,59,48,0.1)',
              border: '1px solid rgba(255,59,48,0.3)',
              color: '#FF3B30',
              width: '100%',
              maxWidth: 520,
            }}
          >
            <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 600 }}>
              Could not connect to the analysis stream
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              {error ?? 'The backend may be unavailable or still starting up.'}
            </Typography>
          </Alert>
          <Button
            id="retry-stream-btn"
            startIcon={<RefreshIcon />}
            onClick={() => router.refresh()}
            variant="outlined"
            size="small"
            sx={{
              color: '#00C805',
              borderColor: 'rgba(0,200,5,0.4)',
              '&:hover': {
                borderColor: '#00C805',
                backgroundColor: 'rgba(0,200,5,0.06)',
              },
            }}
          >
            Retry connection
          </Button>
        </Box>
      )}

      {/* Job-level error state (ran but failed) */}
      {jobStatus === 'failed' && error && !isConnectionError && (
        <Alert
          severity="error"
          sx={{
            backgroundColor: 'rgba(255,59,48,0.1)',
            border: '1px solid rgba(255,59,48,0.3)',
            color: '#FF3B30',
          }}
        >
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}

      {/* Progress panel — show while running, queued, or failed-with-logs */}
      {(jobStatus === 'queued' || jobStatus === 'running' || (jobStatus === 'failed' && !isConnectionError)) && (
        <AgentProgressPanel steps={steps} logLines={logLines} ticker={jobId ?? ''} />
      )}

      {/* Report viewer — show when complete */}
      {jobStatus === 'completed' && report && (
        <ReportViewer
          jobId={jobId ?? ''}
          ticker={ticker}
          report={report}
          sentiment={sentiment}
          marketData={marketData}
        />
      )}

      {/* Queued state fallback — shown briefly before the stream connects */}
      {jobStatus === 'queued' && logLines.length === 0 && (
        <Box className="text-center py-8">
          <Typography variant="body2" className="text-text-muted">
            Connecting to analysis stream...
          </Typography>
        </Box>
      )}
    </Box>
  )
}
