import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import PropertyCard, { PropertyCardSkeleton } from '../components/PropertyCard'
import { propertiesAPI } from '../services/api'
import { TEST_PROPERTIES } from '../data/testData'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useTimeGreeting } from '../hooks/useTimeGreeting'

const CITIES = ['All', 'Gurgaon', 'Noida', 'Delhi', 'Greater Noida', 'Faridabad', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune']
const TYPES  = ['All', 'apartment', 'villa', 'house', 'plot', 'commercial', 'studio']

export default function Home() {
  const { tr } = useLang()
  const { isMobile, isTablet } = useBreakpoint()
  const greetKey = useTimeGreeting()
  const cols = isMobile ? '1fr' : isTablet ? 'repeat(2,1fr)' : 'repeat(auto-fill,minmax(300px,1fr))'
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
        <div style={s.greetBadge}>{tr(greetKey)}</div>
        <h1 style={s.heroH1}>{tr('heroTitle')}</h1>
        <p style={s.heroP}>{tr('heroSub')}</p>

        <div style={s.searchBar}>
          <input
            placeholder={tr('searchPlaceholder')}
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={s.searchInput}
          />
          <div style={s.filterRow}>
            <select value={listingType} onChange={e => setListingType(e.target.value)} style={s.sel}>
              <option value="all">{tr('buyRent')}</option>
              <option value="sale">{tr('buy')}</option>
              <option value="rent">{tr('rent')}</option>
            </select>
            <select value={propType} onChange={e => setPropType(e.target.value)} style={s.sel}>
              {TYPES.map(t => <option key={t} value={t}>{t === 'All' ? tr('allTypes') : t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
            <select value={beds} onChange={e => setBeds(e.target.value)} style={s.sel}>
              {['Any','1','2','3','4','5'].map(b => <option key={b} value={b}>{b === 'Any' ? tr('anyBeds') : `${b} ${tr('bhk')}`}</option>)}
            </select>
            <input placeholder={tr('minPrice')} type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)} style={{ ...s.sel, width: 120 }} />
            <input placeholder={tr('maxPrice')} type="number" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} style={{ ...s.sel, width: 120 }} />
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
          {[['15,000+',tr('activeListings')],['10+',tr('citiesCovered')],['50,000+',tr('happyBuyers')],['₹50Cr+',tr('propertiesSold')]].map(([v,l]) => (
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
          <div style={s.empty}>{tr('noResults')}</div>
        ) : (
          <>
            {featured.length > 0 && <Section title={tr('featured')}   items={featured} cols={cols} />}
            {gurgaon.length  > 0 && <Section title={tr('gurgaon')}    items={gurgaon}  cols={cols} />}
            {nearby.length   > 0 && <Section title={tr('nearby')}     items={nearby}   cols={cols} />}
            {others.length   > 0 && <Section title={tr('otherCities')} items={others}  cols={cols} />}
            {featured.length === 0 && gurgaon.length === 0 && nearby.length === 0 && others.length === 0 && (
              <Section title="All Properties" items={filtered} cols={cols} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

function Section({ title, items, cols }) {
  return (
    <div style={{ marginBottom: '3rem' }}>
      <h2 style={s.sectionTitle}>{title} <span style={s.count}>({items.length})</span></h2>
      <div style={{ ...s.grid, gridTemplateColumns: cols }}>
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
  greetBadge: { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600, marginBottom: 16, backdropFilter: 'blur(4px)' },
  heroH1:      { fontSize: 'clamp(28px, 5vw, 46px)', fontWeight: 900, margin: '0 0 0.75rem', letterSpacing: '-1.5px', lineHeight: 1.1 },
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
