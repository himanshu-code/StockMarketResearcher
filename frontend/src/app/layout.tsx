import type { Metadata } from 'next'
import Box from '@mui/material/Box'
import NavAppBar from '../components/layout/AppBar'
import ThemeRegistry from './ThemeRegistry'
import '../index.css'

export const metadata: Metadata = {
  title: 'Stock Market Researcher',
  description: 'AI-powered multi-agent stock analysis across market data, fundamentals, and news sentiment.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ThemeRegistry>
          <Box className="min-h-screen bg-obsidian">
            <NavAppBar />
            {/* Offset for fixed AppBar (64px) */}
            <Box sx={{ pt: '64px' }}>{children}</Box>
          </Box>
        </ThemeRegistry>
      </body>
    </html>
  )
}
