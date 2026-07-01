import { useParams, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import Alert from '@mui/material/Alert'
import { useSSE } from '../hooks/useSSE'
import AgentProgressPanel from '../components/AgentProgressPanel'
import ReportViewer from '../components/ReportViewer'

export default function ReportPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const { steps, logLines, jobStatus, report, error, sentiment, marketData } = useSSE(jobId ?? null)

  const ticker = steps[0]?.message?.split(' ')[0] ?? jobId ?? ''

  return (
    <Box className="max-w-[1100px] mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
      {/* Back nav */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/')}
        size="small"
        sx={{ color: '#BBCBB2', alignSelf: 'flex-start', '&:hover': { color: '#E1E2EB' } }}
      >
        New Search
      </Button>

      {/* Error state */}
      {jobStatus === 'failed' && error && (
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

      {/* Progress panel — show while running or queued */}
      {(jobStatus === 'queued' || jobStatus === 'running' || jobStatus === 'failed') && (
        <AgentProgressPanel
          steps={steps}
          logLines={logLines}
          ticker={jobId ?? ''}
        />
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

      {/* Queued state fallback */}
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
