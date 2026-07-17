import api from '@/api/client'

export const getMyOrg = () => api.get('/api/orgs/me').then((r) => r.data)
export const updateMyOrg = (payload) => api.patch('/api/orgs/me', payload).then((r) => r.data)
