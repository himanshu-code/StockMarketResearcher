import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import SearchBar from '../components/SearchBar'
import { postResearch } from '../api/research'

export default function SearchPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  const handleSearch = async (ticker: string) => {
    setLoading(true)
    setApiError('')
    try {
      const { job_id } = await postResearch(ticker)
      navigate(`/report/${job_id}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start research. Is the backend running?'
      setApiError(msg)
      setLoading(false)
    }
  }

  return (
    <Box className="min-h-screen flex flex-col items-center justify-center px-4 relative">
      {/* Radial glow background decoration */}
      <Box
        className="absolute inset-0 pointer-events-none"
        sx={{
          background:
            'radial-gradient(ellipse 60% 40% at 50% 40%, rgba(0,200,5,0.07) 0%, transparent 70%)',
        }}
      />

      <Box className="relative z-10 flex flex-col items-center gap-8 w-full max-w-2xl text-center">
        {/* Hero text */}
        <Box>
          <Typography
            variant="h3"
            sx={{ fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.2, mb: 1.5 }}
          >
            AI-Powered Stock Research
          </Typography>
          <Typography variant="body1" className="text-text-muted max-w-md mx-auto">
            Multi-agent analysis across market data, fundamentals, and news sentiment — in seconds.
          </Typography>
        </Box>

        {/* Search bar */}
        <SearchBar onSubmit={handleSearch} loading={loading} />

        {/* API error */}
        {apiError && (
          <Typography variant="body2" sx={{ color: '#FF3B30' }}>
            {apiError}
          </Typography>
        )}

        {/* Footer hint */}
        <Typography variant="caption" className="text-text-muted opacity-50">
          Powered by LangGraph · CrewAI · FastAPI
        </Typography>
      </Box>
    </Box>
  )
}
