'use client'

import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import { useRouter } from 'next/navigation'

const CONSENT_KEY = 'cookie_consent'

export default function CookieBanner() {
  const router = useRouter()
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(CONSENT_KEY)
    if (!stored) {
      // Small delay so the banner animates in after page load
      const t = setTimeout(() => setVisible(true), 600)
      return () => clearTimeout(t)
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem(CONSENT_KEY, 'accepted')
    setVisible(false)
  }

  const handleDecline = () => {
    localStorage.setItem(CONSENT_KEY, 'declined')
    setVisible(false)
  }

  return (
    <Box
      role="dialog"
      aria-label="Cookie consent banner"
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1400,
        display: 'flex',
        justifyContent: 'center',
        px: 2,
        pb: 2,
        pointerEvents: visible ? 'auto' : 'none',
        transform: visible ? 'translateY(0)' : 'translateY(110%)',
        transition: 'transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }}
    >
      <Box
        sx={{
          maxWidth: 780,
          width: '100%',
          background: 'linear-gradient(135deg, #151921 0%, #1D2026 100%)',
          border: '1px solid #2D343F',
          borderRadius: 2,
          boxShadow: '0 -4px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,200,5,0.08)',
          px: { xs: 2.5, sm: 4 },
          py: 2.5,
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'flex-start', sm: 'center' },
          gap: { xs: 2, sm: 3 },
        }}
      >
        {/* Cookie icon */}
        <Box
          sx={{
            flexShrink: 0,
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'rgba(0,200,5,0.1)',
            border: '1px solid rgba(0,200,5,0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
          }}
        >
          🍪
        </Box>

        {/* Text */}
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="body2"
            sx={{ color: '#E1E2EB', fontWeight: 500, mb: 0.4 }}
          >
            We use cookies to improve your experience.
          </Typography>
          <Typography variant="caption" sx={{ color: '#BBCBB2', lineHeight: 1.5 }}>
            By continuing to use this site you agree to our use of cookies for session management
            and analytics.{' '}
            <Box
              component="span"
              onClick={() => router.push('/terms')}
              sx={{
                color: '#00C805',
                cursor: 'pointer',
                textDecoration: 'underline',
                textDecorationColor: 'rgba(0,200,5,0.4)',
                '&:hover': { textDecorationColor: '#00C805' },
              }}
            >
              See our Terms of Service
            </Box>
            .
          </Typography>
        </Box>

        {/* Actions */}
        <Box
          sx={{
            display: 'flex',
            gap: 1.5,
            flexShrink: 0,
            alignSelf: { xs: 'stretch', sm: 'center' },
          }}
        >
          <Button
            id="cookie-decline-btn"
            size="small"
            onClick={handleDecline}
            sx={{
              color: '#BBCBB2',
              border: '1px solid #2D343F',
              borderRadius: 1.5,
              px: 2,
              py: 0.75,
              fontSize: '0.75rem',
              textTransform: 'none',
              '&:hover': {
                borderColor: '#3D4B5A',
                background: 'rgba(255,255,255,0.04)',
                color: '#E1E2EB',
              },
            }}
          >
            Decline
          </Button>
          <Button
            id="cookie-accept-btn"
            size="small"
            onClick={handleAccept}
            sx={{
              background: 'linear-gradient(135deg, #00C805 0%, #00a004 100%)',
              color: '#0B0E14',
              fontWeight: 700,
              borderRadius: 1.5,
              px: 2.5,
              py: 0.75,
              fontSize: '0.75rem',
              textTransform: 'none',
              boxShadow: '0 0 12px rgba(0,200,5,0.3)',
              '&:hover': {
                background: 'linear-gradient(135deg, #00e006 0%, #00C805 100%)',
                boxShadow: '0 0 20px rgba(0,200,5,0.45)',
              },
            }}
          >
            Accept All
          </Button>
        </Box>
      </Box>
    </Box>
  )
}
