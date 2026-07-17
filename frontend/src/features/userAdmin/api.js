import api from '@/api/client'

export const listUsers = () => api.get('/api/users').then((r) => r.data)
export const createUser = (payload) => api.post('/api/users', payload).then((r) => r.data)
export const updateUser = (id, payload) =>
  api.patch(`/api/users/${id}`, payload).then((r) => r.data)
export const deleteUser = (id) => api.delete(`/api/users/${id}`).then((r) => r.data)
