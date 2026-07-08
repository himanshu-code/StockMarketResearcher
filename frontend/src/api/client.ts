import axios from 'axios'

// Base Axios instance — reads from Next.js's NEXT_PUBLIC_API_BASE_URL env variable, falling back to '/'
// In development, relative URLs '/' are proxied to the FastAPI backend via next.config.mjs rewrites.
export const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})
