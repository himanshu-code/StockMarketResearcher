import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Skeleton from '@mui/material/Skeleton'
import Tooltip from '@mui/material/Tooltip'
import IconButton from '@mui/material/IconButton'
import VisibilityIcon from '@mui/icons-material/Visibility'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined'
import { useNavigate } from 'react-router-dom'
import SignalBadge from './SignalBadge'
import type { ResearchReportItem } from '../types/api'

interface ReportHistoryProps {
  reports: ResearchReportItem[]
  loading?: boolean
}

function extractSentiment(report: string): 'positive' | 'negative' | 'neutral' {
  const lower = report.toLowerCase()
  // Simple heuristic: look for sentiment keywords in the report
  const bullishHits = (lower.match(/bullish|uptrend|strong buy|positive outlook/g) ?? []).length
  const bearishHits = (lower.match(/bearish|downtrend|sell|negative outlook|weak/g) ?? []).length
  if (bullishHits > bearishHits) return 'positive'
  if (bearishHits > bullishHits) return 'negative'
  return 'neutral'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function ReportHistory({ reports, loading = false }: ReportHistoryProps) {
  const navigate = useNavigate()

  const COLUMNS = ['Ticker', 'Signal', 'Status', 'Date Analyzed', 'Actions']

  return (
    <Box className="glass-card">
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              {COLUMNS.map(col => (
                <TableCell key={col}>{col}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading &&
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {COLUMNS.map(col => (
                    <TableCell key={col}>
                      <Skeleton height={24} sx={{ borderRadius: '4px' }} />
                    </TableCell>
                  ))}
                </TableRow>
              ))}

            {!loading && reports.length === 0 && (
              <TableRow>
                <TableCell colSpan={COLUMNS.length} align="center" sx={{ py: 6 }}>
                  <Typography variant="body2" className="text-text-muted">
                    No completed reports yet.{' '}
                    <span
                      className="text-accent-blue cursor-pointer hover:underline"
                      onClick={() => navigate('/')}
                    >
                      Start a research →
                    </span>
                  </Typography>
                </TableCell>
              </TableRow>
            )}

            {!loading &&
              reports.map(report => {
                const sentiment = extractSentiment(report.report ?? '')
                return (
                  <TableRow key={report.job_id} hover>
                    {/* Ticker */}
                    <TableCell>
                      <span className="ticker-chip">{report.ticker}</span>
                    </TableCell>

                    {/* Signal badge */}
                    <TableCell>
                      <SignalBadge sentiment={sentiment} />
                    </TableCell>

                    {/* Status */}
                    <TableCell>
                      <Typography
                        variant="caption"
                        sx={{
                          color:
                            report.status === 'completed'
                              ? '#00C805'
                              : report.status === 'failed'
                              ? '#FF3B30'
                              : '#BBCBB2',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.06em',
                        }}
                      >
                        {report.status}
                      </Typography>
                    </TableCell>

                    {/* Date */}
                    <TableCell>
                      <Typography variant="caption" className="text-text-muted tabular-nums">
                        {formatDate(report.updated_at)}
                      </Typography>
                    </TableCell>

                    {/* Actions */}
                    <TableCell>
                      <Box className="flex items-center gap-1">
                        <Tooltip title="View report">
                          <Button
                            size="small"
                            startIcon={<VisibilityIcon sx={{ fontSize: 14 }} />}
                            onClick={() => navigate(`/report/${report.job_id}`)}
                            sx={{
                              color: '#3D8BFF',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              '&:hover': { backgroundColor: 'rgba(61,139,255,0.08)' },
                            }}
                          >
                            View
                          </Button>
                        </Tooltip>
                        <Tooltip title="Delete (coming soon)">
                          <span>
                            <IconButton size="small" disabled sx={{ color: '#4B5563' }}>
                              <DeleteOutlineIcon sx={{ fontSize: 16 }} />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                )
              })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
