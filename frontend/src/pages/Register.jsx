import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
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
      nav('/login?registered=1')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const f = (field) => ({ value: form[field], onChange: e => setForm({...form, [field]: e.target.value}) })

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>🏠 PropertyYards</div>
        <h1 style={s.title}>Create your account</h1>
        <p style={s.sub}>Join thousands of buyers, sellers and agents</p>

        {error && <div style={s.error}>{error}</div>}

        <form onSubmit={submit} style={s.form}>
          <div style={s.row}>
            <Field label="First Name" type="text" placeholder="Rahul" {...f('first_name')} required />
            <Field label="Last Name" type="text" placeholder="Sharma" {...f('last_name')} required />
          </div>
          <Field label="Email" type="email" placeholder="you@example.com" {...f('email')} required />
          <Field label="Phone Number" type="tel" placeholder="+91 9876543210" {...f('phone_number')} />
          <Field label="Password" type="password" placeholder="Min 8 characters" {...f('password')} required />

          <div style={s.field}>
            <label style={s.label}>I am a</label>
            <div style={s.roleGrid}>
              {[['buyer','🏠 Buyer'],['seller','🏢 Seller'],['agent','🧑‍💼 Agent']].map(([val, label]) => (
                <button type="button" key={val} onClick={() => setForm({...form, role: val})}
                  style={{ ...s.roleBtn, ...(form.role === val ? s.roleActive : {}) }}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" disabled={loading} style={s.btn}>
            {loading ? 'Creating account...' : 'Create Free Account'}
          </button>
        </form>

        <p style={s.footer}>
          Already have an account? <Link to="/login" style={s.link}>Sign in</Link>
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
  page:      { minHeight: '100vh', background: 'linear-gradient(135deg, #f0f4ff, #e8f5e9)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' },
  card:      { background: '#fff', borderRadius: 18, padding: '2.5rem', width: '100%', maxWidth: 480, boxShadow: '0 8px 40px rgba(0,0,0,0.1)' },
  logo:      { textAlign: 'center', fontSize: 22, fontWeight: 800, color: '#1a56db', marginBottom: '1.5rem' },
  title:     { fontSize: 24, fontWeight: 800, textAlign: 'center', margin: '0 0 6px', color: '#111827' },
  sub:       { textAlign: 'center', color: '#6b7280', marginBottom: '1.5rem', fontSize: 14 },
  error:     { background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', borderRadius: 8, padding: '10px 14px', fontSize: 14, marginBottom: 16 },
  form:      { display: 'flex', flexDirection: 'column', gap: 14 },
  row:       { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  field:     { display: 'flex', flexDirection: 'column', gap: 6 },
  label:     { fontSize: 14, fontWeight: 600, color: '#374151' },
  roleGrid:  { display: 'flex', gap: 10 },
  roleBtn:   { flex: 1, padding: '10px', borderRadius: 10, border: '2px solid #e5e7eb', background: '#f9fafb', cursor: 'pointer', fontSize: 14, fontWeight: 600, color: '#374151' },
  roleActive:{ border: '2px solid #1a56db', background: '#eff6ff', color: '#1a56db' },
  btn:       { background: '#1a56db', color: '#fff', border: 'none', borderRadius: 10, padding: '13px', fontSize: 16, fontWeight: 700, cursor: 'pointer', marginTop: 4 },
  footer:    { textAlign: 'center', fontSize: 14, color: '#6b7280', marginTop: 20 },
  link:      { color: '#1a56db', fontWeight: 600, textDecoration: 'none' },
}
