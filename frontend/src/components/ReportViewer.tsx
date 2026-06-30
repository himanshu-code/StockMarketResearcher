import { useState } from 'react'
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
import SignalBadge from './SignalBadge'
import type { SentimentLabel } from '../types/api'
import type { ResearcherData } from '../types/api'

interface ReportViewerProps {
  ticker: string
  report: string
  sentiment: SentimentLabel | null
  marketData: ResearcherData['market_data'] | null
}

// ── Placeholder: Price Sparkline ────────────────────────────────────────────
function PriceChartPlaceholder() {
  return (
    <Box className="glass-card p-4 flex flex-col gap-2">
      <Box className="flex items-center gap-2">
        <Typography variant="caption" className="text-text-muted uppercase tracking-wider">
          30-Day Price Chart
        </Typography>
        <Tooltip title="Price chart will be available once the OHLCV data endpoint is wired to the frontend.">
          <InfoOutlinedIcon sx={{ fontSize: 14, color: '#4B5563', cursor: 'help' }} />
        </Tooltip>
        <Box
          component="span"
          className="text-xs px-2 py-0.5 rounded-full border border-border text-text-muted ml-1"
        >
          Coming Soon
        </Box>
      </Box>
      <Skeleton
        variant="rectangular"
        height={80}
        sx={{ borderRadius: '6px', bgcolor: 'rgba(255,255,255,0.04)' }}
      />
      <Typography variant="caption" className="text-text-muted opacity-50 text-center">
        OHLCV endpoint not yet connected
      </Typography>
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
export default function ReportViewer({ ticker, report, sentiment, marketData }: ReportViewerProps) {
  const [tab, setTab] = useState(0)

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
            {/* PDF Export — Placeholder: endpoint not yet implemented */}
            <Tooltip title="PDF export coming soon — backend endpoint not yet available">
              <span>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<DownloadIcon />}
                  disabled
                  sx={{ borderColor: '#2D343F', color: '#4B5563' }}
                >
                  Download PDF
                </Button>
              </span>
            </Tooltip>

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

      {/* Price chart placeholder */}
      <PriceChartPlaceholder />

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
