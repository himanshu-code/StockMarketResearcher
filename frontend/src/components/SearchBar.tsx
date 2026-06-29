import { useState } from 'react'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import InputAdornment from '@mui/material/InputAdornment'
import SearchIcon from '@mui/icons-material/Search'

const TRENDING_TICKERS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'META']

interface SearchBarProps {
  onSubmit: (ticker: string) => Promise<void>
  loading?: boolean
}

export default function SearchBar({ onSubmit, loading = false }: SearchBarProps) {
  const [ticker, setTicker] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    const trimmed = ticker.trim().toUpperCase()
    if (!trimmed) {
      setError('Please enter a ticker symbol')
      return
    }
    if (!/^[A-Z]{1,5}$/.test(trimmed)) {
      setError('Enter a valid ticker (1–5 letters, e.g. NVDA)')
      return
    }
    setError('')
    await onSubmit(trimmed)
  }

  return (
    <Box className="w-full max-w-2xl mx-auto flex flex-col gap-4">
      {/* Search input row */}
      <form onSubmit={handleSubmit} className="flex gap-3 items-start">
        <TextField
          fullWidth
          value={ticker}
          onChange={e => {
            setTicker(e.target.value.toUpperCase())
            if (error) setError('')
          }}
          placeholder="Enter ticker symbol e.g. NVDA, AAPL"
          error={!!error}
          helperText={error}
          disabled={loading}
          autoComplete="off"
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: '#BBCBB2', fontSize: 20 }} />
                </InputAdornment>
              ),
              inputProps: { maxLength: 5 },
            },
          }}
          sx={{ '& .MuiInputBase-root': { fontSize: '1rem', height: 52 } }}
        />
        <Button
          type="submit"
          variant="contained"
          disabled={loading}
          className="shrink-0"
          sx={{
            height: 52,
            px: 3,
            minWidth: 120,
            fontSize: '0.9375rem',
          }}
        >
          {loading ? (
            <CircularProgress size={20} sx={{ color: '#0B0E14' }} />
          ) : (
            'Analyze'
          )}
        </Button>
      </form>

      {/* Trending tickers */}
      <Box className="flex flex-wrap items-center gap-2">
        <Typography variant="caption" className="text-text-muted mr-1">
          Trending:
        </Typography>
        {TRENDING_TICKERS.map(t => (
          <button
            key={t}
            type="button"
            disabled={loading}
            onClick={() => {
              setTicker(t)
              setError('')
            }}
            className="ticker-chip cursor-pointer hover:bg-accent-green/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {t}
          </button>
        ))}
      </Box>
    </Box>
  )
}
