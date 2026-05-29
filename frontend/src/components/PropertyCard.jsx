import { useState } from 'react'
import { Link } from 'react-router-dom'

export function formatPrice(price, listingType) {
  if (listingType === 'rent') return `₹${price.toLocaleString('en-IN')}/mo`
  if (price >= 10000000) return `₹${(price / 10000000).toFixed(2)} Cr`
  if (price >= 100000)   return `₹${(price / 100000).toFixed(1)} L`
  return `₹${price.toLocaleString('en-IN')}`
}

export function PropertyCardSkeleton() {
  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: 18, overflow: 'hidden', background: '#fff' }}>
      <div className="skeleton" style={{ height: 210 }} />
      <div style={{ padding: '16px' }}>
        <div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 10 }} />
        <div className="skeleton" style={{ height: 20, width: '80%', marginBottom: 8 }} />
        <div className="skeleton" style={{ height: 14, width: '55%', marginBottom: 14 }} />
        <div style={{ display: 'flex', gap: 8 }}>
          {[60, 70, 80].map((w, i) => <div key={i} className="skeleton" style={{ height: 28, width: w }} />)}
        </div>
      </div>
    </div>
  )
}

export default function PropertyCard({ property }) {
  const { id, title, city, state, price, listing_type, bedrooms, bathrooms, area, images, featured, premium_listing, property_type, furnished } = property
  const [wishlist, setWishlist] = useState(false)
  const [hovered, setHovered]  = useState(false)

  return (
    <div
      style={{ ...s.card, ...(hovered ? s.cardHover : {}) }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="fade-in"
    >
      <div style={s.imgWrap}>
        <Link to={`/property/${id}`}>
          <img
            src={images?.[0] || `https://picsum.photos/seed/${id}/800/600`}
            alt={title}
            style={{ ...s.img, transform: hovered ? 'scale(1.04)' : 'scale(1)' }}
            onError={e => { e.target.src = `https://picsum.photos/seed/fallback${id}/800/600` }}
          />
        </Link>
        <div style={s.overlay} />

        <div style={s.topLeft}>
          {featured        && <span style={{ ...s.tag, background: '#f59e0b' }}>⭐ Featured</span>}
          {premium_listing && <span style={{ ...s.tag, background: '#7c3aed' }}>✦ Premium</span>}
        </div>
        <span style={{ ...s.typeTag, background: listing_type === 'rent' ? '#059669' : '#1a56db' }}>
          {listing_type === 'rent' ? 'For Rent' : 'For Sale'}
        </span>
        <button
          onClick={() => setWishlist(w => !w)}
          style={{ ...s.heart, background: wishlist ? '#fef2f2' : 'rgba(255,255,255,0.9)' }}
          title={wishlist ? 'Remove from wishlist' : 'Add to wishlist'}
        >
          {wishlist ? '❤️' : '🤍'}
        </button>
      </div>

      <Link to={`/property/${id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
        <div style={s.body}>
          <div style={s.price}>{formatPrice(price, listing_type)}</div>
          <div style={s.title}>{title}</div>
          <div style={s.loc}>
            <span style={s.locDot}>📍</span> {city}, {state}
          </div>
          <div style={s.specRow}>
            {bedrooms  > 0 && <Spec icon="🛏" val={`${bedrooms} Bed`} />}
            {bathrooms > 0 && <Spec icon="🚿" val={`${bathrooms} Bath`} />}
            <Spec icon="📐" val={`${area} sq ft`} />
            {furnished     && <Spec icon="🛋" val="Furnished" />}
          </div>
          <div style={s.footer}>
            <span style={s.propType}>{property_type}</span>
            <span style={s.viewLink}>View Details →</span>
          </div>
        </div>
      </Link>
    </div>
  )
}

function Spec({ icon, val }) {
  return (
    <span style={s.spec}>{icon} {val}</span>
  )
}

const s = {
  card:     { border: '1px solid #e2e8f0', borderRadius: 18, overflow: 'hidden', background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.05)', transition: 'all 0.25s cubic-bezier(.4,0,.2,1)', cursor: 'pointer' },
  cardHover:{ boxShadow: '0 12px 40px rgba(0,0,0,0.12)', transform: 'translateY(-4px)' },
  imgWrap:  { position: 'relative', height: 215, overflow: 'hidden' },
  img:      { width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.4s ease', display: 'block' },
  overlay:  { position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(0,0,0,0.3) 0%, transparent 50%)', pointerEvents: 'none' },
  topLeft:  { position: 'absolute', top: 10, left: 10, display: 'flex', flexDirection: 'column', gap: 4 },
  tag:      { color: '#fff', borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700, backdropFilter: 'blur(4px)' },
  typeTag:  { position: 'absolute', bottom: 10, left: 10, color: '#fff', borderRadius: 8, padding: '4px 12px', fontSize: 12, fontWeight: 700, backdropFilter: 'blur(4px)' },
  heart:    { position: 'absolute', top: 10, right: 10, border: 'none', borderRadius: '50%', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.15)', transition: 'transform 0.2s' },
  body:     { padding: '16px 18px' },
  price:    { fontSize: 22, fontWeight: 800, color: '#1a56db', marginBottom: 6, letterSpacing: '-0.5px' },
  title:    { fontSize: 14, fontWeight: 600, color: '#0f172a', marginBottom: 6, lineHeight: 1.45, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' },
  loc:      { fontSize: 13, color: '#64748b', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 4 },
  locDot:   { fontSize: 12 },
  specRow:  { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 },
  spec:     { background: '#f1f5f9', color: '#475569', fontSize: 12, fontWeight: 500, padding: '4px 10px', borderRadius: 6 },
  footer:   { display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f1f5f9', paddingTop: 10 },
  propType: { fontSize: 12, color: '#94a3b8', textTransform: 'capitalize', fontWeight: 500 },
  viewLink: { fontSize: 12, color: '#1a56db', fontWeight: 700 },
}
