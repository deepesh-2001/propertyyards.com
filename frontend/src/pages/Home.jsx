import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import PropertyCard, { PropertyCardSkeleton } from '../components/PropertyCard'
import { propertiesAPI } from '../services/api'
import { TEST_PROPERTIES } from '../data/testData'

const CITIES = ['All', 'Gurgaon', 'Noida', 'Delhi', 'Greater Noida', 'Faridabad', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune']
const TYPES  = ['All', 'apartment', 'villa', 'house', 'plot', 'commercial', 'studio']

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [properties, setProperties] = useState([])
  const [loading, setLoading]         = useState(true)
  const [search, setSearch]           = useState('')
  const [city, setCity]               = useState('All')
  const [propType, setPropType]       = useState('All')
  const [listingType, setListingType] = useState(searchParams.get('type') || 'all')
  const [minPrice, setMinPrice]       = useState('')
  const [maxPrice, setMaxPrice]       = useState('')
  const [beds, setBeds]               = useState('Any')

  useEffect(() => {
    propertiesAPI.list({ limit: 100 })
      .then(r => setProperties(r.data?.properties || r.data || []))
      .catch(() => setProperties(TEST_PROPERTIES))
      .finally(() => setLoading(false))
  }, [])

  const filtered = properties.filter(p => {
    if (search && !p.title?.toLowerCase().includes(search.toLowerCase()) &&
        !p.city?.toLowerCase().includes(search.toLowerCase()) &&
        !p.location?.toLowerCase().includes(search.toLowerCase())) return false
    if (city !== 'All' && p.city !== city) return false
    if (propType !== 'All' && p.property_type !== propType) return false
    if (listingType !== 'all' && p.listing_type !== listingType) return false
    if (minPrice && p.price < Number(minPrice)) return false
    if (maxPrice && p.price > Number(maxPrice)) return false
    if (beds !== 'Any' && p.bedrooms !== Number(beds)) return false
    return true
  })

  const featured  = filtered.filter(p => p.featured)
  const gurgaon   = filtered.filter(p => p.city === 'Gurgaon')
  const nearby    = filtered.filter(p => ['Noida','Greater Noida','Faridabad','Delhi'].includes(p.city))
  const others    = filtered.filter(p => !['Gurgaon','Noida','Greater Noida','Faridabad','Delhi'].includes(p.city))

  return (
    <div style={{ background: '#f9fafb', minHeight: '100vh' }}>
      {/* Hero */}
      <div style={s.hero}>
        <h1 style={s.heroH1}>Find Your Dream Property</h1>
        <p style={s.heroP}>Buy, Rent or Sell — India's most trusted real estate platform</p>

        <div style={s.searchBar}>
          <input
            placeholder="Search city, locality, project name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={s.searchInput}
          />
          <div style={s.filterRow}>
            <select value={listingType} onChange={e => setListingType(e.target.value)} style={s.sel}>
              <option value="all">Buy + Rent</option>
              <option value="sale">Buy</option>
              <option value="rent">Rent</option>
            </select>
            <select value={propType} onChange={e => setPropType(e.target.value)} style={s.sel}>
              {TYPES.map(t => <option key={t} value={t}>{t === 'All' ? 'All Types' : t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
            <select value={beds} onChange={e => setBeds(e.target.value)} style={s.sel}>
              {['Any','1','2','3','4','5'].map(b => <option key={b} value={b}>{b === 'Any' ? 'Any Beds' : `${b} BHK`}</option>)}
            </select>
            <input placeholder="Min Price ₹" type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)} style={{ ...s.sel, width: 120 }} />
            <input placeholder="Max Price ₹" type="number" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} style={{ ...s.sel, width: 120 }} />
          </div>
        </div>

        <div style={s.cityPills}>
          {CITIES.map(c => (
            <button key={c} onClick={() => setCity(c)}
              style={{ ...s.pill, ...(city === c ? s.pillActive : {}) }}>{c}</button>
          ))}
        </div>
      </div>

      <div style={s.statBar}>
        <div style={s.statWrap}>
          {[['15,000+','Active Listings'],['10+','Cities Covered'],['50,000+','Happy Buyers'],['₹50Cr+','Properties Sold']].map(([v,l]) => (
            <div key={l} style={s.stat}>
              <span style={s.statVal}>{v}</span>
              <span style={s.statLabel}>{l}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={s.main}>
        {loading ? (
          <div style={s.grid}>{Array(6).fill(0).map((_,i) => <PropertyCardSkeleton key={i} />)}</div>
        ) : filtered.length === 0 ? (
          <div style={s.empty}>No properties found. Try adjusting filters.</div>
        ) : (
          <>
            {featured.length > 0 && <Section title="🔥 Featured Properties" items={featured} />}
            {gurgaon.length  > 0 && <Section title="🏙️ Gurgaon" items={gurgaon} />}
            {nearby.length   > 0 && <Section title="📍 Noida, Greater Noida, Faridabad & Delhi" items={nearby} />}
            {others.length   > 0 && <Section title="🌆 Other Cities" items={others} />}
            {featured.length === 0 && gurgaon.length === 0 && nearby.length === 0 && others.length === 0 && (
              <Section title="All Properties" items={filtered} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

function Section({ title, items }) {
  return (
    <div style={{ marginBottom: '3rem' }}>
      <h2 style={s.sectionTitle}>{title} <span style={s.count}>({items.length})</span></h2>
      <div style={s.grid}>
        {items.map(p => <PropertyCard key={p.id || p._id} property={p} />)}
      </div>
    </div>
  )
}

const s = {
  hero:        { background: 'linear-gradient(135deg, #0f172a 0%, #1a56db 60%, #0e3a8c 100%)', padding: '5rem 2rem 3.5rem', textAlign: 'center', color: '#fff' },
  statBar:    { background: '#fff', borderBottom: '1px solid #e2e8f0', boxShadow: '0 1px 8px rgba(0,0,0,0.05)' },
  statWrap:   { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-around', height: 76, alignItems: 'center' },
  stat:       { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 },
  statVal:    { fontSize: 22, fontWeight: 800, color: '#1a56db', letterSpacing: '-0.5px' },
  statLabel:  { fontSize: 12, color: '#64748b', fontWeight: 500 },
  heroH1:      { fontSize: 46, fontWeight: 900, margin: '0 0 0.75rem', letterSpacing: '-1.5px', lineHeight: 1.1 },
  heroP:       { fontSize: 18, opacity: 0.85, margin: '0 0 2rem' },
  searchBar:   { background: '#fff', borderRadius: 14, padding: '16px 20px', maxWidth: 860, margin: '0 auto 1.5rem', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' },
  searchInput: { width: '100%', border: 'none', outline: 'none', fontSize: 16, padding: '6px 0', borderBottom: '2px solid #e5e7eb', marginBottom: 12, boxSizing: 'border-box' },
  filterRow:   { display: 'flex', gap: 8, flexWrap: 'wrap' },
  sel:         { border: '1px solid #d1d5db', borderRadius: 8, padding: '7px 10px', fontSize: 13, color: '#374151', background: '#f9fafb', flex: 1, minWidth: 90, outline: 'none' },
  cityPills:   { display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap' },
  pill:        { background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.25)', color: '#fff', padding: '6px 18px', borderRadius: 20, fontSize: 14, cursor: 'pointer' },
  pillActive:  { background: '#fff', color: '#1a56db', fontWeight: 700 },
  main:        { maxWidth: 1240, margin: '0 auto', padding: '3rem 1.5rem' },
  sectionTitle:{ fontSize: 24, fontWeight: 700, marginBottom: '1.2rem', color: '#111827' },
  count:       { fontSize: 16, color: '#6b7280', fontWeight: 400 },
  grid:        { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 },
  loading:     { textAlign: 'center', fontSize: 18, padding: '4rem', color: '#6b7280' },
  empty:       { textAlign: 'center', fontSize: 16, padding: '4rem', color: '#9ca3af' },
}
