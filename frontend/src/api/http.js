import axios from 'axios'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

const http = axios.create({
  baseURL: configuredBaseUrl ? configuredBaseUrl.replace(/\/$/, '') : '',
  timeout: 180_000,
  headers: {
    Accept: 'application/json',
  },
})

export default http
