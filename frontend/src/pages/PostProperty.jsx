import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { propertiesAPI } from '../services/api'

const AMENITIES = ['Swimming Pool','Gym','Parking','Security','Power Backup','Lift','Garden','Club House','24x7 Water Supply','CCTV','Intercom','Fire Safety','Rainwater Harvesting','Solar Panel']

export default function PostProperty() {
  const { isLoggedIn } = useAuth()
  const { toast }      = useToast()
  const { tr }         = useLang()
  const { isMobile }   = useBreakpoint()
  const nav = useNavigate()

  const [form, setForm] = useState({
    title: '', description: '', location: '', city: '', state: '', country: 'India',
    price: '', property_type: 'apartment', listing_type: 'sale',
    bedrooms: '', bathrooms: '', area: '',
    amenities: [], furnished: false, pets_allowed: false,
    broker_name: '', broker_phone: '',
  })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  if (!isLoggedIn) { nav('/login'); return null }

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const toggleAmenity = (a) => {
    setForm(f => ({ ...f, amenities: f.amenities.includes(a) ? f.amenities.filter(x => x !== a) : [...f.amenities, a] }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await propertiesAPI.create({
        ...form,
        price: Number(form.price),
        bedrooms: Number(form.bedrooms),
        bathrooms: Number(form.bathrooms),
        area: Number(form.area),
      })
      toast('Property posted successfully! 🎉', 'success')
      setSuccess(true)
      setTimeout(() => nav('/dashboard'), 2000)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to post property. Please try again.'
      setError(msg)
      toast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  if (success) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16, background: '#f8fafc' }}>
      <div style={{ fontSize: 72 }}>🎉</div>
      <h2 style={{ fontSize: 28, fontWeight: 900, color: '#0f172a', letterSpacing: '-0.5px' }}>Property Posted!</h2>
      <p style={{ color: '#64748b', fontSize: 16 }}>Redirecting to your dashboard...</p>
      <div style={{ width: 200, height: 4, background: '#e2e8f0', borderRadius: 99, overflow: 'hidden' }}>
        <div style={{ height: '100%', background: 'linear-gradient(90deg,#1a56db,#7c3aed)', borderRadius: 99, animation: 'none', width: '100%' }} />
      </div>
    </div>
  )

  const rowCols = isMobile ? '1fr' : null

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div style={{ fontSize: 36 }}>🏠</div>
          <div>
            <h1 style={s.h1}>{tr('postTitle')}</h1>
            <p style={s.sub}>{tr('postSub')}</p>
          </div>
        </div>
      </div>

      <div style={s.wrap}>
        {error && <div style={s.error}>{error}</div>}

        <form onSubmit={submit} style={s.form}>
          <Section title="📝 Basic Details" icon="📝">
            <FullField label="Property Title *" placeholder="e.g. 3BHK Apartment in Koramangala" value={form.title} onChange={set('title')} required />
            <Row cols={rowCols || 3}>
              <SelectField label="Property Type *" value={form.property_type} onChange={set('property_type')}>
                {['apartment','house','villa','plot','commercial','studio'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}
              </SelectField>
              <SelectField label="Listing Type *" value={form.listing_type} onChange={set('listing_type')}>
                <option value="sale">{tr('forSale')}</option>
                <option value="rent">{tr('forRent')}</option>
              </SelectField>
              <InputField label="Price (₹) *" type="number" placeholder="e.g. 5000000" value={form.price} onChange={set('price')} required />
            </Row>
            <FullField label="Description *" placeholder="Describe the property..." value={form.description} onChange={set('description')} required textarea />
          </Section>

          <Section title="📍 Location">
            <Row cols={rowCols || 3}>
              <InputField label="Locality / Area *" placeholder="e.g. Koramangala" value={form.location} onChange={set('location')} required />
              <InputField label="City *" placeholder="e.g. Bangalore" value={form.city} onChange={set('city')} required />
              <InputField label="State *" placeholder="e.g. Karnataka" value={form.state} onChange={set('state')} required />
            </Row>
          </Section>

          <Section title="🏠 Property Details">
            <Row cols={rowCols || 3}>
              <InputField label="Bedrooms" type="number" placeholder="e.g. 3" value={form.bedrooms} onChange={set('bedrooms')} />
              <InputField label="Bathrooms" type="number" placeholder="e.g. 2" value={form.bathrooms} onChange={set('bathrooms')} />
              <InputField label="Area (sq ft) *" type="number" placeholder="e.g. 1200" value={form.area} onChange={set('area')} required />
            </Row>
            <Row cols={rowCols || 2}>
              <CheckField label="Furnished" checked={form.furnished} onChange={set('furnished')} />
              <CheckField label="Pets Allowed" checked={form.pets_allowed} onChange={set('pets_allowed')} />
            </Row>
          </Section>

          <Section title="✨ Amenities">
            <div style={s.amenGrid}>
              {AMENITIES.map(a => (
                <button type="button" key={a} onClick={() => toggleAmenity(a)}
                  style={{ ...s.amenBtn, ...(form.amenities.includes(a) ? s.amenActive : {}) }}>
                  {form.amenities.includes(a) ? '✓ ' : ''}{a}
                </button>
              ))}
            </div>
            {form.amenities.length > 0 && (
              <div style={{ fontSize: 13, color: '#1a56db', fontWeight: 600 }}>
                {form.amenities.length} amenit{form.amenities.length === 1 ? 'y' : 'ies'} selected
              </div>
            )}
          </Section>

          <Section title="🧑‍💼 Broker / Agent Info (Optional)">
            <Row cols={rowCols || 2}>
              <InputField label="Broker Name" placeholder="e.g. Rahul Sharma" value={form.broker_name} onChange={set('broker_name')} />
              <InputField label="Broker Phone" placeholder="e.g. +91 9876543210" value={form.broker_phone} onChange={set('broker_phone')} />
            </Row>
          </Section>

          <button type="submit" disabled={loading} style={s.submitBtn}>
            {loading ? tr('posting') : tr('postBtn')}
          </button>
        </form>
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div style={{ background: '#fff', borderRadius: 14, padding: '24px', border: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, color: '#111827', margin: 0 }}>{title}</h2>
      {children}
    </div>
  )
}
function Row({ children, cols }) {
  const count = Array.isArray(children) ? children.filter(Boolean).length : 1
  return <div style={{ display: 'grid', gridTemplateColumns: cols ? `repeat(${cols},1fr)` : `repeat(${count},1fr)`, gap: 16 }}>{children}</div>
}
function FullField({ label, textarea, ...props }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
    <label style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{label}</label>
    {textarea
      ? <textarea rows={4} {...props} style={{ border: '1px solid #d1d5db', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none', resize: 'vertical', fontFamily: 'inherit' }} />
      : <input {...props} style={{ border: '1px solid #d1d5db', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none' }} />}
  </div>
}
function InputField({ label, ...props }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
    <label style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{label}</label>
    <input {...props} style={{ border: '1px solid #d1d5db', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none', width: '100%', boxSizing: 'border-box' }} />
  </div>
}
function SelectField({ label, children, ...props }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
    <label style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{label}</label>
    <select {...props} style={{ border: '1px solid #d1d5db', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none', background: '#fff' }}>{children}</select>
  </div>
}
function CheckField({ label, ...props }) {
  return <label style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 15, fontWeight: 600, cursor: 'pointer', padding: '10px 0' }}>
    <input type="checkbox" {...props} style={{ width: 18, height: 18 }} /> {label}
  </label>
}

const s = {
  page:       { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:     { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '2.5rem 0' },
  bannerInner:{ maxWidth: 860, margin: '0 auto', padding: '0 1.5rem', display: 'flex', alignItems: 'center', gap: 20 },
  h1:         { fontSize: 'clamp(22px,4vw,30px)', fontWeight: 900, margin: 0, letterSpacing: '-0.5px' },
  sub:        { fontSize: 14, opacity: 0.75, marginTop: 4 },
  wrap:       { maxWidth: 860, margin: '0 auto', padding: '2rem 1.5rem' },
  error:      { background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', borderRadius: 12, padding: '12px 16px', marginBottom: 20 },
  form:       { display: 'flex', flexDirection: 'column', gap: 20 },
  amenGrid:   { display: 'flex', flexWrap: 'wrap', gap: 8 },
  amenBtn:    { padding: '7px 16px', borderRadius: 20, border: '1.5px solid #e2e8f0', background: '#f8fafc', cursor: 'pointer', fontSize: 13, color: '#374151', transition: 'all 0.15s' },
  amenActive: { border: '1.5px solid #1a56db', background: '#eff6ff', color: '#1a56db', fontWeight: 700 },
  submitBtn:  { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 14, padding: '16px', fontSize: 17, fontWeight: 800, cursor: 'pointer', boxShadow: '0 4px 16px rgba(26,86,219,0.35)', letterSpacing: '-0.3px', transition: 'all 0.2s' },
}
