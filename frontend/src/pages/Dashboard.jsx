import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useTimeGreeting } from '../hooks/useTimeGreeting'
import { propertiesAPI, inquiriesAPI } from '../services/api'
import PropertyCard, { PropertyCardSkeleton } from '../components/PropertyCard'

export default function Dashboard() {
  const { user, isLoggedIn } = useAuth()
  const { tr }               = useLang()
  const { isMobile }         = useBreakpoint()
  const greetKey             = useTimeGreeting()
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

  const displayName = user?.first_name || user?.email?.split('@')[0] || 'User'
  const cols = isMobile ? '1fr' : 'repeat(auto-fill,minmax(300px,1fr))'

  const tabs = [
    { key: 'properties', label: tr('myListings'),  count: myProperties.length },
    { key: 'inquiries',  label: tr('myInquiries'), count: myInquiries.length },
  ]

  return (
    <div style={s.page}>
      {/* Banner */}
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <div style={s.greet}>{tr(greetKey)}</div>
            <h1 style={s.h1}>{displayName} 👋</h1>
            <p style={s.sub}>Manage your properties and inquiries</p>
          </div>
          <Link to="/post-property" style={s.postBtn}>{tr('postProperty')}</Link>
        </div>
      </div>

      <div style={s.wrap}>
        {/* Stats */}
        <div style={{ ...s.statsRow, gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(3,1fr)' }}>
          <StatCard icon="🏠" label={tr('myListings')}  val={myProperties.length}  color="#1a56db" bg="#eff6ff" />
          <StatCard icon="📩" label={tr('myInquiries')} val={myInquiries.length}   color="#059669" bg="#f0fdf4" />
          <StatCard icon="👁" label={tr('totalViews')}  val={myProperties.reduce((a,p) => a+(p.view_count||0),0)} color="#7c3aed" bg="#f5f3ff" />
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
          <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 24 }}>
            {Array(4).fill(0).map((_,i) => <PropertyCardSkeleton key={i} />)}
          </div>
        ) : tab === 'properties' ? (
          myProperties.length === 0 ? (
            <div style={s.empty}>
              <div style={{ fontSize: 56 }}>🏠</div>
              <p style={{ fontWeight: 600, fontSize: 18, color: '#0f172a' }}>{tr('noListings')}</p>
              <Link to="/post-property" style={s.postBtn}>{tr('postFirst')}</Link>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 24 }}>
              {myProperties.map(p => <PropertyCard key={p.id || p._id} property={p} />)}
            </div>
          )
        ) : (
          myInquiries.length === 0 ? (
            <div style={s.empty}>
              <div style={{ fontSize: 56 }}>📩</div>
              <p style={{ fontWeight: 600, fontSize: 18, color: '#0f172a' }}>{tr('noInquiries')}</p>
            </div>
          ) : (
            <div style={s.inquiryList}>
              {myInquiries.map((inq, i) => (
                <div key={i} style={s.inqCard} className="fade-in">
                  <div style={s.inqTop}>
                    <span style={s.inqIcon}>📩</span>
                    <div style={s.inqProp}>Property ID: <code>{inq.property_id}</code></div>
                    <span style={{ ...s.inqStatus, background: inq.status === 'responded' ? '#d1fae5' : '#fef3c7', color: inq.status === 'responded' ? '#065f46' : '#92400e' }}>
                      {inq.status || 'pending'}
                    </span>
                  </div>
                  <div style={s.inqMsg}>{inq.message}</div>
                  <div style={s.inqDate}>{inq.created_at ? new Date(inq.created_at).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' }) : ''}</div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  )
}

function StatCard({ icon, label, val, color, bg }) {
  return (
    <div style={{ background: bg, borderRadius: 16, padding: '22px 24px', border: `1px solid ${color}22`, display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ fontSize: 32, width: 52, height: 52, borderRadius: 14, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{icon}</div>
      <div>
        <div style={{ fontSize: 30, fontWeight: 900, color, letterSpacing: '-1px', lineHeight: 1 }}>{val}</div>
        <div style={{ fontSize: 13, color: '#64748b', marginTop: 4, fontWeight: 500 }}>{label}</div>
      </div>
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:      { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '2.5rem 0' },
  bannerInner: { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 },
  greet:       { fontSize: 13, opacity: 0.7, fontWeight: 500, marginBottom: 6 },
  h1:          { fontSize: 'clamp(22px,4vw,32px)', fontWeight: 900, margin: 0, letterSpacing: '-0.5px' },
  sub:         { fontSize: 14, opacity: 0.75, marginTop: 4 },
  postBtn:     { background: '#fff', color: '#1a56db', padding: '11px 22px', borderRadius: 12, fontWeight: 700, textDecoration: 'none', fontSize: 14, border: 'none', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', whiteSpace: 'nowrap' },
  wrap:        { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  statsRow:    { display: 'grid', gap: 16, marginBottom: '2rem' },
  tabs:        { display: 'flex', gap: 4, marginBottom: '1.5rem', borderBottom: '2px solid #e2e8f0' },
  tab:         { background: 'none', border: 'none', padding: '10px 20px', fontSize: 15, fontWeight: 600, color: '#64748b', cursor: 'pointer', borderBottom: '3px solid transparent', marginBottom: -2 },
  tabActive:   { color: '#1a56db', borderBottom: '3px solid #1a56db' },
  cnt:         { background: '#dbeafe', color: '#1e40af', borderRadius: 12, padding: '1px 8px', fontSize: 12, marginLeft: 6 },
  empty:       { textAlign: 'center', padding: '5rem 2rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, background: '#fff', borderRadius: 18, border: '1px solid #e2e8f0' },
  inquiryList: { display: 'flex', flexDirection: 'column', gap: 12 },
  inqCard:     { background: '#fff', borderRadius: 14, padding: '18px 20px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  inqTop:      { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' },
  inqIcon:     { fontSize: 18 },
  inqProp:     { fontSize: 13, color: '#64748b', flex: 1 },
  inqMsg:      { fontSize: 15, color: '#0f172a', marginBottom: 8, lineHeight: 1.5 },
  inqDate:     { fontSize: 12, color: '#94a3b8' },
  inqStatus:   { fontSize: 12, padding: '3px 12px', borderRadius: 20, fontWeight: 700, textTransform: 'capitalize' },
}
