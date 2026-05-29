import { useState, useEffect } from 'react'
import { brokersAPI } from '../services/api'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'

const FALLBACK = [
  { id: 1, name: 'Rahul Sharma',  city: 'Gurgaon',   state: 'Haryana',        experience_years: 12, rating: 4.8, total_deals: 145, specialization: ['apartment','villa'],       license_number: 'RERA-382910', is_verified: true, phone: '+91 98100 11234' },
  { id: 2, name: 'Priya Verma',   city: 'Noida',      state: 'Uttar Pradesh',  experience_years: 8,  rating: 4.6, total_deals: 89,  specialization: ['apartment','commercial'],  license_number: 'RERA-294011', is_verified: true, phone: '+91 98200 22345' },
  { id: 3, name: 'Amit Patel',    city: 'Mumbai',     state: 'Maharashtra',    experience_years: 15, rating: 4.9, total_deals: 210, specialization: ['villa','plot'],            license_number: 'RERA-571234', is_verified: true, phone: '+91 98300 33456' },
  { id: 4, name: 'Sneha Nair',    city: 'Bangalore',  state: 'Karnataka',      experience_years: 6,  rating: 4.5, total_deals: 67,  specialization: ['apartment','house'],       license_number: 'RERA-182741', is_verified: true, phone: '+91 98400 44567' },
  { id: 5, name: 'Vikram Singh',  city: 'Gurgaon',    state: 'Haryana',        experience_years: 10, rating: 4.7, total_deals: 122, specialization: ['commercial','apartment'],  license_number: 'RERA-441920', is_verified: true, phone: '+91 98500 55678' },
  { id: 6, name: 'Anita Reddy',   city: 'Hyderabad',  state: 'Telangana',      experience_years: 9,  rating: 4.6, total_deals: 98,  specialization: ['villa','house'],           license_number: 'RERA-332812', is_verified: true, phone: '+91 98600 66789' },
  { id: 7, name: 'Karthik Raja',  city: 'Chennai',    state: 'Tamil Nadu',     experience_years: 11, rating: 4.7, total_deals: 134, specialization: ['apartment','commercial'],  license_number: 'RERA-229341', is_verified: true, phone: '+91 98700 77890' },
  { id: 8, name: 'Meera Joshi',   city: 'Pune',       state: 'Maharashtra',    experience_years: 7,  rating: 4.4, total_deals: 78,  specialization: ['house','plot'],            license_number: 'RERA-118234', is_verified: true, phone: '+91 98800 88901' },
]

const AVATAR_COLORS = [
  ['#1a56db','#7c3aed'], ['#059669','#0284c7'], ['#dc2626','#f59e0b'],
  ['#7c3aed','#ec4899'], ['#0284c7','#059669'], ['#f59e0b','#dc2626'],
]

export default function Brokers() {
  const { tr }         = useLang()
  const { isMobile }   = useBreakpoint()
  const [brokers, setBrokers] = useState([])
  const [loading, setLoading] = useState(true)
  const [city, setCity]       = useState('All')
  const [search, setSearch]   = useState('')

  useEffect(() => {
    brokersAPI.list()
      .then(r => setBrokers(r.data?.brokers || r.data || []))
      .catch(() => setBrokers(FALLBACK))
      .finally(() => setLoading(false))
  }, [])

  const cities = ['All', ...new Set(brokers.map(b => b.city))]
  const displayed = brokers.filter(b => {
    if (city !== 'All' && b.city !== city) return false
    if (search && !b.name?.toLowerCase().includes(search.toLowerCase()) &&
        !b.city?.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const cols = isMobile ? '1fr' : 'repeat(auto-fill,minmax(280px,1fr))'

  return (
    <div style={s.page}>
      {/* Hero banner */}
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>{tr('trustedBrokers')}</h1>
            <p style={s.sub}>{tr('brokersSub')}</p>
          </div>
          <div style={s.bannerStats}>
            {[['500+','Verified Agents'],['₹200Cr+','Deals Closed'],['4.7★','Avg Rating']].map(([v,l]) => (
              <div key={l} style={s.bStat}>
                <span style={s.bStatVal}>{v}</span>
                <span style={s.bStatLabel}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={s.wrap}>
        {/* Filters */}
        <div style={s.filtersRow}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search broker name or city..."
            style={s.searchInput}
          />
          <select value={city} onChange={e => setCity(e.target.value)} style={s.sel}>
            {cities.map(c => <option key={c} value={c}>{c === 'All' ? tr('allCities') : c}</option>)}
          </select>
        </div>

        <div style={s.resultCount}>
          {displayed.length} broker{displayed.length !== 1 ? 's' : ''} found
        </div>

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 24 }}>
            {Array(6).fill(0).map((_,i) => <BrokerSkeleton key={i} />)}
          </div>
        ) : displayed.length === 0 ? (
          <div style={s.empty}>
            <div style={{ fontSize: 52 }}>🔍</div>
            <p>No brokers found. Try a different city.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 24 }}>
            {displayed.map((b, idx) => <BrokerCard key={b.id || b._id} broker={b} idx={idx} tr={tr} />)}
          </div>
        )}
      </div>
    </div>
  )
}

function BrokerCard({ broker, idx, tr }) {
  const [hovered, setHovered] = useState(false)
  const [g1, g2] = AVATAR_COLORS[idx % AVATAR_COLORS.length]
  const stars = Math.floor(broker.rating || 0)
  const halfRating = ((broker.rating || 0) % 1) >= 0.5

  return (
    <div
      style={{ ...s.card, ...(hovered ? s.cardHover : {}) }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="fade-in"
    >
      <div style={{ ...s.avatar, background: `linear-gradient(135deg,${g1},${g2})` }}>
        {broker.name?.charAt(0)}
      </div>

      <div style={s.name}>{broker.name}</div>

      {broker.is_verified && (
        <div style={s.verified}>✓ RERA Verified</div>
      )}

      <div style={s.loc}>📍 {broker.city}, {broker.state}</div>

      <div style={s.ratingRow}>
        <span style={s.stars}>
          {'★'.repeat(stars)}{halfRating ? '½' : ''}{'☆'.repeat(5 - stars - (halfRating ? 1 : 0))}
        </span>
        <span style={s.ratingText}>{broker.rating}</span>
      </div>

      <div style={s.statsRow}>
        <div style={s.statItem}>
          <span style={s.statNum}>{broker.total_deals}</span>
          <span style={s.statLbl}>{tr('deals')}</span>
        </div>
        <div style={s.statDivider} />
        <div style={s.statItem}>
          <span style={s.statNum}>{broker.experience_years}</span>
          <span style={s.statLbl}>{tr('yearsExp')}</span>
        </div>
      </div>

      <div style={s.chips}>
        {broker.specialization?.map(sp => (
          <span key={sp} style={s.chip}>{sp}</span>
        ))}
      </div>

      <div style={s.rera}>{broker.license_number}</div>

      <a
        href={`tel:${broker.phone || ''}`}
        style={s.contactBtn}
      >
        {tr('contactBroker')}
      </a>
    </div>
  )
}

function BrokerSkeleton() {
  return (
    <div style={{ ...s.card, gap: 12 }}>
      <div className="skeleton" style={{ width: 80, height: 80, borderRadius: '50%' }} />
      <div className="skeleton" style={{ height: 18, width: '60%' }} />
      <div className="skeleton" style={{ height: 14, width: '40%' }} />
      <div className="skeleton" style={{ height: 14, width: '70%' }} />
      <div className="skeleton" style={{ height: 40, width: '100%', borderRadius: 10 }} />
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:      { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '3rem 0' },
  bannerInner: { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 24 },
  h1:          { fontSize: 'clamp(24px,4vw,36px)', fontWeight: 900, margin: 0, letterSpacing: '-0.5px' },
  sub:         { fontSize: 15, opacity: 0.75, marginTop: 6 },
  bannerStats: { display: 'flex', gap: 32 },
  bStat:       { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 },
  bStatVal:    { fontSize: 24, fontWeight: 800, letterSpacing: '-0.5px' },
  bStatLabel:  { fontSize: 12, opacity: 0.7, fontWeight: 500 },
  wrap:        { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  filtersRow:  { display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' },
  searchInput: { flex: 1, minWidth: 200, border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none', background: '#fff' },
  sel:         { border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '10px 16px', fontSize: 14, outline: 'none', background: '#fff' },
  resultCount: { fontSize: 13, color: '#64748b', marginBottom: 20, fontWeight: 500 },
  empty:       { textAlign: 'center', padding: '4rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 },
  card:        { background: '#fff', borderRadius: 20, padding: '28px 24px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 10, boxShadow: '0 1px 4px rgba(0,0,0,0.05)', transition: 'all 0.25s cubic-bezier(.4,0,.2,1)', cursor: 'default' },
  cardHover:   { transform: 'translateY(-5px)', boxShadow: '0 12px 40px rgba(0,0,0,0.12)' },
  avatar:      { width: 80, height: 80, borderRadius: '50%', color: '#fff', fontSize: 34, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 16px rgba(0,0,0,0.15)' },
  name:        { fontSize: 18, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.3px' },
  verified:    { background: '#d1fae5', color: '#065f46', borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 700 },
  loc:         { fontSize: 13, color: '#64748b' },
  ratingRow:   { display: 'flex', alignItems: 'center', gap: 6 },
  stars:       { color: '#f59e0b', fontSize: 16, letterSpacing: 1 },
  ratingText:  { fontSize: 14, fontWeight: 700, color: '#0f172a' },
  statsRow:    { display: 'flex', alignItems: 'center', gap: 16, background: '#f8fafc', borderRadius: 12, padding: '10px 20px', width: '100%', justifyContent: 'center' },
  statItem:    { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 },
  statNum:     { fontSize: 20, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.5px' },
  statLbl:     { fontSize: 11, color: '#64748b', fontWeight: 500 },
  statDivider: { width: 1, height: 30, background: '#e2e8f0' },
  chips:       { display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center' },
  chip:        { background: '#eff6ff', color: '#1d4ed8', borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 600, textTransform: 'capitalize' },
  rera:        { fontSize: 11, color: '#94a3b8', fontFamily: 'monospace', letterSpacing: 1 },
  contactBtn:  { width: '100%', background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '12px', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginTop: 4, textDecoration: 'none', display: 'block', boxShadow: '0 2px 8px rgba(26,86,219,0.3)', transition: 'all 0.2s' },
}
