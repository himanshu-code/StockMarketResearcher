import Chip from '@mui/material/Chip'
import Skeleton from '@mui/material/Skeleton'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import RemoveIcon from '@mui/icons-material/Remove'
import type { SentimentLabel } from '../types/api'

interface SignalBadgeProps {
  sentiment: SentimentLabel | null
  /** When true, shows a skeleton placeholder instead */
  loading?: boolean
}

const CONFIG = {
  positive: {
    label: 'BULLISH',
    color: '#00C805',
    bg: 'rgba(0,200,5,0.15)',
    icon: <TrendingUpIcon sx={{ fontSize: 14 }} />,
  },
  negative: {
    label: 'BEARISH',
    color: '#FF3B30',
    bg: 'rgba(255,59,48,0.15)',
    icon: <TrendingDownIcon sx={{ fontSize: 14 }} />,
  },
  neutral: {
    label: 'NEUTRAL',
    color: '#BBCBB2',
    bg: 'rgba(187,203,178,0.1)',
    icon: <RemoveIcon sx={{ fontSize: 14 }} />,
  },
}

export default function SignalBadge({ sentiment, loading = false }: SignalBadgeProps) {
  if (loading || !sentiment) {
    return <Skeleton variant="rounded" width={90} height={28} sx={{ borderRadius: '999px' }} />
  }

  const cfg = CONFIG[sentiment]

  return (
    <Chip
      icon={cfg.icon}
      label={cfg.label}
      size="small"
      sx={{
        backgroundColor: cfg.bg,
        color: cfg.color,
        border: `1px solid ${cfg.color}40`,
        fontWeight: 700,
        fontSize: '0.7rem',
        letterSpacing: '0.06em',
        '& .MuiChip-icon': { color: cfg.color },
      }}
    />
  )
}
