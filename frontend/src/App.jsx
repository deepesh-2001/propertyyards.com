import { Routes, Route, Link } from 'react-router-dom'
import { TEST_PROPERTIES } from './data/testData'

function formatPrice(price, listingType) {
  if (listingType === 'rent') return `₹${price.toLocaleString('en-IN')}/mo`
  if (price >= 10000000) return `₹${(price / 10000000).toFixed(2)} Cr`
  if (price >= 100000)   return `₹${(price / 100000).toFixed(1)} L`
  return `₹${price.toLocaleString('en-IN')}`
}

function Navbar() {
  return (
    <nav style={{ background: '#1a56db', padding: '0 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
      <Link to="/" style={{ color: '#fff', fontWeight: 700, fontSize: 22, textDecoration: 'none' }}>🏠 PropertyYards</Link>
      <div style={{ display: 'flex', gap: 24 }}>
        <Link to="/" style={{ color: '#fff', textDecoration: 'none', fontSize: 15 }}>Buy</Link>
        <Link to="/rent" style={{ color: '#fff', textDecoration: 'none', fontSize: 15 }}>Rent</Link>
        <Link to="/login" style={{ background: '#fff', color: '#1a56db', padding: '6px 18px', borderRadius: 6, fontWeight: 600, textDecoration: 'none', fontSize: 15 }}>Login</Link>
      </div>
    </nav>
  )
}

function PropertyCard({ property }) {
  const { title, city, state, price, listing_type, bedrooms, bathrooms, area, images, featured, property_type } = property
  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 12, overflow: 'hidden', background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', transition: 'transform 0.15s', cursor: 'pointer' }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-3px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'none'}>
      <div style={{ position: 'relative' }}>
        <img src={images[0]} alt={title} style={{ width: '100%', height: 200, objectFit: 'cover' }} />
        {featured && <span style={{ position: 'absolute', top: 10, left: 10, background: '#f59e0b', color: '#fff', borderRadius: 4, padding: '2px 10px', fontSize: 12, fontWeight: 700 }}>Featured</span>}
        <span style={{ position: 'absolute', top: 10, right: 10, background: listing_type === 'rent' ? '#10b981' : '#1a56db', color: '#fff', borderRadius: 4, padding: '2px 10px', fontSize: 12, fontWeight: 600 }}>
          {listing_type === 'rent' ? 'Rent' : 'Sale'}
        </span>
      </div>
      <div style={{ padding: '14px 16px' }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: '#1a56db', marginBottom: 4 }}>{formatPrice(price, listing_type)}</div>
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4, color: '#111827', lineHeight: 1.3 }}>{title}</div>
        <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 10 }}>📍 {city}, {state}</div>
        <div style={{ display: 'flex', gap: 16, fontSize: 13, color: '#374151', borderTop: '1px solid #f3f4f6', paddingTop: 10 }}>
          {bedrooms > 0 && <span>🛏 {bedrooms} Beds</span>}
          {bathrooms > 0 && <span>🚿 {bathrooms} Baths</span>}
          <span>📐 {area} sq ft</span>
          <span style={{ marginLeft: 'auto', textTransform: 'capitalize', color: '#6b7280' }}>{property_type}</span>
        </div>
      </div>
    </div>
  )
}

function Home() {
  const forSale = TEST_PROPERTIES.filter(p => p.listing_type === 'sale')
  const forRent = TEST_PROPERTIES.filter(p => p.listing_type === 'rent')

  return (
    <div style={{ background: '#f9fafb', minHeight: '100vh' }}>
      <div style={{ background: 'linear-gradient(135deg, #1a56db, #0e3a8c)', padding: '4rem 2rem', textAlign: 'center', color: '#fff' }}>
        <h1 style={{ fontSize: 40, fontWeight: 800, margin: 0 }}>Find Your Dream Property</h1>
        <p style={{ fontSize: 18, opacity: 0.85, margin: '1rem 0 2rem' }}>Buy, Rent or Sell — India's trusted real estate platform</p>
        <div style={{ display: 'inline-flex', background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}>
          <input placeholder="Search city, locality, project..." style={{ border: 'none', outline: 'none', padding: '14px 20px', fontSize: 16, width: 360 }} />
          <button style={{ background: '#1a56db', color: '#fff', border: 'none', padding: '14px 28px', fontSize: 16, fontWeight: 600, cursor: 'pointer' }}>Search</button>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '3rem 2rem' }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: '1.5rem', color: '#111827' }}>🔥 Featured Properties</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24, marginBottom: '3rem' }}>
          {forSale.map(p => <PropertyCard key={p.id} property={p} />)}
        </div>

        <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: '1.5rem', color: '#111827' }}>🏡 Properties for Rent</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24 }}>
          {forRent.map(p => <PropertyCard key={p.id} property={p} />)}
        </div>
      </div>
    </div>
  )
}

function RentPage() {
  const forRent = TEST_PROPERTIES.filter(p => p.listing_type === 'rent')
  return (
    <div style={{ background: '#f9fafb', minHeight: '100vh', padding: '2rem' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: '1.5rem' }}>Properties for Rent</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24 }}>
          {forRent.map(p => <PropertyCard key={p.id} property={p} />)}
        </div>
      </div>
    </div>
  )
}

function LoginPage() {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#fff', borderRadius: 16, padding: '2.5rem', width: 380, boxShadow: '0 4px 24px rgba(0,0,0,0.1)' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', fontSize: 24, fontWeight: 700 }}>Login to PropertyYards</h2>
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 6 }}>Email</label>
          <input defaultValue="admin@propertyyards.com" style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 15, boxSizing: 'border-box' }} />
        </div>
        <div style={{ marginBottom: 24 }}>
          <label style={{ fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 6 }}>Password</label>
          <input type="password" defaultValue="Test@1234" style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 15, boxSizing: 'border-box' }} />
        </div>
        <button style={{ width: '100%', background: '#1a56db', color: '#fff', border: 'none', borderRadius: 8, padding: '12px', fontSize: 16, fontWeight: 600, cursor: 'pointer' }}>
          Login
        </button>
        <p style={{ textAlign: 'center', fontSize: 13, color: '#6b7280', marginTop: 16 }}>
          Test: admin@propertyyards.com / Test@1234
        </p>
      </div>
    </div>
  )
}

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/rent" element={<RentPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </>
  )
}

export default App
