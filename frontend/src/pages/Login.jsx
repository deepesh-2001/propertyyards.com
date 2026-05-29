import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [form, setForm]     = useState({ email: '', password: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      nav('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>🏠 PropertyYards</div>
        <h1 style={s.title}>Welcome back</h1>
        <p style={s.sub}>Sign in to your account</p>

        {error && <div style={s.error}>{error}</div>}

        <form onSubmit={submit} style={s.form}>
          <div style={s.field}>
            <label style={s.label}>Email address</label>
            <input required type="email" value={form.email} placeholder="you@example.com"
              onChange={e => setForm({...form, email: e.target.value})} style={s.input} />
          </div>
          <div style={s.field}>
            <label style={s.label}>Password</label>
            <input required type="password" value={form.password} placeholder="••••••••"
              onChange={e => setForm({...form, password: e.target.value})} style={s.input} />
          </div>
          <button type="submit" disabled={loading} style={s.btn}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={s.divider}><span>Test Credentials</span></div>
        <div style={s.testCreds}>
          <div>📧 admin@propertyyards.com</div>
          <div>🔑 Test@1234</div>
        </div>

        <p style={s.footer}>
          Don't have an account? <Link to="/register" style={s.link}>Create one free</Link>
        </p>
      </div>
    </div>
  )
}

const s = {
  page:      { minHeight: '100vh', background: 'linear-gradient(135deg, #f0f4ff, #e8f5e9)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' },
  card:      { background: '#fff', borderRadius: 18, padding: '2.5rem', width: '100%', maxWidth: 420, boxShadow: '0 8px 40px rgba(0,0,0,0.1)' },
  logo:      { textAlign: 'center', fontSize: 22, fontWeight: 800, color: '#1a56db', marginBottom: '1.5rem' },
  title:     { fontSize: 26, fontWeight: 800, textAlign: 'center', margin: '0 0 6px', color: '#111827' },
  sub:       { textAlign: 'center', color: '#6b7280', marginBottom: '1.5rem', fontSize: 15 },
  error:     { background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', borderRadius: 8, padding: '10px 14px', fontSize: 14, marginBottom: 16 },
  form:      { display: 'flex', flexDirection: 'column', gap: 16 },
  field:     { display: 'flex', flexDirection: 'column', gap: 6 },
  label:     { fontSize: 14, fontWeight: 600, color: '#374151' },
  input:     { border: '1px solid #d1d5db', borderRadius: 10, padding: '12px 14px', fontSize: 15, outline: 'none', transition: 'border 0.2s' },
  btn:       { background: '#1a56db', color: '#fff', border: 'none', borderRadius: 10, padding: '13px', fontSize: 16, fontWeight: 700, cursor: 'pointer', marginTop: 4 },
  divider:   { textAlign: 'center', margin: '20px 0 12px', fontSize: 13, color: '#9ca3af', borderTop: '1px solid #e5e7eb', paddingTop: 14 },
  testCreds: { background: '#f0f9ff', borderRadius: 10, padding: '10px 14px', fontSize: 13, color: '#0369a1', display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 16 },
  footer:    { textAlign: 'center', fontSize: 14, color: '#6b7280', marginTop: 20 },
  link:      { color: '#1a56db', fontWeight: 600, textDecoration: 'none' },
}
