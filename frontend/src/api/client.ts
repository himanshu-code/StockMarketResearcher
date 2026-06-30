import axios from 'axios'

// Base Axios instance — in dev, Vite proxies /research and /reports to :8000
export const apiClient = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})
