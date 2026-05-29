import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { propertiesAPI, inquiriesAPI } from '../services/api'
import PropertyCard from '../components/PropertyCard'

export default function Dashboard() {
  const { user, isLoggedIn } = useAuth()
  const nav = useNavigate()
  const [tab, setTab]               = useState('properties')
  const [myProperties, setMyProps]  = useState([])
  const [myInquiries, setMyInquiries] = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    if (!isLoggedIn) { nav('/login'); return }
    Promise.allSettled([
      propertiesAPI.my().then(r => setMyProps(r.data?.properties || r.data || [])),
      inquiriesAPI.mine().then(r => setMyInquiries(r.data?.inquiries || r.data || [])),
    ]).finally(() => setLoading(false))
  }, [isLoggedIn])

  if (!isLoggedIn) return null

  const tabs = [
    { key: 'properties', label: '🏠 My Listings', count: myProperties.length },
    { key: 'inquiries',  label: '📩 My Inquiries', count: myInquiries.length },
  ]

  return (
    <div style={s.page}>
      <div style={s.wrap}>
        {/* Header */}
        <div style={s.header}>
          <div>
            <h1 style={s.h1}>Welcome back, {user?.email?.split('@')[0]} 👋</h1>
            <p style={s.sub}>Manage your properties and inquiries</p>
          </div>
          <Link to="/post-property" style={s.postBtn}>+ Post New Property</Link>
        </div>

        {/* Stats */}
        <div style={s.statsRow}>
          <StatCard icon="🏠" label="My Listings" val={myProperties.length} color="#1a56db" />
          <StatCard icon="📩" label="Inquiries Received" val={myInquiries.length} color="#059669" />
          <StatCard icon="👁" label="Total Views" val={myProperties.reduce((a, p) => a + (p.view_count || 0), 0)} color="#7c3aed" />
        </div>

        {/* Tabs */}
        <div style={s.tabs}>
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              style={{ ...s.tab, ...(tab === t.key ? s.tabActive : {}) }}>
              {t.label} {t.count > 0 && <span style={s.cnt}>{t.count}</span>}
            </button>
          ))}
        </div>

        {loading ? (
          <div style={s.loading}>⏳ Loading...</div>
        ) : tab === 'properties' ? (
          myProperties.length === 0 ? (
            <div style={s.empty}>
              <div style={{ fontSize: 48 }}>🏠</div>
              <p>No properties listed yet</p>
              <Link to="/post-property" style={s.postBtn}>Post Your First Property</Link>
            </div>
          ) : (
            <div style={s.grid}>
              {myProperties.map(p => <PropertyCard key={p.id || p._id} property={p} />)}
            </div>
          )
        ) : (
          myInquiries.length === 0 ? (
            <div style={s.empty}><div style={{ fontSize: 48 }}>📩</div><p>No inquiries yet</p></div>
          ) : (
            <div style={s.inquiryList}>
              {myInquiries.map((inq, i) => (
                <div key={i} style={s.inqCard}>
                  <div style={s.inqProp}>Property ID: {inq.property_id}</div>
                  <div style={s.inqMsg}>{inq.message}</div>
                  <div style={s.inqMeta}>
                    <span style={{ ...s.inqStatus, background: inq.status === 'responded' ? '#d1fae5' : '#fef3c7', color: inq.status === 'responded' ? '#065f46' : '#92400e' }}>
                      {inq.status}
                    </span>
                    <span style={{ color: '#9ca3af', fontSize: 12 }}>{new Date(inq.created_at).toLocaleDateString('en-IN')}</span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  )
}

function StatCard({ icon, label, val, color }) {
  return (
    <div style={{ background: '#fff', borderRadius: 14, padding: '20px 24px', border: '1px solid #e5e7eb', flex: 1 }}>
      <div style={{ fontSize: 28, marginBottom: 8 }}>{icon}</div>
      <div style={{ fontSize: 32, fontWeight: 800, color }}>{val}</div>
      <div style={{ fontSize: 14, color: '#6b7280', marginTop: 4 }}>{label}</div>
    </div>
  )
}

const s = {
  page:        { background: '#f9fafb', minHeight: '100vh', paddingBottom: '4rem' },
  wrap:        { maxWidth: 1200, margin: '0 auto', padding: '2rem' },
  header:      { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' },
  h1:          { fontSize: 28, fontWeight: 800, margin: 0, color: '#111827' },
  sub:         { fontSize: 15, color: '#6b7280', marginTop: 4 },
  postBtn:     { background: '#1a56db', color: '#fff', padding: '10px 22px', borderRadius: 10, fontWeight: 700, textDecoration: 'none', fontSize: 14, border: 'none', cursor: 'pointer' },
  statsRow:    { display: 'flex', gap: 20, marginBottom: '2rem' },
  tabs:        { display: 'flex', gap: 4, marginBottom: '1.5rem', borderBottom: '2px solid #e5e7eb', paddingBottom: 0 },
  tab:         { background: 'none', border: 'none', padding: '10px 20px', fontSize: 15, fontWeight: 600, color: '#6b7280', cursor: 'pointer', borderBottom: '3px solid transparent', marginBottom: -2 },
  tabActive:   { color: '#1a56db', borderBottom: '3px solid #1a56db' },
  cnt:         { background: '#dbeafe', color: '#1e40af', borderRadius: 12, padding: '1px 8px', fontSize: 12, marginLeft: 6 },
  loading:     { textAlign: 'center', padding: '4rem', color: '#6b7280' },
  empty:       { textAlign: 'center', padding: '4rem', color: '#9ca3af', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 },
  grid:        { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 },
  inquiryList: { display: 'flex', flexDirection: 'column', gap: 16 },
  inqCard:     { background: '#fff', borderRadius: 12, padding: '18px 20px', border: '1px solid #e5e7eb' },
  inqProp:     { fontSize: 12, color: '#6b7280', marginBottom: 6 },
  inqMsg:      { fontSize: 15, color: '#111827', marginBottom: 10 },
  inqMeta:     { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  inqStatus:   { fontSize: 12, padding: '3px 10px', borderRadius: 12, fontWeight: 600, textTransform: 'capitalize' },
}
