'use client'

import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Tooltip from '@mui/material/Tooltip'
import Skeleton from '@mui/material/Skeleton'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import Divider from '@mui/material/Divider'
import DownloadIcon from '@mui/icons-material/Download'
import ShareIcon from '@mui/icons-material/Share'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts'
import SignalBadge from './SignalBadge'
import { exportReport, getStockOHLCV } from '../api/research'
import type { SentimentLabel, OHLCVRecord } from '../types/api'
import type { ResearcherData } from '../types/api'

interface ReportViewerProps {
  jobId: string
  ticker: string
  report: string
  sentiment: SentimentLabel | null
  marketData: ResearcherData['market_data'] | null
}

// ── Price Sparkline (Recharts Area Chart) ──────────────────────────────────
interface PriceSparklineProps {
  ticker: string
  percentageChange: number
}

function PriceSparkline({ ticker, percentageChange }: PriceSparklineProps) {
  const [data, setData] = useState<OHLCVRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    getStockOHLCV(ticker, '1mo')
      .then(res => {
        if (active) {
          setData(res.data)
          setLoading(false)
        }
      })
      .catch(err => {
        console.error('Failed to load sparkline data:', err)
        if (active) {
          setError('Failed to load price chart')
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [ticker])

  if (loading) {
    return (
      <Box className="glass-card p-4 flex flex-col gap-2">
        <Typography variant="caption" className="text-text-muted uppercase tracking-wider">
          30-Day Price Chart ({ticker})
        </Typography>
        <Skeleton
          variant="rectangular"
          height={100}
          sx={{ borderRadius: '6px', bgcolor: 'rgba(255,255,255,0.04)' }}
        />
      </Box>
    )
  }

  if (error || data.length === 0) {
    return (
      <Box className="glass-card p-4 flex flex-col gap-2 items-center justify-center min-h-[142px]">
        <Typography variant="caption" className="text-text-muted uppercase tracking-wider self-start">
          30-Day Price Chart ({ticker})
        </Typography>
        <Typography variant="caption" className="text-accent-red opacity-80 mt-2">
          {error || 'No price history available'}
        </Typography>
      </Box>
    )
  }

  const isPositive = percentageChange >= 0
  const chartColor = isPositive ? '#00C805' : '#FF3B30'
  const gradientId = `sparklineGradient-${ticker}`

  // Format date for tooltip
  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  return (
    <Box className="glass-card p-4 flex flex-col gap-2">
      <Box className="flex items-center justify-between">
        <Typography variant="caption" className="text-text-muted uppercase tracking-wider">
          30-Day Price Chart ({ticker})
        </Typography>
        <Typography variant="caption" className="text-text-muted" sx={{ fontSize: '0.75rem' }}>
          {formatDate(data[0]?.date)} — {formatDate(data[data.length - 1]?.date)}
        </Typography>
      </Box>
      <Box sx={{ width: '100%', height: 100, mt: 1 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.25} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" hide />
            <YAxis domain={['auto', 'auto']} hide />
            <RechartsTooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const record = payload[0].payload as OHLCVRecord
                  return (
                    <Box
                      className="glass-card"
                      sx={{
                        p: 1.5,
                        bgcolor: 'rgba(21, 25, 33, 0.95)',
                        border: '1px solid #2D343F',
                        borderRadius: '6px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                      }}
                    >
                      <Typography variant="caption" className="text-text-muted" sx={{ display: 'block', fontWeight: 500 }}>
                        {formatDate(record.date)}
                      </Typography>
                      <Box className="flex gap-4 mt-1">
                        <Box>
                          <Typography variant="caption" className="text-text-muted" sx={{ display: 'block', fontSize: '0.65rem', textTransform: 'uppercase' }}>
                            Close
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace', color: '#E1E2EB' }}>
                            ${record.close.toFixed(2)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" className="text-text-muted" sx={{ display: 'block', fontSize: '0.65rem', textTransform: 'uppercase' }}>
                            Volume
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace', color: '#BBCBB2' }}>
                            {record.volume.toLocaleString()}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  )
                }
                return null
              }}
              cursor={{ stroke: '#2D343F', strokeWidth: 1 }}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke={chartColor}
              strokeWidth={2}
              fillOpacity={1}
              fill={`url(#${gradientId})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  )
}


// ── Market data summary row ─────────────────────────────────────────────────
function MarketDataRow({ marketData }: { marketData: ResearcherData['market_data'] | null }) {
  if (!marketData || Object.keys(marketData).length === 0) {
    return (
      <Box className="flex gap-4">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} width={90} height={40} sx={{ borderRadius: '6px' }} />
        ))}
      </Box>
    )
  }

  const items = [
    {
      label: 'Price',
      value: marketData.current_price
        ? `${marketData.current_price.toFixed(2)} ${marketData.currency ?? ''}`
        : 'N/A',
    },
    {
      label: 'Day Change',
      value: marketData.percentage_change !== undefined
        ? `${marketData.percentage_change > 0 ? '+' : ''}${marketData.percentage_change.toFixed(2)}%`
        : 'N/A',
      color:
        (marketData.percentage_change ?? 0) > 0
          ? '#00C805'
          : (marketData.percentage_change ?? 0) < 0
          ? '#FF3B30'
          : undefined,
    },
    { label: '52W High', value: marketData.high_52w?.toFixed(2) ?? 'N/A' },
    { label: '52W Low', value: marketData.low_52w?.toFixed(2) ?? 'N/A' },
    { label: 'Trend', value: marketData.trend ?? 'N/A' },
  ]

  return (
    <Box className="flex flex-wrap gap-4">
      {items.map(item => (
        <Box key={item.label} className="flex flex-col">
          <Typography variant="caption" className="text-text-muted">
            {item.label}
          </Typography>
          <Typography
            variant="body2"
            sx={{ fontWeight: 600, fontFamily: 'monospace', color: item.color ?? '#E1E2EB' }}
          >
            {item.value}
          </Typography>
        </Box>
      ))}
    </Box>
  )
}

// ── Main component ──────────────────────────────────────────────────────────
export default function ReportViewer({ jobId, ticker, report, sentiment, marketData }: ReportViewerProps) {
  const [tab, setTab] = useState(0)
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await exportReport(jobId, ticker)
    } catch (err) {
      console.error('Failed to export PDF:', err)
      alert('Failed to export PDF report. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <Box className="flex flex-col gap-4">
      {/* Header card */}
      <Box className="glass-card p-5">
        <Box className="flex flex-wrap items-start justify-between gap-4 mb-4">
          {/* Ticker + signal */}
          <Box className="flex items-center gap-3 flex-wrap">
            <Typography variant="h5" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
              {ticker}
            </Typography>
            <SignalBadge sentiment={sentiment} loading={!sentiment} />
          </Box>

          {/* Actions */}
          <Box className="flex items-center gap-2">
            {/* PDF Export */}
            <Button
              variant="outlined"
              size="small"
              startIcon={<DownloadIcon />}
              disabled={downloading}
              onClick={handleDownload}
              sx={{ borderColor: '#2D343F', color: '#BBCBB2', '&:hover': { borderColor: '#3D8BFF', color: '#3D8BFF' } }}
            >
              {downloading ? 'Downloading...' : 'Download PDF'}
            </Button>

            <Tooltip title="Copy report link">
              <Button
                variant="outlined"
                size="small"
                startIcon={<ShareIcon />}
                onClick={() => navigator.clipboard.writeText(window.location.href)}
                sx={{ borderColor: '#2D343F', color: '#BBCBB2' }}
              >
                Share
              </Button>
            </Tooltip>
          </Box>
        </Box>

        {/* Market data summary */}
        <MarketDataRow marketData={marketData} />
      </Box>

      {/* Price chart */}
      <PriceSparkline ticker={ticker} percentageChange={marketData?.percentage_change ?? 0} />

      {/* Report content card */}
      <Box className="glass-card p-5">
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label="Full Report" />
          <Tab label="Raw Markdown" />
        </Tabs>
        <Divider sx={{ borderColor: '#2D343F', mb: 3 }} />

        {tab === 0 && (
          <Box
            className="prose prose-invert max-w-none"
            sx={{
              '& h1, & h2, & h3': { color: '#E1E2EB', fontWeight: 600 },
              '& h2': { borderBottom: '1px solid #2D343F', pb: 1, mb: 2, mt: 3 },
              '& ul': { pl: 2 },
              '& li': { color: '#BBCBB2', mb: 0.5 },
              '& p': { color: '#BBCBB2', lineHeight: 1.7 },
              '& table': { width: '100%', borderCollapse: 'collapse' },
              '& th': {
                textAlign: 'left',
                padding: '8px 12px',
                backgroundColor: '#272A31',
                color: '#E1E2EB',
                fontWeight: 600,
                fontSize: '0.8rem',
              },
              '& td': {
                padding: '8px 12px',
                borderBottom: '1px solid #2D343F',
                color: '#BBCBB2',
                fontFamily: 'monospace',
              },
              '& tr:hover td': { backgroundColor: 'rgba(255,255,255,0.02)' },
              '& code': {
                backgroundColor: '#272A31',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.85em',
                color: '#3D8BFF',
              },
              '& strong': { color: '#E1E2EB' },
            }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
          </Box>
        )}

        {tab === 1 && (
          <Box className="terminal-log" sx={{ maxHeight: 500 }}>
            <pre className="whitespace-pre-wrap break-words">{report}</pre>
          </Box>
        )}
      </Box>
    </Box>
  )
}
