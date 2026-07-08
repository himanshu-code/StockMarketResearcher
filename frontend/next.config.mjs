/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy API requests to the FastAPI backend in development
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
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
