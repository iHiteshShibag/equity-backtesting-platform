import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const runBacktest = (params) => {
  return api.post('/api/backtest/run', params).then(r => r.data)
}

export const getStocks = () => {
  return api.get('/api/stocks/list').then(r => r.data)
}

export const healthCheck = () => {
  return api.get('/api/backtest/health').then(r => r.data)
}

export default api
