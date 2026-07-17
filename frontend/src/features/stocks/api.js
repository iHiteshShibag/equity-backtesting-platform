import api from '@/api/client'

export const getStocks = () => {
  return api.get('/api/stocks/list').then((r) => r.data)
}
