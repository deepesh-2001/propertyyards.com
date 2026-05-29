import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { propertiesAPI } from '../services/api'

const AMENITIES = ['Swimming Pool','Gym','Parking','Security','Power Backup','Lift','Garden','Club House','24x7 Water Supply','CCTV','Intercom','Fire Safety','Rainwater Harvesting','Solar Panel']

export default function PostProperty() {
  const { isLoggedIn } = useAuth()
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
      setSuccess(true)
      setTimeout(() => nav('/dashboard'), 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to post property. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 60 }}>✅</div>
      <h2 style={{ fontSize: 24, fontWeight: 700 }}>Property Posted Successfully!</h2>
      <p style={{ color: '#6b7280' }}>Redirecting to dashboard...</p>
    </div>
  )

  return (
    <div style={s.page}>
      <div style={s.wrap}>
        <h1 style={s.h1}>Post a Property</h1>
        <p style={s.sub}>Fill in the details to list your property</p>

        {error && <div style={s.error}>{error}</div>}

        <form onSubmit={submit} style={s.form}>
          <Section title="Basic Details">
            <FullField label="Property Title *" placeholder="e.g. 3BHK Apartment in Koramangala" value={form.title} onChange={set('title')} required />
            <Row>
              <SelectField label="Property Type *" value={form.property_type} onChange={set('property_type')}>
                {['apartment','house','villa','plot','commercial','studio'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}
              </SelectField>
              <SelectField label="Listing Type *" value={form.listing_type} onChange={set('listing_type')}>
                <option value="sale">For Sale</option>
                <option value="rent">For Rent</option>
              </SelectField>
              <InputField label="Price (₹) *" type="number" placeholder="e.g. 5000000" value={form.price} onChange={set('price')} required />
            </Row>
            <FullField label="Description *" placeholder="Describe the property..." value={form.description} onChange={set('description')} required textarea />
          </Section>

          <Section title="Location">
            <Row>
              <InputField label="Locality / Area *" placeholder="e.g. Koramangala" value={form.location} onChange={set('location')} required />
              <InputField label="City *" placeholder="e.g. Bangalore" value={form.city} onChange={set('city')} required />
              <InputField label="State *" placeholder="e.g. Karnataka" value={form.state} onChange={set('state')} required />
            </Row>
          </Section>

          <Section title="Property Details">
            <Row>
              <InputField label="Bedrooms" type="number" placeholder="e.g. 3" value={form.bedrooms} onChange={set('bedrooms')} />
              <InputField label="Bathrooms" type="number" placeholder="e.g. 2" value={form.bathrooms} onChange={set('bathrooms')} />
              <InputField label="Area (sq ft) *" type="number" placeholder="e.g. 1200" value={form.area} onChange={set('area')} required />
            </Row>
            <Row>
              <CheckField label="Furnished" checked={form.furnished} onChange={set('furnished')} />
              <CheckField label="Pets Allowed" checked={form.pets_allowed} onChange={set('pets_allowed')} />
            </Row>
          </Section>

          <Section title="Amenities">
            <div style={s.amenGrid}>
              {AMENITIES.map(a => (
                <button type="button" key={a} onClick={() => toggleAmenity(a)}
                  style={{ ...s.amenBtn, ...(form.amenities.includes(a) ? s.amenActive : {}) }}>
                  {form.amenities.includes(a) ? '✓ ' : ''}{a}
                </button>
              ))}
            </div>
          </Section>

          <Section title="Broker / Agent Info (Optional)">
            <Row>
              <InputField label="Broker Name" placeholder="e.g. Rahul Sharma" value={form.broker_name} onChange={set('broker_name')} />
              <InputField label="Broker Phone" placeholder="e.g. +91 9876543210" value={form.broker_phone} onChange={set('broker_phone')} />
            </Row>
          </Section>

          <button type="submit" disabled={loading} style={s.submitBtn}>
            {loading ? 'Posting...' : '🚀 Post Property'}
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
function Row({ children }) { return <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Array.isArray(children) ? children.length : 1}, 1fr)`, gap: 16 }}>{children}</div> }
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
  page:      { background: '#f9fafb', minHeight: '100vh', paddingBottom: '4rem' },
  wrap:      { maxWidth: 860, margin: '0 auto', padding: '2rem' },
  h1:        { fontSize: 30, fontWeight: 800, margin: '0 0 6px', color: '#111827' },
  sub:       { fontSize: 15, color: '#6b7280', marginBottom: '2rem' },
  error:     { background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', borderRadius: 10, padding: '12px 16px', marginBottom: 20 },
  form:      { display: 'flex', flexDirection: 'column', gap: 24 },
  amenGrid:  { display: 'flex', flexWrap: 'wrap', gap: 10 },
  amenBtn:   { padding: '7px 16px', borderRadius: 20, border: '1px solid #d1d5db', background: '#f9fafb', cursor: 'pointer', fontSize: 13, color: '#374151' },
  amenActive:{ border: '1px solid #1a56db', background: '#eff6ff', color: '#1a56db', fontWeight: 600 },
  submitBtn: { background: '#1a56db', color: '#fff', border: 'none', borderRadius: 12, padding: '15px', fontSize: 17, fontWeight: 700, cursor: 'pointer' },
}
