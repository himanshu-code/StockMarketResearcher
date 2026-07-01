import axios from 'axios'

// Base Axios instance — reads from Vite's VITE_API_BASE_URL env variable, falling back to '/'
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})
