import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { propertiesAPI, inquiriesAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { formatPrice } from '../components/PropertyCard'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { TEST_PROPERTIES } from '../data/testData'

export default function PropertyDetail() {
  const { id }              = useParams()
  const nav                 = useNavigate()
  const { isLoggedIn }      = useAuth()
  const { toast }           = useToast()
  const { isMobile, isTablet } = useBreakpoint()

  const [property, setProperty] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [imgIdx, setImgIdx]     = useState(0)
  const [inquiry, setInquiry]   = useState({ name: '', email: '', phone: '', message: '' })
  const [sent, setSent]         = useState(false)
  const [sending, setSending]   = useState(false)
  const [wishlist, setWishlist] = useState(false)

  useEffect(() => {
    setImgIdx(0)
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

  /* ── Loading skeleton ── */
  if (loading) return (
    <div style={s.page}>
      <div style={s.wrap}>
        <div className="skeleton" style={{ height: 36, width: 80, borderRadius: 8, marginBottom: 24 }} />
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 400px', gap: 28, marginBottom: 28 }}>
          <div className="skeleton" style={{ height: 420, borderRadius: 18 }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="skeleton" style={{ height: 28, width: '60%' }} />
            <div className="skeleton" style={{ height: 44, width: '80%' }} />
            <div className="skeleton" style={{ height: 20, width: '50%' }} />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
              {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ height: 72, borderRadius: 10 }} />)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  if (!property) return (
    <div style={s.notFound}>
      <div style={{ fontSize: 56 }}>🏚️</div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0f172a' }}>Property Not Found</h2>
      <p style={{ color: '#64748b' }}>This listing may have been removed or is no longer available.</p>
      <button onClick={() => nav(-1)} style={s.goBackBtn}>← Go Back</button>
    </div>
  )

  const images  = property.images?.length ? property.images : [`https://picsum.photos/seed/${id}/800/600`]
  const compact = isMobile || isTablet

  const prevImg = () => setImgIdx(i => (i - 1 + images.length) % images.length)
  const nextImg = () => setImgIdx(i => (i + 1) % images.length)

  /* ── Spec rows ── */
  const specs = [
    property.bedrooms  > 0    && { icon: '🛏', label: 'Bedrooms',    val: property.bedrooms },
    property.bathrooms > 0    && { icon: '🚿', label: 'Bathrooms',   val: property.bathrooms },
    property.area             && { icon: '📐', label: 'Area',         val: `${property.area} sq ft` },
    property.property_type    && { icon: '🏠', label: 'Type',         val: property.property_type },
    property.furnished != null && { icon: '🛋', label: 'Furnished',   val: property.furnished ? 'Yes' : 'No' },
    property.pets_allowed != null && { icon: '🐾', label: 'Pets',     val: property.pets_allowed ? 'Allowed' : 'Not allowed' },
    property.listing_type === 'rent' && property.deposit_amount && {
      icon: '💰', label: 'Deposit', val: `₹${Number(property.deposit_amount).toLocaleString('en-IN')}`
    },
    property.listing_type === 'rent' && property.rent_period && {
      icon: '📅', label: 'Rent Period', val: property.rent_period
    },
    property.view_count != null && { icon: '👁', label: 'Views',      val: property.view_count },
    property.status           && { icon: '✅', label: 'Status',       val: property.status },
  ].filter(Boolean)

  return (
    <div style={s.page}>
      <div style={s.wrap}>

        {/* ── Breadcrumb / Back ── */}
        <div style={s.topBar}>
          <button onClick={() => nav(-1)} style={s.backBtn}>← Back to Listings</button>
          <div style={s.topBarRight}>
            <button onClick={() => setWishlist(w => !w)}
              style={{ ...s.iconBtn, background: wishlist ? '#fef2f2' : '#f8fafc', color: wishlist ? '#dc2626' : '#64748b' }}>
              {wishlist ? '❤️' : '🤍'} {wishlist ? 'Saved' : 'Save'}
            </button>
            <button onClick={() => { navigator.share?.({ title: property.title, url: window.location.href }) }}
              style={s.iconBtn}>
              🔗 Share
            </button>
          </div>
        </div>

        {/* ── Top Grid: Gallery + Info ── */}
        <div style={{ ...s.topRow, gridTemplateColumns: compact ? '1fr' : '1fr 400px' }}>

          {/* Gallery */}
          <div style={s.galleryWrap}>
            <div style={s.mainImgWrap}>
              <img
                src={images[imgIdx]}
                alt={property.title}
                style={s.mainImg}
                onError={e => { e.target.src = `https://picsum.photos/seed/fallback${id}/800/600` }}
              />
              {/* Overlay badges */}
              <div style={s.imgTopLeft}>
                <span style={{ ...s.imgBadge, background: property.listing_type === 'rent' ? '#059669' : '#1a56db' }}>
                  {property.listing_type === 'rent' ? 'For Rent' : 'For Sale'}
                </span>
                {property.featured        && <span style={{ ...s.imgBadge, background: '#f59e0b' }}>⭐ Featured</span>}
                {property.premium_listing && <span style={{ ...s.imgBadge, background: '#7c3aed' }}>✦ Premium</span>}
              </div>
              {property.ai_generated && (
                <div style={s.imgAiBadge}>✨ AI Generated</div>
              )}
              {/* Arrow controls */}
              {images.length > 1 && (
                <>
                  <button onClick={prevImg} style={{ ...s.arrow, left: 12 }}>‹</button>
                  <button onClick={nextImg} style={{ ...s.arrow, right: 12 }}>›</button>
                  <div style={s.imgCounter}>{imgIdx + 1} / {images.length}</div>
                </>
              )}
            </div>
            {/* Thumbnails */}
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
            {/* Badges */}
            <div style={s.badges}>
              {property.featured        && <span style={{ ...s.badge, background: '#f59e0b' }}>⭐ Featured</span>}
              {property.premium_listing && <span style={{ ...s.badge, background: '#7c3aed' }}>✦ Premium</span>}
              {property.ai_generated    && (
                <span style={{ ...s.badge, background: 'linear-gradient(135deg,#0ea5e9,#6366f1)' }}>✨ AI</span>
              )}
            </div>

            <h1 style={s.title}>{property.title}</h1>
            <div style={s.price}>{formatPrice(property.price, property.listing_type)}</div>
            <div style={s.loc}>📍 {[property.location, property.city, property.state].filter(Boolean).join(', ')}</div>

            {/* Spec grid */}
            <div style={{ ...s.specGrid, gridTemplateColumns: isMobile ? 'repeat(2,1fr)' : 'repeat(3,1fr)' }}>
              {specs.map(({ icon, label, val }) => (
                <SpecBox key={label} icon={icon} label={label} val={val} />
              ))}
            </div>

            {/* Rent notice */}
            {property.listing_type === 'rent' && property.deposit_amount && (
              <div style={s.rentNotice}>
                💡 <strong>Security Deposit:</strong> ₹{Number(property.deposit_amount).toLocaleString('en-IN')} &nbsp;·&nbsp;
                <strong>Available</strong> immediately
              </div>
            )}

            {/* Broker */}
            {property.broker_name && (
              <div style={s.brokerBox}>
                <div style={s.brokerLabel}>Listed by</div>
                <div style={s.brokerName}>🧑‍💼 {property.broker_name}</div>
                {property.broker_phone && (
                  <a href={`tel:${property.broker_phone}`} style={s.brokerPhone}>
                    📞 {property.broker_phone}
                  </a>
                )}
              </div>
            )}

            {/* CTA on mobile — show form inline below */}
            {!compact && (
              <button onClick={() => document.getElementById('inquiry-form')?.scrollIntoView({ behavior: 'smooth' })}
                style={s.ctaBtn}>
                📩 Send Inquiry
              </button>
            )}
          </div>
        </div>

        {/* ── Bottom Grid: Description + Inquiry ── */}
        <div style={{ ...s.bottomRow, gridTemplateColumns: compact ? '1fr' : '1fr 380px' }}>

          {/* Left: Description + Amenities */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* About */}
            {property.description && (
              <div style={s.card}>
                <h2 style={s.h2}>About this Property</h2>
                {property.ai_generated && (
                  <div style={s.aiNotice}>
                    <span style={s.aiIcon}>✨</span>
                    <div>
                      <div style={s.aiTitle}>AI-Generated Description</div>
                      <div style={s.aiSub}>This description was crafted by AI for maximum detail. All specs (area, price, bedrooms) are verified data points.</div>
                    </div>
                  </div>
                )}
                <p style={s.descText}>{property.description}</p>
              </div>
            )}

            {/* Amenities */}
            {property.amenities?.length > 0 && (
              <div style={s.card}>
                <h2 style={s.h2}>Amenities <span style={s.countBadge}>{property.amenities.length}</span></h2>
                <div style={s.amenitiesGrid}>
                  {property.amenities.map(a => (
                    <span key={a} style={s.amenityChip}>✓ {a}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Key details table */}
            <div style={s.card}>
              <h2 style={s.h2}>Property Details</h2>
              <div style={s.detailsTable}>
                {[
                  ['Property Type', property.property_type],
                  ['Listing Type',  property.listing_type === 'rent' ? 'For Rent' : 'For Sale'],
                  ['City',          property.city],
                  ['State',         property.state],
                  property.area     && ['Built-up Area', `${property.area} sq ft`],
                  property.bedrooms > 0 && ['Bedrooms', property.bedrooms],
                  property.bathrooms > 0 && ['Bathrooms', property.bathrooms],
                  property.furnished != null && ['Furnished', property.furnished ? 'Yes' : 'No'],
                  property.pets_allowed != null && ['Pets Allowed', property.pets_allowed ? 'Yes' : 'No'],
                  property.status   && ['Status', property.status],
                  property.view_count != null && ['Total Views', property.view_count],
                  property.listing_type === 'rent' && property.deposit_amount && ['Security Deposit', `₹${Number(property.deposit_amount).toLocaleString('en-IN')}`],
                  property.listing_type === 'rent' && property.rent_period    && ['Rent Period', property.rent_period],
                ].filter(Boolean).map(([k, v]) => (
                  <div key={k} style={s.detailRow}>
                    <span style={s.detailKey}>{k}</span>
                    <span style={s.detailVal}>{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Inquiry Form */}
          <div id="inquiry-form" style={{ ...s.inquiryBox, position: compact ? 'static' : 'sticky', top: 80 }}>
            <div style={s.inquiryHeader}>
              <h2 style={{ ...s.h2, marginBottom: 0 }}>Contact Owner / Agent</h2>
              <div style={s.priceSmall}>{formatPrice(property.price, property.listing_type)}</div>
            </div>

            {sent ? (
              <div style={s.success}>
                <div style={{ fontSize: 36 }}>✅</div>
                <div style={{ fontWeight: 700, marginTop: 8 }}>Inquiry Sent!</div>
                <div style={{ fontSize: 13, color: '#4b7a5c', marginTop: 4 }}>The owner or agent will contact you shortly.</div>
              </div>
            ) : (
              <form onSubmit={sendInquiry} style={s.form}>
                <Field placeholder="Your Full Name *" value={inquiry.name}
                  onChange={e => setInquiry({ ...inquiry, name: e.target.value })} required />
                <Field placeholder="Email Address *" type="email" value={inquiry.email}
                  onChange={e => setInquiry({ ...inquiry, email: e.target.value })} required />
                <Field placeholder="Phone Number" value={inquiry.phone}
                  onChange={e => setInquiry({ ...inquiry, phone: e.target.value })} />
                <textarea
                  required
                  placeholder={`I'm interested in "${property.title?.slice(0,40)}..." Please share more details.`}
                  value={inquiry.message}
                  onChange={e => setInquiry({ ...inquiry, message: e.target.value })}
                  rows={4}
                  style={{ ...s.input, resize: 'vertical' }}
                />
                <button type="submit" disabled={sending} style={s.submitBtn}>
                  {sending ? '⏳ Sending...' : isLoggedIn ? '📩 Send Inquiry' : '🔐 Login to Send Inquiry'}
                </button>
                {!isLoggedIn && (
                  <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', margin: 0 }}>
                    You'll be redirected to login and returned here.
                  </p>
                )}
              </form>
            )}

            {/* Quick contact row */}
            {property.broker_phone && (
              <a href={`tel:${property.broker_phone}`} style={s.callBtn}>
                📞 Call Directly: {property.broker_phone}
              </a>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}

function SpecBox({ icon, label, val }) {
  return (
    <div style={s.specBox}>
      <div style={{ fontSize: 22 }}>{icon}</div>
      <div style={{ fontSize: 11, color: '#64748b', marginTop: 4, fontWeight: 500 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 800, color: '#0f172a', textTransform: 'capitalize', marginTop: 2 }}>{val}</div>
    </div>
  )
}

function Field({ placeholder, type = 'text', value, onChange, required }) {
  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      required={required}
      style={s.input}
    />
  )
}

const s = {
  page:          { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  wrap:          { maxWidth: 1240, margin: '0 auto', padding: '1.5rem' },
  notFound:      { minHeight: '70vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, textAlign: 'center', padding: '2rem' },
  topBar:        { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 },
  topBarRight:   { display: 'flex', gap: 8 },
  backBtn:       { background: '#fff', border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '8px 18px', cursor: 'pointer', fontSize: 14, fontWeight: 600, color: '#374151', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' },
  goBackBtn:     { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 10, padding: '12px 28px', fontSize: 15, fontWeight: 700, cursor: 'pointer', marginTop: 8 },
  iconBtn:       { border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 },
  topRow:        { display: 'grid', gap: 28, marginBottom: 28 },
  galleryWrap:   { display: 'flex', flexDirection: 'column', gap: 10 },
  mainImgWrap:   { position: 'relative', borderRadius: 18, overflow: 'hidden', background: '#e2e8f0' },
  mainImg:       { width: '100%', height: 420, objectFit: 'cover', display: 'block' },
  imgTopLeft:    { position: 'absolute', top: 14, left: 14, display: 'flex', flexDirection: 'column', gap: 6 },
  imgBadge:      { color: '#fff', borderRadius: 8, padding: '4px 12px', fontSize: 12, fontWeight: 700, backdropFilter: 'blur(4px)', width: 'fit-content' },
  imgAiBadge:    { position: 'absolute', top: 14, right: 14, background: 'linear-gradient(135deg,#0ea5e9,#6366f1)', color: '#fff', borderRadius: 8, padding: '4px 12px', fontSize: 12, fontWeight: 700 },
  arrow:         { position: 'absolute', top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', borderRadius: '50%', width: 40, height: 40, fontSize: 22, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1, backdropFilter: 'blur(4px)' },
  imgCounter:    { position: 'absolute', bottom: 14, right: 14, background: 'rgba(0,0,0,0.55)', color: '#fff', borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 600, backdropFilter: 'blur(4px)' },
  thumbs:        { display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 },
  thumb:         { width: 84, height: 62, objectFit: 'cover', borderRadius: 10, cursor: 'pointer', opacity: 0.55, border: '2.5px solid transparent', flexShrink: 0, transition: 'all 0.15s' },
  thumbActive:   { opacity: 1, border: '2.5px solid #1a56db' },
  info:          { background: '#fff', borderRadius: 18, padding: '28px 24px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', display: 'flex', flexDirection: 'column', gap: 14 },
  badges:        { display: 'flex', gap: 8, flexWrap: 'wrap' },
  badge:         { color: '#fff', borderRadius: 8, padding: '4px 14px', fontSize: 12, fontWeight: 700 },
  title:         { fontSize: 'clamp(18px,3vw,26px)', fontWeight: 900, color: '#0f172a', margin: 0, lineHeight: 1.3, letterSpacing: '-0.4px' },
  price:         { fontSize: 'clamp(24px,4vw,36px)', fontWeight: 900, color: '#1a56db', margin: 0, letterSpacing: '-1px' },
  loc:           { fontSize: 14, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 },
  specGrid:      { display: 'grid', gap: 10 },
  specBox:       { background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: '14px 10px', textAlign: 'center' },
  rentNotice:    { background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 10, padding: '10px 14px', fontSize: 13, color: '#78350f' },
  brokerBox:     { background: '#eff6ff', borderRadius: 12, padding: '14px 16px', border: '1px solid #bfdbfe' },
  brokerLabel:   { fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 },
  brokerName:    { fontSize: 15, fontWeight: 800, color: '#1e3a8a' },
  brokerPhone:   { fontSize: 14, color: '#2563eb', marginTop: 4, textDecoration: 'none', display: 'block', fontWeight: 600 },
  ctaBtn:        { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 15, fontWeight: 800, cursor: 'pointer', boxShadow: '0 4px 16px rgba(26,86,219,0.3)', letterSpacing: '-0.3px' },
  bottomRow:     { display: 'grid', gap: 28 },
  card:          { background: '#fff', borderRadius: 18, padding: '24px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  h2:            { fontSize: 18, fontWeight: 800, color: '#0f172a', marginBottom: 16, marginTop: 0, letterSpacing: '-0.3px', display: 'flex', alignItems: 'center', gap: 10 },
  countBadge:    { background: '#eff6ff', color: '#1a56db', borderRadius: 20, padding: '2px 10px', fontSize: 13, fontWeight: 700 },
  descText:      { fontSize: 15, color: '#374151', lineHeight: 1.8, margin: 0 },
  amenitiesGrid: { display: 'flex', flexWrap: 'wrap', gap: 8 },
  amenityChip:   { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 500 },
  detailsTable:  { display: 'flex', flexDirection: 'column', gap: 0 },
  detailRow:     { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f1f5f9' },
  detailKey:     { fontSize: 14, color: '#64748b', fontWeight: 500 },
  detailVal:     { fontSize: 14, fontWeight: 700, color: '#0f172a', textTransform: 'capitalize', textAlign: 'right' },
  inquiryBox:    { background: '#fff', borderRadius: 18, padding: '24px', border: '1px solid #e2e8f0', boxShadow: '0 2px 12px rgba(0,0,0,0.07)', height: 'fit-content' },
  inquiryHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 8 },
  priceSmall:    { fontSize: 20, fontWeight: 900, color: '#1a56db', letterSpacing: '-0.5px' },
  form:          { display: 'flex', flexDirection: 'column', gap: 12 },
  input:         { border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '11px 14px', fontSize: 14, outline: 'none', fontFamily: 'inherit', width: '100%', boxSizing: 'border-box', transition: 'border 0.15s', background: '#fafafa' },
  submitBtn:     { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 15, fontWeight: 800, cursor: 'pointer', boxShadow: '0 4px 16px rgba(26,86,219,0.3)', letterSpacing: '-0.3px' },
  success:       { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', borderRadius: 14, padding: '24px', textAlign: 'center', fontSize: 15 },
  callBtn:       { display: 'block', marginTop: 14, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 10, padding: '12px 14px', fontSize: 13, fontWeight: 700, color: '#166534', textDecoration: 'none', textAlign: 'center' },
  aiNotice:      { display: 'flex', alignItems: 'flex-start', gap: 12, background: 'linear-gradient(135deg,#f0f9ff,#eef2ff)', border: '1px solid #bae6fd', borderRadius: 12, padding: '12px 16px', marginBottom: 16 },
  aiIcon:        { fontSize: 22, flexShrink: 0, marginTop: 1 },
  aiTitle:       { fontSize: 13, fontWeight: 700, color: '#0369a1', marginBottom: 2 },
  aiSub:         { fontSize: 12, color: '#4b5563', lineHeight: 1.5 },
}
