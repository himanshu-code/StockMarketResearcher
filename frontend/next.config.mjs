/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy API requests to the FastAPI backend in development.
  // IMPORTANT: The SSE stream rule must come FIRST so it is matched before the
  // general /research/:path* catch-all. This ensures the long-lived streaming
  // connection is unambiguously routed to the backend.
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
      {
        // SSE stream endpoint — explicit rule to avoid shadowing by the catch-all below
        source: '/research/:jobId/stream',
        destination: `${backendUrl}/research/:jobId/stream`,
      },
      {
        source: '/research/:path*',
        destination: `${backendUrl}/research/:path*`,
      },
      {
        source: '/reports/:path*',
        destination: `${backendUrl}/reports/:path*`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/stock/:path*',
        destination: `${backendUrl}/stock/:path*`,
      },
    ]
  },
}

export default nextConfig
