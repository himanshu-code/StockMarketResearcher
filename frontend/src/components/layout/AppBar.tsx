import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import { useNavigate, useLocation } from 'react-router-dom'

// Simple stock chart icon SVG
function LogoIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="28" height="28" rx="6" fill="#0B0E14" />
      <polyline
        points="3,20 8,12 13,16 18,8 25,11"
        stroke="#00C805"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="18" cy="8" r="2" fill="#00C805" />
    </svg>
  )
}

export default function NavAppBar() {
  const navigate = useNavigate()
  const location = useLocation()

  const navLinks = [
    { label: 'Search', path: '/' },
    { label: 'History', path: '/history' },
  ]

  return (
    <AppBar position="fixed" elevation={0}>
      <Toolbar className="max-w-[1440px] mx-auto w-full px-4 sm:px-6">
        {/* Brand */}
        <Box
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate('/')}
        >
          <LogoIcon />
          <Typography
            variant="body1"
            className="font-semibold tracking-tight text-text-primary hidden sm:block"
            sx={{ fontWeight: 600 }}
          >
            StockMarketResearcher
          </Typography>
        </Box>

        {/* Spacer */}
        <Box className="flex-1" />

        {/* Nav links */}
        <Box className="flex items-center gap-1">
          {navLinks.map(link => (
            <Button
              key={link.path}
              onClick={() => navigate(link.path)}
              size="small"
              sx={{
                color: location.pathname === link.path ? '#E1E2EB' : '#BBCBB2',
                fontWeight: location.pathname === link.path ? 600 : 400,
                borderBottom:
                  location.pathname === link.path ? '2px solid #00C805' : '2px solid transparent',
                borderRadius: 0,
                px: 1.5,
                py: 0.75,
                '&:hover': { color: '#E1E2EB', backgroundColor: 'rgba(255,255,255,0.04)' },
              }}
            >
              {link.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  )
}
