import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { authAPI } from '../services/api'
import { clearAllCache } from '../services/cache'

const AuthContext = createContext(null)

const SESSION_KEY = 'py_session'

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const session = JSON.parse(raw)
    if (session.expiresAt && Date.now() > session.expiresAt) {
      localStorage.removeItem(SESSION_KEY)
      return null
    }
    return session
  } catch { return null }
}

function saveSession(data) {
  const session = {
    user:          data.user,
    expiresAt:     Date.now() + (data.expires_in || 1800) * 1000,
    refreshedAt:   Date.now(),
  }
  localStorage.setItem(SESSION_KEY,       JSON.stringify(session))
  localStorage.setItem('access_token',    data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  return session
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadSession())
  const user      = session?.user ?? null
  const isLoggedIn = !!user

  useEffect(() => {
    if (!session) return
    const ttl = session.expiresAt - Date.now() - 60_000
    if (ttl <= 0) { setSession(null); return }
    const timer = setTimeout(() => {
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) { setSession(null); return }
      authAPI.refresh(refresh)
        .then(({ data }) => {
          const newSession = saveSession({ ...data, user: session.user })
          setSession(newSession)
        })
        .catch(() => setSession(null))
    }, ttl)
    return () => clearTimeout(timer)
  }, [session])

  const login = useCallback(async (email, password) => {
    const { data } = await authAPI.login(email, password)
    const me = { email, role: data.role || 'buyer', first_name: data.first_name, id: data.user_id }
    const newSession = saveSession({ ...data, user: me })
    setSession(newSession)
    return data
  }, [])

  const register = useCallback(async (formData) => {
    const { data } = await authAPI.register(formData)
    return data
  }, [])

  const logout = useCallback(async () => {
    try { await authAPI.logout() } catch {}
    localStorage.removeItem(SESSION_KEY)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    clearAllCache()
    setSession(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, session, login, register, logout, isLoggedIn }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
