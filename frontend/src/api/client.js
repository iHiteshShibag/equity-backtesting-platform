import axios from 'axios'
import { getAccessToken, setAccessToken, clearAccessToken, notifyUnauthorized } from './authStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// withCredentials so the browser sends/stores the httpOnly refresh-token
// cookie set by the backend; the token itself is never readable from JS.
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Separate instance for the refresh call itself, so its own 401s don't
// re-enter the interceptor below and loop.
const refreshClient = axios.create({ baseURL: API_URL, withCredentials: true })

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise = null

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post('/api/auth/refresh')
      .then(({ data }) => {
        setAccessToken(data.access_token)
        return data.access_token
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    if (response?.status === 401 && !config._retried && !config.url?.includes('/api/auth/')) {
      config._retried = true
      try {
        const newToken = await refreshAccessToken()
        config.headers.Authorization = `Bearer ${newToken}`
        return api(config)
      } catch {
        clearAccessToken()
        notifyUnauthorized()
      }
    }
    return Promise.reject(error)
  },
)

export default api
