import { Routes, Route } from 'react-router-dom'
import Box from '@mui/material/Box'
import NavAppBar from './components/layout/AppBar'
import SearchPage from './pages/SearchPage'
import ReportPage from './pages/ReportPage'
import HistoryPage from './pages/HistoryPage'

export default function App() {
  return (
    <Box className="min-h-screen bg-obsidian">
      <NavAppBar />
      {/* Offset for fixed AppBar (64px) */}
      <Box sx={{ pt: '64px' }}>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/report/:jobId" element={<ReportPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </Box>
    </Box>
  )
}
