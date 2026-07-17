import api from '@/api/client'

export const getIngestionStatus = () => api.get('/api/market-data/status').then((r) => r.data)
export const triggerIngestion = () => api.post('/api/market-data/ingest').then((r) => r.data)
