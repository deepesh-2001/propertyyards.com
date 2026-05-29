import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useLang } from '../context/LangContext'

export default function Register() {
  const { register } = useAuth()
  const { toast }    = useToast()
  const { tr }       = useLang()
  const nav = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone_number: '', password: '', role: 'buyer' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      toast('Account created! Please sign in.', 'success')
      nav('/login?registered=1')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed. Please try again.'
      setError(msg)
      toast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const f = (field) => ({ value: form[field], onChange: e => setForm({...form, [field]: e.target.value}) })

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>🏠 PropertyYards</div>
        <h1 style={s.title}>{tr('createAccount')}</h1>
        <p style={s.sub}>{tr('registerSub')}</p>

        {error && <div style={s.error}>{error}</div>}

        <form onSubmit={submit} style={s.form}>
          <div style={s.row}>
            <Field label={tr('firstName')} type="text" placeholder="Rahul" {...f('first_name')} required />
            <Field label={tr('lastName')}  type="text" placeholder="Sharma" {...f('last_name')} required />
          </div>
          <Field label={tr('emailLabel')} type="email" placeholder="you@example.com" {...f('email')} required />
          <Field label={tr('phone')} type="tel" placeholder="+91 9876543210" {...f('phone_number')} />
          <Field label={tr('passwordLabel')} type="password" placeholder="Min 8 characters" {...f('password')} required />

          <div style={s.field}>
            <label style={s.label}>{tr('iAm')}</label>
            <div style={s.roleGrid}>
              {[['buyer', tr('buyer')],['seller', tr('seller')],['agent', tr('agent')]].map(([val, label]) => (
                <button type="button" key={val} onClick={() => setForm({...form, role: val})}
                  style={{ ...s.roleBtn, ...(form.role === val ? s.roleActive : {}) }}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" disabled={loading} style={s.btn}>
            {loading ? tr('creatingAccount') : tr('createFreeBtn')}
          </button>
        </form>

        <p style={s.footer}>
          {tr('alreadyAccount')} <Link to="/login" style={s.link}>{tr('signIn')}</Link>
        </p>
      </div>
    </div>
  )
}

function Field({ label, ...props }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{label}</label>
      <input {...props} style={{ border: '1px solid #d1d5db', borderRadius: 10, padding: '11px 14px', fontSize: 15, outline: 'none', width: '100%', boxSizing: 'border-box' }} />
    </div>
  )
}

const s = {
  page:      { minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' },
  card:      { background: '#fff', borderRadius: 24, padding: '2.5rem', width: '100%', maxWidth: 500, boxShadow: '0 24px 80px rgba(0,0,0,0.4)' },
  logo:      { textAlign: 'center', fontSize: 24, fontWeight: 900, color: '#1a56db', marginBottom: '1.5rem', letterSpacing: '-0.5px' },
  title:     { fontSize: 26, fontWeight: 800, textAlign: 'center', margin: '0 0 6px', color: '#0f172a', letterSpacing: '-0.5px' },
  sub:       { textAlign: 'center', color: '#64748b', marginBottom: '1.5rem', fontSize: 14 },
  error:     { background: '#fef2f2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: 10, padding: '10px 14px', fontSize: 14, marginBottom: 16 },
  form:      { display: 'flex', flexDirection: 'column', gap: 14 },
  row:       { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  field:     { display: 'flex', flexDirection: 'column', gap: 6 },
  label:     { fontSize: 13, fontWeight: 700, color: '#374151', textTransform: 'uppercase', letterSpacing: '0.5px' },
  roleGrid:  { display: 'flex', gap: 10 },
  roleBtn:   { flex: 1, padding: '10px', borderRadius: 12, border: '2px solid #e2e8f0', background: '#f8fafc', cursor: 'pointer', fontSize: 14, fontWeight: 600, color: '#374151', transition: 'all 0.15s' },
  roleActive:{ border: '2px solid #1a56db', background: '#eff6ff', color: '#1a56db' },
  btn:       { background: 'linear-gradient(135deg, #1a56db, #2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 16, fontWeight: 700, cursor: 'pointer', marginTop: 4, boxShadow: '0 4px 16px rgba(26,86,219,0.35)' },
  footer:    { textAlign: 'center', fontSize: 14, color: '#64748b', marginTop: 20 },
  link:      { color: '#1a56db', fontWeight: 700, textDecoration: 'none' },
}
