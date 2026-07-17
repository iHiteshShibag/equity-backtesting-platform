import { createContext, useContext, useEffect, useState } from 'react'
import api from '@/api/client'
import { setAccessToken, clearAccessToken, setUnauthorizedHandler } from '@/api/authStore'

const AuthContext = createContext(null)

function toDisplayUser(apiUser) {
  return {
    id: apiUser.id,
    name: apiUser.full_name || apiUser.email,
    email: apiUser.email,
    initials: apiUser.initials,
    role: apiUser.role,
    tosAcceptedAt: apiUser.tos_accepted_at,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  const logout = () => {
    api.post('/api/auth/logout').catch(() => {})
    clearAccessToken()
    setUser(null)
  }

  useEffect(() => {
    setUnauthorizedHandler(logout)

    // No refresh token to check client-side anymore -- it lives in an httpOnly
    // cookie the browser sends automatically. Just attempt a refresh; a
    // missing/expired cookie fails the same way an absent token used to.
    async function restoreSession() {
      try {
        const { data } = await api.post('/api/auth/refresh')
        setAccessToken(data.access_token)
        const me = await api.get('/api/auth/me')
        setUser(toDisplayUser(me.data))
      } catch {
        clearAccessToken()
      } finally {
        setReady(true)
      }
    }
    restoreSession()
  }, [])

  const login = async (email, password) => {
    const { data } = await api.post('/api/auth/login', { email, password })
    setAccessToken(data.access_token)
    const me = await api.get('/api/auth/me')
    setUser(toDisplayUser(me.data))
  }

  const acceptTos = async () => {
    const { data } = await api.post('/api/auth/accept-tos')
    setUser(toDisplayUser(data))
  }

  const updateProfile = async (payload) => {
    const { data } = await api.patch('/api/auth/me', payload)
    setUser(toDisplayUser(data))
  }

  const changePassword = async (currentPassword, newPassword) => {
    await api.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        ready,
        login,
        logout,
        acceptTos,
        updateProfile,
        changePassword,
        isAdmin: user?.role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
