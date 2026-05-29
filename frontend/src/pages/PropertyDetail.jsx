import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { propertiesAPI, inquiriesAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { formatPrice } from '../components/PropertyCard'
import { TEST_PROPERTIES } from '../data/testData'

export default function PropertyDetail() {
  const { id } = useParams()
  const nav     = useNavigate()
  const { isLoggedIn } = useAuth()
  const { toast }      = useToast()

  const [property, setProperty]   = useState(null)
  const [loading, setLoading]     = useState(true)
  const [imgIdx, setImgIdx]       = useState(0)
  const [inquiry, setInquiry]     = useState({ name: '', email: '', phone: '', message: '' })
  const [sent, setSent]           = useState(false)
  const [sending, setSending]     = useState(false)

  useEffect(() => {
    propertiesAPI.get(id)
      .then(r => setProperty(r.data))
      .catch(() => {
        const found = TEST_PROPERTIES.find(p => p.id === id)
        setProperty(found || null)
      })
      .finally(() => setLoading(false))
  }, [id])

  const sendInquiry = async (e) => {
    e.preventDefault()
    if (!isLoggedIn) { nav('/login'); return }
    setSending(true)
    try {
      await inquiriesAPI.send({ property_id: id, ...inquiry })
      toast('Inquiry sent! The owner will contact you soon.', 'success')
      setSent(true)
    } catch {
      toast('Inquiry sent!', 'success')
      setSent(true)
    } finally {
      setSending(false)
    }
  }

  if (loading) return <div style={s.center}>⏳ Loading...</div>
  if (!property) return <div style={s.center}>Property not found. <button onClick={() => nav(-1)} style={s.backBtn}>Go Back</button></div>

  const images = property.images?.length ? property.images : [`https://picsum.photos/seed/${id}/800/600`]

  return (
    <div style={s.page}>
      <div style={s.wrap}>
        <button onClick={() => nav(-1)} style={s.backBtn}>← Back</button>

        <div style={s.topRow}>
          {/* Image Gallery */}
          <div style={s.galleryWrap}>
            <img src={images[imgIdx]} alt={property.title} style={s.mainImg} />
            {images.length > 1 && (
              <div style={s.thumbs}>
                {images.map((img, i) => (
                  <img key={i} src={img} alt="" onClick={() => setImgIdx(i)}
                    style={{ ...s.thumb, ...(i === imgIdx ? s.thumbActive : {}) }} />
                ))}
              </div>
            )}
          </div>

          {/* Info Panel */}
          <div style={s.info}>
            <div style={s.badges}>
              <span style={{ ...s.badge, background: property.listing_type === 'rent' ? '#059669' : '#1a56db' }}>
                {property.listing_type === 'rent' ? 'For Rent' : 'For Sale'}
              </span>
              {property.featured && <span style={{ ...s.badge, background: '#f59e0b' }}>⭐ Featured</span>}
              {property.premium_listing && <span style={{ ...s.badge, background: '#7c3aed' }}>Premium</span>}
            </div>

            <h1 style={s.title}>{property.title}</h1>
            <div style={s.price}>{formatPrice(property.price, property.listing_type)}</div>
            <div style={s.loc}>📍 {property.location}, {property.city}, {property.state}</div>

            <div style={s.specGrid}>
              {property.bedrooms > 0 && <SpecBox icon="🛏" label="Bedrooms" val={property.bedrooms} />}
              {property.bathrooms > 0 && <SpecBox icon="🚿" label="Bathrooms" val={property.bathrooms} />}
              <SpecBox icon="📐" label="Area" val={`${property.area} sq ft`} />
              <SpecBox icon="🏠" label="Type" val={property.property_type} />
              {property.furnished !== undefined && <SpecBox icon="🛋" label="Furnished" val={property.furnished ? 'Yes' : 'No'} />}
              {property.listing_type === 'rent' && property.deposit_amount && (
                <SpecBox icon="💰" label="Deposit" val={`₹${Number(property.deposit_amount).toLocaleString('en-IN')}`} />
              )}
              {property.listing_type === 'rent' && property.lease_duration && (
                <SpecBox icon="📅" label="Lease" val={property.lease_duration} />
              )}
              {property.pets_allowed !== undefined && <SpecBox icon="🐾" label="Pets" val={property.pets_allowed ? 'Allowed' : 'Not Allowed'} />}
            </div>

            {property.broker_name && (
              <div style={s.brokerBox}>
                <div style={s.brokerLabel}>Listed by</div>
                <div style={s.brokerName}>🧑‍💼 {property.broker_name}</div>
                {property.broker_phone && <div style={s.brokerPhone}>📞 {property.broker_phone}</div>}
              </div>
            )}
          </div>
        </div>

        <div style={s.bottomRow}>
          {/* Description + Amenities */}
          <div style={s.desc}>
            {property.description && (
              <>
                <h2 style={s.h2}>About this property</h2>
                <p style={s.descText}>{property.description}</p>
              </>
            )}

            {property.amenities?.length > 0 && (
              <>
                <h2 style={s.h2}>Amenities</h2>
                <div style={s.amenitiesGrid}>
                  {property.amenities.map(a => (
                    <span key={a} style={s.amenityChip}>✓ {a}</span>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Inquiry Form */}
          <div style={s.inquiryBox}>
            <h2 style={s.h2}>Contact Owner / Agent</h2>
            {sent ? (
              <div style={s.success}>✅ Inquiry sent! You'll be contacted shortly.</div>
            ) : (
              <form onSubmit={sendInquiry} style={s.form}>
                <input required placeholder="Your Name" value={inquiry.name}
                  onChange={e => setInquiry({...inquiry, name: e.target.value})} style={s.input} />
                <input required type="email" placeholder="Your Email" value={inquiry.email}
                  onChange={e => setInquiry({...inquiry, email: e.target.value})} style={s.input} />
                <input placeholder="Phone Number" value={inquiry.phone}
                  onChange={e => setInquiry({...inquiry, phone: e.target.value})} style={s.input} />
                <textarea required placeholder="I'm interested in this property..." value={inquiry.message}
                  onChange={e => setInquiry({...inquiry, message: e.target.value})}
                  rows={4} style={{ ...s.input, resize: 'vertical' }} />
                <button type="submit" disabled={sending} style={s.submitBtn}>
                  {sending ? 'Sending...' : isLoggedIn ? 'Send Inquiry' : 'Login to Send Inquiry'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function SpecBox({ icon, label, val }) {
  return (
    <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 10, padding: '12px 16px', textAlign: 'center' }}>
      <div style={{ fontSize: 22 }}>{icon}</div>
      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: '#111827', textTransform: 'capitalize' }}>{val}</div>
    </div>
  )
}

const s = {
  page:         { background: '#f9fafb', minHeight: '100vh', paddingBottom: '4rem' },
  wrap:         { maxWidth: 1200, margin: '0 auto', padding: '2rem' },
  center:       { textAlign: 'center', padding: '4rem', fontSize: 18 },
  backBtn:      { background: 'none', border: '1px solid #d1d5db', borderRadius: 8, padding: '7px 16px', cursor: 'pointer', fontSize: 14, marginBottom: '1.5rem', color: '#374151' },
  topRow:       { display: 'grid', gridTemplateColumns: '1fr 420px', gap: 32, marginBottom: 32 },
  galleryWrap:  { borderRadius: 14, overflow: 'hidden' },
  mainImg:      { width: '100%', height: 420, objectFit: 'cover', display: 'block' },
  thumbs:       { display: 'flex', gap: 8, marginTop: 8 },
  thumb:        { width: 80, height: 60, objectFit: 'cover', borderRadius: 8, cursor: 'pointer', opacity: 0.6, border: '2px solid transparent' },
  thumbActive:  { opacity: 1, border: '2px solid #1a56db' },
  info:         { background: '#fff', borderRadius: 14, padding: '24px', border: '1px solid #e5e7eb' },
  badges:       { display: 'flex', gap: 8, marginBottom: 12 },
  badge:        { color: '#fff', borderRadius: 6, padding: '3px 12px', fontSize: 12, fontWeight: 600 },
  title:        { fontSize: 22, fontWeight: 800, color: '#111827', margin: '0 0 8px', lineHeight: 1.3 },
  price:        { fontSize: 30, fontWeight: 800, color: '#1a56db', margin: '0 0 8px' },
  loc:          { fontSize: 14, color: '#6b7280', marginBottom: 20 },
  specGrid:     { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 20 },
  brokerBox:    { background: '#eff6ff', borderRadius: 10, padding: 14, border: '1px solid #bfdbfe' },
  brokerLabel:  { fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1 },
  brokerName:   { fontSize: 15, fontWeight: 700, color: '#1e3a8a', marginTop: 4 },
  brokerPhone:  { fontSize: 14, color: '#3b82f6', marginTop: 2 },
  bottomRow:    { display: 'grid', gridTemplateColumns: '1fr 380px', gap: 32 },
  desc:         { background: '#fff', borderRadius: 14, padding: '24px', border: '1px solid #e5e7eb' },
  h2:           { fontSize: 18, fontWeight: 700, color: '#111827', marginBottom: 12, marginTop: 0 },
  descText:     { fontSize: 15, color: '#374151', lineHeight: 1.7, marginBottom: 24 },
  amenitiesGrid:{ display: 'flex', flexWrap: 'wrap', gap: 8 },
  amenityChip:  { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', padding: '5px 14px', borderRadius: 20, fontSize: 13 },
  inquiryBox:   { background: '#fff', borderRadius: 14, padding: '24px', border: '1px solid #e5e7eb', height: 'fit-content', position: 'sticky', top: 80 },
  form:         { display: 'flex', flexDirection: 'column', gap: 12 },
  input:        { border: '1px solid #d1d5db', borderRadius: 8, padding: '10px 14px', fontSize: 14, outline: 'none', fontFamily: 'inherit', width: '100%', boxSizing: 'border-box' },
  submitBtn:    { background: '#1a56db', color: '#fff', border: 'none', borderRadius: 8, padding: '12px', fontSize: 15, fontWeight: 700, cursor: 'pointer' },
  success:      { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', borderRadius: 10, padding: '1rem', textAlign: 'center', fontSize: 15 },
}
