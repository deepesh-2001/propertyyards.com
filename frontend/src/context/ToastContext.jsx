import { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random()
    setToasts(t => [...t, { id, message, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), duration)
  }, [])

  const dismiss = useCallback((id) => setToasts(t => t.filter(x => x.id !== id)), [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div style={styles.container}>
        {toasts.map(t => (
          <div key={t.id} style={{ ...styles.toast, ...styles[t.type] }} onClick={() => dismiss(t.id)}>
            <span style={styles.icon}>{icons[t.type]}</span>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)

const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' }

const styles = {
  container: { position: 'fixed', bottom: 24, right: 24, display: 'flex', flexDirection: 'column', gap: 10, zIndex: 9999, maxWidth: 360 },
  toast:     { display: 'flex', alignItems: 'center', gap: 10, padding: '12px 18px', borderRadius: 12, fontWeight: 500, fontSize: 14, cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.15)', animation: 'slideIn 0.25s ease', backdropFilter: 'blur(8px)' },
  icon:      { fontSize: 18, flexShrink: 0 },
  success:   { background: '#f0fdf4', border: '1px solid #86efac', color: '#166534' },
  error:     { background: '#fef2f2', border: '1px solid #fca5a5', color: '#991b1b' },
  info:      { background: '#eff6ff', border: '1px solid #93c5fd', color: '#1e3a8a' },
  warning:   { background: '#fffbeb', border: '1px solid #fcd34d', color: '#92400e' },
}
