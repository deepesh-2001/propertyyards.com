import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useLang } from '../context/LangContext'

export default function Login() {
  const { login } = useAuth()
  const { toast } = useToast()
  const { tr }    = useLang()
  const nav = useNavigate()
  const [form, setForm]     = useState({ email: '', password: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      toast('Welcome back! 👋', 'success')
      nav('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid email or password'
      setError(msg)
      toast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>🏠 PropertyYards</div>
        <h1 style={s.title}>{tr('welcomeBack')}</h1>
        <p style={s.sub}>{tr('signInSub')}</p>

        {error && <div style={s.error}>{error}</div>}

        <form onSubmit={submit} style={s.form}>
          <div style={s.field}>
            <label style={s.label}>{tr('emailLabel')}</label>
            <input required type="email" value={form.email} placeholder="you@example.com"
              onChange={e => setForm({...form, email: e.target.value})} style={s.input} />
          </div>
          <div style={s.field}>
            <label style={s.label}>{tr('passwordLabel')}</label>
            <div style={{ position: 'relative' }}>
              <input required type={showPass ? 'text' : 'password'} value={form.password} placeholder="••••••••"
                onChange={e => setForm({...form, password: e.target.value})} style={s.input} />
              <button type="button" onClick={() => setShowPass(p => !p)}
                style={s.eyeBtn}>{showPass ? '🙈' : '👁'}</button>
            </div>
          </div>
          <button type="submit" disabled={loading} style={s.btn}>
            {loading ? tr('signingIn') : tr('signIn')}
          </button>
        </form>

        <div style={s.divider}><span>{tr('testCredentials')}</span></div>
        <div style={s.testCreds}>
          <div>📧 admin@propertyyards.com</div>
          <div>🔑 Test@1234</div>
        </div>

        <p style={s.footer}>
          {tr('noAccount')} <Link to="/register" style={s.link}>{tr('createFree')}</Link>
        </p>
      </div>
    </div>
  )
}

const s = {
  page:      { minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' },
  card:      { background: '#fff', borderRadius: 24, padding: '2.5rem', width: '100%', maxWidth: 440, boxShadow: '0 24px 80px rgba(0,0,0,0.4)' },
  logo:      { textAlign: 'center', fontSize: 24, fontWeight: 900, color: '#1a56db', marginBottom: '1.5rem', letterSpacing: '-0.5px' },
  title:     { fontSize: 28, fontWeight: 800, textAlign: 'center', margin: '0 0 6px', color: '#0f172a', letterSpacing: '-0.5px' },
  sub:       { textAlign: 'center', color: '#64748b', marginBottom: '1.5rem', fontSize: 15 },
  error:     { background: '#fef2f2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: 10, padding: '10px 14px', fontSize: 14, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 },
  form:      { display: 'flex', flexDirection: 'column', gap: 18 },
  field:     { display: 'flex', flexDirection: 'column', gap: 6 },
  label:     { fontSize: 13, fontWeight: 700, color: '#374151', textTransform: 'uppercase', letterSpacing: '0.5px' },
  input:     { border: '1.5px solid #e2e8f0', borderRadius: 12, padding: '12px 14px', fontSize: 15, outline: 'none', transition: 'all 0.2s', width: '100%', boxSizing: 'border-box' },
  eyeBtn:    { position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, padding: 0 },
  btn:       { background: 'linear-gradient(135deg, #1a56db, #2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 16, fontWeight: 700, cursor: 'pointer', marginTop: 4, boxShadow: '0 4px 16px rgba(26,86,219,0.35)', transition: 'all 0.2s' },
  divider:   { textAlign: 'center', margin: '20px 0 12px', fontSize: 13, color: '#94a3b8', borderTop: '1px solid #e2e8f0', paddingTop: 14 },
  testCreds: { background: '#f0f9ff', borderRadius: 12, padding: '12px 16px', fontSize: 13, color: '#0369a1', display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 8, border: '1px solid #bae6fd' },
  footer:    { textAlign: 'center', fontSize: 14, color: '#64748b', marginTop: 20 },
  link:      { color: '#1a56db', fontWeight: 700, textDecoration: 'none' },
}
