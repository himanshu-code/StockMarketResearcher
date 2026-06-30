import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import AddIcon from '@mui/icons-material/Add'
import RefreshIcon from '@mui/icons-material/Refresh'
import Tooltip from '@mui/material/Tooltip'
import IconButton from '@mui/material/IconButton'
import Alert from '@mui/material/Alert'
import ReportHistory from '../components/ReportHistory'
import { getReports } from '../api/research'
import type { ResearchReportItem } from '../types/api'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [reports, setReports] = useState<ResearchReportItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchReports = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getReports()
      setReports(data)
    } catch {
      setError('Could not load reports. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchReports() }, [])

  return (
    <Box className="max-w-[1100px] mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
      {/* Page header */}
      <Box className="flex items-center justify-between">
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Research History
          </Typography>
          <Typography variant="body2" className="text-text-muted mt-0.5">
            Completed analyses from this session
            <Tooltip title="History is in-memory and resets when the backend restarts. Persistent storage coming in a future phase.">
              <Box
                component="span"
                className="ml-2 text-xs px-2 py-0.5 rounded-full border border-border text-text-muted cursor-help"
              >
                Session only
              </Box>
            </Tooltip>
          </Typography>
        </Box>

        <Box className="flex items-center gap-2">
          <Tooltip title="Refresh">
            <IconButton size="small" onClick={fetchReports} sx={{ color: '#BBCBB2' }}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/')}
            size="small"
          >
            New Research
          </Button>
        </Box>
      </Box>

      {/* Error */}
      {error && (
        <Alert
          severity="error"
          sx={{
            backgroundColor: 'rgba(255,59,48,0.1)',
            border: '1px solid rgba(255,59,48,0.3)',
            color: '#FF3B30',
          }}
        >
          {error}
        </Alert>
      )}

      {/* Table */}
      <ReportHistory reports={reports} loading={loading} />
    </Box>
  )
}
