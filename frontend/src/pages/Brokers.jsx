import { useState, useEffect } from 'react'
import { brokersAPI } from '../services/api'

const FALLBACK = [
  { id: 1, name: 'Rahul Sharma', city: 'Gurgaon', state: 'Haryana', experience_years: 12, rating: 4.8, total_deals: 145, specialization: ['apartment','villa'], license_number: 'RERA-382910', is_verified: true },
  { id: 2, name: 'Priya Verma', city: 'Noida', state: 'Uttar Pradesh', experience_years: 8, rating: 4.6, total_deals: 89, specialization: ['apartment','commercial'], license_number: 'RERA-294011', is_verified: true },
  { id: 3, name: 'Amit Patel', city: 'Mumbai', state: 'Maharashtra', experience_years: 15, rating: 4.9, total_deals: 210, specialization: ['villa','plot'], license_number: 'RERA-571234', is_verified: true },
  { id: 4, name: 'Sneha Nair', city: 'Bangalore', state: 'Karnataka', experience_years: 6, rating: 4.5, total_deals: 67, specialization: ['apartment','house'], license_number: 'RERA-182741', is_verified: true },
  { id: 5, name: 'Vikram Singh', city: 'Gurgaon', state: 'Haryana', experience_years: 10, rating: 4.7, total_deals: 122, specialization: ['commercial','apartment'], license_number: 'RERA-441920', is_verified: true },
  { id: 6, name: 'Anita Reddy', city: 'Hyderabad', state: 'Telangana', experience_years: 9, rating: 4.6, total_deals: 98, specialization: ['villa','house'], license_number: 'RERA-332812', is_verified: true },
]

export default function Brokers() {
  const [brokers, setBrokers] = useState([])
  const [loading, setLoading] = useState(true)
  const [city, setCity]       = useState('All')

  useEffect(() => {
    brokersAPI.list()
      .then(r => setBrokers(r.data?.brokers || r.data || []))
      .catch(() => setBrokers(FALLBACK))
      .finally(() => setLoading(false))
  }, [])

  const cities    = ['All', ...new Set(brokers.map(b => b.city))]
  const displayed = city === 'All' ? brokers : brokers.filter(b => b.city === city)

  return (
    <div style={s.page}>
      <div style={s.wrap}>
        <div style={s.header}>
          <div>
            <h1 style={s.h1}>Find Trusted Brokers</h1>
            <p style={s.sub}>RERA certified agents across India</p>
          </div>
          <select value={city} onChange={e => setCity(e.target.value)} style={s.sel}>
            {cities.map(c => <option key={c} value={c}>{c === 'All' ? 'All Cities' : c}</option>)}
          </select>
        </div>

        {loading ? (
          <div style={s.loading}>⏳ Loading brokers...</div>
        ) : (
          <div style={s.grid}>
            {displayed.map(b => <BrokerCard key={b.id || b._id} broker={b} />)}
          </div>
        )}
      </div>
    </div>
  )
}

function BrokerCard({ broker }) {
  const stars = '★'.repeat(Math.floor(broker.rating || 0)) + '☆'.repeat(5 - Math.floor(broker.rating || 0))
  return (
    <div style={s.card}>
      <div style={s.avatar}>{broker.name?.charAt(0)}</div>
      <div style={s.name}>{broker.name}</div>
      {broker.is_verified && <div style={s.verified}>✓ RERA Verified</div>}
      <div style={s.loc}>📍 {broker.city}, {broker.state}</div>
      <div style={s.rating}>
        <span style={{ color: '#f59e0b' }}>{stars}</span>
        <span style={{ fontSize: 13, color: '#374151', marginLeft: 6 }}>{broker.rating} · {broker.total_deals} deals</span>
      </div>
      <div style={s.exp}>{broker.experience_years} years experience</div>
      <div style={s.specs}>
        {broker.specialization?.map(sp => (
          <span key={sp} style={s.chip}>{sp}</span>
        ))}
      </div>
      <div style={s.rera}>{broker.license_number}</div>
      <button style={s.contactBtn}>📞 Contact Broker</button>
    </div>
  )
}

const s = {
  page:       { background: '#f9fafb', minHeight: '100vh', paddingBottom: '4rem' },
  wrap:       { maxWidth: 1200, margin: '0 auto', padding: '2rem' },
  header:     { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' },
  h1:         { fontSize: 30, fontWeight: 800, margin: 0, color: '#111827' },
  sub:        { fontSize: 15, color: '#6b7280', marginTop: 4 },
  sel:        { border: '1px solid #d1d5db', borderRadius: 10, padding: '10px 16px', fontSize: 14, outline: 'none', background: '#fff' },
  loading:    { textAlign: 'center', padding: '4rem', color: '#6b7280' },
  grid:       { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 24 },
  card:       { background: '#fff', borderRadius: 16, padding: '24px', border: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 8 },
  avatar:     { width: 72, height: 72, borderRadius: '50%', background: 'linear-gradient(135deg, #1a56db, #7c3aed)', color: '#fff', fontSize: 30, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  name:       { fontSize: 18, fontWeight: 700, color: '#111827' },
  verified:   { background: '#d1fae5', color: '#065f46', borderRadius: 12, padding: '3px 12px', fontSize: 12, fontWeight: 600 },
  loc:        { fontSize: 14, color: '#6b7280' },
  rating:     { display: 'flex', alignItems: 'center', fontSize: 16 },
  exp:        { fontSize: 13, color: '#6b7280' },
  specs:      { display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center' },
  chip:       { background: '#eff6ff', color: '#1a56db', borderRadius: 12, padding: '2px 10px', fontSize: 12, textTransform: 'capitalize' },
  rera:       { fontSize: 11, color: '#9ca3af', fontFamily: 'monospace' },
  contactBtn: { width: '100%', background: '#1a56db', color: '#fff', border: 'none', borderRadius: 10, padding: '11px', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginTop: 8 },
}
