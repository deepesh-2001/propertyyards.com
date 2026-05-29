import { Link } from 'react-router-dom'

export function formatPrice(price, listingType) {
  if (listingType === 'rent') return `₹${price.toLocaleString('en-IN')}/mo`
  if (price >= 10000000) return `₹${(price / 10000000).toFixed(2)} Cr`
  if (price >= 100000)   return `₹${(price / 100000).toFixed(1)} L`
  return `₹${price.toLocaleString('en-IN')}`
}

export default function PropertyCard({ property }) {
  const { id, title, city, state, price, listing_type, bedrooms, bathrooms, area, images, featured, premium_listing, property_type, furnished } = property

  return (
    <Link to={`/property/${id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
      <div style={s.card}>
        <div style={s.imgWrap}>
          <img
            src={images?.[0] || `https://picsum.photos/seed/${id}/800/600`}
            alt={title}
            style={s.img}
            onError={e => { e.target.src = `https://picsum.photos/seed/default${id}/800/600` }}
          />
          <div style={s.badges}>
            {featured && <span style={{ ...s.badge, background: '#f59e0b' }}>⭐ Featured</span>}
            {premium_listing && <span style={{ ...s.badge, background: '#7c3aed' }}>Premium</span>}
          </div>
          <span style={{ ...s.typeBadge, background: listing_type === 'rent' ? '#059669' : '#1a56db' }}>
            {listing_type === 'rent' ? 'For Rent' : 'For Sale'}
          </span>
        </div>
        <div style={s.body}>
          <div style={s.price}>{formatPrice(price, listing_type)}</div>
          <div style={s.title}>{title}</div>
          <div style={s.loc}>📍 {city}, {state}</div>
          <div style={s.specs}>
            {bedrooms > 0 && <span style={s.spec}>🛏 {bedrooms} Bed</span>}
            {bathrooms > 0 && <span style={s.spec}>🚿 {bathrooms} Bath</span>}
            <span style={s.spec}>📐 {area} sq ft</span>
            {furnished && <span style={s.spec}>🛋 Furnished</span>}
            <span style={{ ...s.spec, marginLeft: 'auto', textTransform: 'capitalize', color: '#9ca3af' }}>{property_type}</span>
          </div>
        </div>
      </div>
    </Link>
  )
}

const s = {
  card:     { border: '1px solid #e5e7eb', borderRadius: 14, overflow: 'hidden', background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', transition: 'all 0.2s', cursor: 'pointer' },
  imgWrap:  { position: 'relative', height: 210 },
  img:      { width: '100%', height: '100%', objectFit: 'cover' },
  badges:   { position: 'absolute', top: 10, left: 10, display: 'flex', flexDirection: 'column', gap: 4 },
  badge:    { color: '#fff', borderRadius: 5, padding: '2px 10px', fontSize: 11, fontWeight: 700 },
  typeBadge:{ position: 'absolute', top: 10, right: 10, color: '#fff', borderRadius: 6, padding: '3px 12px', fontSize: 12, fontWeight: 600 },
  body:     { padding: '14px 16px' },
  price:    { fontSize: 21, fontWeight: 800, color: '#1a56db', marginBottom: 4 },
  title:    { fontSize: 14, fontWeight: 600, color: '#111827', marginBottom: 5, lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' },
  loc:      { fontSize: 13, color: '#6b7280', marginBottom: 10 },
  specs:    { display: 'flex', gap: 10, fontSize: 12, color: '#374151', borderTop: '1px solid #f3f4f6', paddingTop: 10, flexWrap: 'wrap' },
  spec:     { background: '#f9fafb', padding: '3px 8px', borderRadius: 5 },
}
