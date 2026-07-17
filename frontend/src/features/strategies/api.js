import api from '@/api/client'

export const saveStrategy = (name, request) => {
  return api.post('/api/strategies/', { name, request }).then((r) => r.data)
}

export const listStrategies = () => {
  return api.get('/api/strategies/').then((r) => r.data)
}

export const setStrategyActive = (id, is_active) => {
  return api.patch(`/api/strategies/${id}`, { is_active }).then((r) => r.data)
}

export const deleteStrategy = (id) => {
  return api.delete(`/api/strategies/${id}`).then((r) => r.data)
}
