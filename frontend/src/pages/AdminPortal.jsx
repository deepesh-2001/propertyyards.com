import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const TABS = [
  { id: 'overview',  icon: '📊', label: 'Overview' },
  { id: 'users',     icon: '👥', label: 'Users' },
  { id: 'listings',  icon: '🏠', label: 'Listings' },
  { id: 'flags',     icon: '🚩', label: 'Feature Flags' },
  { id: 'reports',   icon: '📄', label: 'Reports' },
  { id: 'system',    icon: '⚙️', label: 'System Health' },
]

const USERS = [
  { id: 1, name: 'Rajesh Kumar',  email: 'rajesh@email.com', role: 'buyer',  status: 'active',   joined: '2025-03-12', properties: 0 },
  { id: 2, name: 'Amit Broker',   email: 'amit@email.com',   role: 'broker', status: 'active',   joined: '2025-01-05', properties: 14 },
  { id: 3, name: 'Sunita Patel',  email: 'sunita@email.com', role: 'seller', status: 'active',   joined: '2025-02-18', properties: 3 },
  { id: 4, name: 'Deepak Sharma', email: 'deepak@email.com', role: 'admin',  status: 'active',   joined: '2024-11-01', properties: 0 },
  { id: 5, name: 'Priya Joshi',   email: 'priya@email.com',  role: 'buyer',  status: 'inactive', joined: '2025-04-22', properties: 0 },
  { id: 6, name: 'Vikram Nair',   email: 'vikram@email.com', role: 'broker', status: 'pending',  joined: '2025-05-28', properties: 0 },
]

const LISTINGS_DATA = [
  { id: 'p1', title: '3BHK Godrej Horizon',  city: 'Gurgaon',   price: '1.8 Cr',  status: 'active',  owner: 'Amit Broker',  views: 4821 },
  { id: 'p2', title: 'DLF Penthouse 5BHK',   city: 'Gurgaon',   price: '12 Cr',   status: 'active',  owner: 'Sunita Patel', views: 3940 },
  { id: 'p3', title: '2BHK Prestige Lake',   city: 'Bangalore', price: '95 L',    status: 'pending', owner: 'Amit Broker',  views: 0 },
  { id: 'p4', title: '4BHK Villa Sea View',  city: 'Mumbai',    price: '4.2 Cr',  status: 'active',  owner: 'Sunita Patel', views: 2864 },
  { id: 'p5', title: 'Commercial Complex',   city: 'Noida',     price: '8.5 Cr',  status: 'flagged', owner: 'Unknown',      views: 412 },
]

const FEATURE_FLAGS = [
  { key: 'user_registration',    label: 'User Registration',       enabled: true,  env: 'all' },
  { key: 'ai_descriptions',      label: 'AI Descriptions',         enabled: true,  env: 'all' },
  { key: 'property_3d_models',   label: '3D Model Generation',     enabled: true,  env: 'all' },
  { key: 'ai_price_prediction',  label: 'AI Price Prediction',     enabled: true,  env: 'all' },
  { key: 'whatsapp_alerts',      label: 'WhatsApp Notifications',  enabled: false, env: 'prod' },
  { key: 'payment_gateway',      label: 'Payment Gateway',         enabled: false, env: 'prod' },
  { key: 'live_chat',            label: 'Live Chat Widget',        enabled: true,  env: 'all' },
  { key: 'fraud_detection',      label: 'Fraud Detection',         enabled: true,  env: 'all' },
  { key: 'auto_healing',         label: 'Auto-Healing Service',    enabled: true,  env: 'prod' },
  { key: 'cashback_rewards',     label: 'Cashback & Rewards',      enabled: false, env: 'staging' },
  { key: 'broker_verification',  label: 'RERA Broker Verification',enabled: true,  env: 'all' },
  { key: 'seo_optimizer',        label: 'SEO Auto-Optimizer',      enabled: true,  env: 'all' },
]

const SYSTEM_HEALTH = [
  { service: 'API Gateway',      status: 'healthy', uptime: '99.98%', latency: '42ms',  icon: '🌐' },
  { service: 'MongoDB Atlas',    status: 'healthy', uptime: '99.99%', latency: '18ms',  icon: '🗄' },
  { service: 'Redis Cache',      status: 'healthy', uptime: '100%',   latency: '3ms',   icon: '⚡' },
  { service: 'AI Image Service', status: 'healthy', uptime: '99.7%',  latency: '1.8s',  icon: '🖼' },
  { service: 'Email Service',    status: 'warning', uptime: '98.2%',  latency: '220ms', icon: '✉️' },
  { service: 'WhatsApp Bot',     status: 'down',    uptime: '92.1%',  latency: 'N/A',   icon: '💬' },
  { service: 'Fraud Detection',  status: 'healthy', uptime: '99.9%',  latency: '55ms',  icon: '🛡' },
  { service: 'Background Tasks', status: 'healthy', uptime: '99.8%',  latency: '—',     icon: '⚙️' },
]

const STATUS_COLORS = { active:'#059669', inactive:'#94a3b8', pending:'#f59e0b', flagged:'#dc2626', healthy:'#059669', warning:'#f59e0b', down:'#dc2626' }

export default function AdminPortal() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()
  const [tab,   setTab]   = useState('overview')
  const [flags, setFlags] = useState(FEATURE_FLAGS)
  const [users, setUsers] = useState(USERS)

  const toggleFlag = (key) => {
    setFlags(prev => prev.map(f => f.key === key ? { ...f, enabled: !f.enabled } : f))
    const flag = flags.find(f => f.key === key)
    toast(`${flag.label} ${flag.enabled ? 'disabled' : 'enabled'}`, 'success')
  }

  const updateUserStatus = (id, status) => {
    setUsers(prev => prev.map(u => u.id === id ? { ...u, status } : u))
    toast(`User status updated to ${status}`, 'success')
  }

  const overview = {
    totalUsers: users.length, activeUsers: users.filter(u=>u.status==='active').length,
    totalListings: LISTINGS_DATA.length, activeListings: LISTINGS_DATA.filter(l=>l.status==='active').length,
    flaggedListings: LISTINGS_DATA.filter(l=>l.status==='flagged').length,
    enabledFlags: flags.filter(f=>f.enabled).length,
  }

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <h1 style={s.h1}>⚙️ Admin Portal</h1>
          <p style={s.sub}>Manage users, listings, features and system health</p>
        </div>
      </div>

      {/* Tabs */}
      <div style={s.tabBar}>
        <div style={s.tabInner}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{ ...s.tab, ...(tab === t.id ? s.tabActive : {}) }}>
              {t.icon} {!isMobile && t.label}
            </button>
          ))}
        </div>
      </div>

      <div style={s.wrap}>
        {/* Overview */}
        {tab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(3,1fr)', gap: 16 }}>
              {[
                { icon:'👥', label:'Total Users',       val: overview.totalUsers,      sub:`${overview.activeUsers} active`,      color:'#1a56db' },
                { icon:'🏠', label:'Listings',          val: overview.totalListings,   sub:`${overview.activeListings} active`,   color:'#059669' },
                { icon:'⚠️', label:'Flagged Listings',  val: overview.flaggedListings, sub:'Needs review',                        color:'#dc2626' },
                { icon:'🚩', label:'Feature Flags ON',  val: overview.enabledFlags,    sub:`of ${flags.length} total`,            color:'#7c3aed' },
                { icon:'💚', label:'System Services',   val: SYSTEM_HEALTH.filter(s=>s.status==='healthy').length, sub:'Healthy', color:'#059669' },
                { icon:'⚡', label:'Redis Hit Rate',     val: '94.2%',                  sub:'Cache efficiency',                    color:'#f59e0b' },
              ].map(k => (
                <div key={k.label} style={{ background:'#fff', borderRadius:16, padding:'20px', border:'1px solid #e2e8f0', borderTop:`4px solid ${k.color}` }}>
                  <span style={{ fontSize:24 }}>{k.icon}</span>
                  <div style={{ fontSize:28, fontWeight:900, color:k.color, letterSpacing:'-0.5px', marginTop:8 }}>{k.val}</div>
                  <div style={{ fontSize:13, fontWeight:700, color:'#0f172a', marginTop:2 }}>{k.label}</div>
                  <div style={{ fontSize:11, color:'#94a3b8', marginTop:2 }}>{k.sub}</div>
                </div>
              ))}
            </div>
            <div style={s.card}>
              <h3 style={s.cardTitle}>🕒 Recent Activity</h3>
              {[
                { time:'2min ago',  action:'New user registered: vikram@email.com', type:'user' },
                { time:'8min ago',  action:'Listing flagged for review: Commercial Complex, Noida', type:'warn' },
                { time:'15min ago', action:'Feature flag "ai_descriptions" enabled by admin', type:'flag' },
                { time:'1hr ago',   action:'WhatsApp service went down. Auto-healing triggered.', type:'error' },
                { time:'2hr ago',   action:'842 new leads generated from Paid Ads campaign', type:'lead' },
                { time:'3hr ago',   action:'MongoDB Atlas: 99.99% uptime checkpoint passed', type:'ok' },
              ].map((a, i) => (
                <div key={i} style={s.actRow}>
                  <span style={{ fontSize:20 }}>{a.type==='error'?'🔴':a.type==='warn'?'🟡':a.type==='flag'?'🚩':a.type==='lead'?'📈':'🟢'}</span>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:14, color:'#0f172a' }}>{a.action}</div>
                    <div style={{ fontSize:12, color:'#94a3b8', marginTop:2 }}>{a.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Users */}
        {tab === 'users' && (
          <div style={{ overflowX:'auto' }}>
            <table style={s.table}>
              <thead>
                <tr style={{ background:'#f8fafc' }}>
                  {['User','Email','Role','Status','Joined','Properties','Actions'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={u.id} style={i%2===0?{}:{background:'#fafafa'}}>
                    <td style={s.td}><strong>{u.name}</strong></td>
                    <td style={s.td}>{u.email}</td>
                    <td style={s.td}><span style={{ ...s.chip, background:'#eff6ff', color:'#1d4ed8' }}>{u.role}</span></td>
                    <td style={s.td}><span style={{ ...s.chip, background:`${STATUS_COLORS[u.status]}18`, color:STATUS_COLORS[u.status] }}>{u.status}</span></td>
                    <td style={s.td}>{u.joined}</td>
                    <td style={s.td}>{u.properties}</td>
                    <td style={s.td}>
                      <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
                        {u.status !== 'active' && <button onClick={() => updateUserStatus(u.id,'active')} style={s.aBtn}>✅ Approve</button>}
                        {u.status === 'active' && <button onClick={() => updateUserStatus(u.id,'inactive')} style={{ ...s.aBtn, background:'#fee2e2', color:'#dc2626' }}>🚫 Suspend</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Listings */}
        {tab === 'listings' && (
          <div style={{ overflowX:'auto' }}>
            <table style={s.table}>
              <thead>
                <tr style={{ background:'#f8fafc' }}>
                  {['Title','City','Price','Owner','Status','Views','Actions'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {LISTINGS_DATA.map((l, i) => (
                  <tr key={l.id} style={i%2===0?{}:{background:'#fafafa'}}>
                    <td style={s.td}><strong>{l.title}</strong></td>
                    <td style={s.td}>{l.city}</td>
                    <td style={s.td}><span style={{ fontWeight:800, color:'#1a56db' }}>{l.price}</span></td>
                    <td style={s.td}>{l.owner}</td>
                    <td style={s.td}><span style={{ ...s.chip, background:`${STATUS_COLORS[l.status]}18`, color:STATUS_COLORS[l.status] }}>{l.status}</span></td>
                    <td style={s.td}>{l.views.toLocaleString()}</td>
                    <td style={s.td}>
                      <div style={{ display:'flex', gap:6 }}>
                        <button onClick={() => toast(`Listing ${l.id} approved`,'success')} style={s.aBtn}>✅ Approve</button>
                        <button onClick={() => toast(`Listing ${l.id} removed`,'error')} style={{ ...s.aBtn, background:'#fee2e2', color:'#dc2626' }}>🗑 Remove</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Feature Flags */}
        {tab === 'flags' && (
          <div style={s.card}>
            <h3 style={s.cardTitle}>🚩 Feature Flags — feature_flags.py</h3>
            <div style={{ display:'flex', flexDirection:'column', gap:0 }}>
              {flags.map((f, i) => (
                <div key={f.key} style={{ ...s.flagRow, borderBottom: i < flags.length-1 ? '1px solid #f1f5f9' : 'none' }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:15, fontWeight:700, color:'#0f172a' }}>{f.label}</div>
                    <div style={{ fontSize:12, color:'#94a3b8', marginTop:2, fontFamily:'monospace' }}>{f.key} · {f.env}</div>
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <span style={{ fontSize:12, fontWeight:700, color: f.enabled ? '#059669' : '#94a3b8' }}>
                      {f.enabled ? '✅ Enabled' : '⚫ Disabled'}
                    </span>
                    <button onClick={() => toggleFlag(f.key)} style={{ ...s.toggle, background: f.enabled ? '#059669' : '#e2e8f0' }}>
                      <div style={{ ...s.toggleThumb, transform: f.enabled ? 'translateX(20px)' : 'translateX(2px)' }} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reports */}
        {tab === 'reports' && (
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)', gap:20 }}>
            {[
              { icon:'📊', title:'Monthly Analytics Report',  desc:'Traffic, leads, conversions, revenue breakdown', btn:'📥 Download PDF' },
              { icon:'👥', title:'User Growth Report',        desc:'New registrations, churn, role distribution', btn:'📥 Download CSV' },
              { icon:'🏠', title:'Listings Performance',      desc:'Views, inquiries, listing health by city', btn:'📥 Download Excel' },
              { icon:'💰', title:'Revenue & Commission',      desc:'Broker commissions, platform fees, payouts', btn:'📥 Download PDF' },
              { icon:'🚩', title:'Feature Flags Audit',       desc:'All flag changes with timestamps and authors', btn:'📥 Download Log' },
              { icon:'🛡', title:'Fraud Detection Report',    desc:'Suspicious listings, flagged users, blocked IPs', btn:'📥 Download PDF' },
            ].map(r => (
              <div key={r.title} style={s.card}>
                <div style={{ fontSize:32, marginBottom:12 }}>{r.icon}</div>
                <div style={{ fontSize:16, fontWeight:800, color:'#0f172a', marginBottom:6 }}>{r.title}</div>
                <div style={{ fontSize:13, color:'#64748b', marginBottom:16, lineHeight:1.5 }}>{r.desc}</div>
                <button onClick={() => toast(`Generating ${r.title}...`,'info')} style={s.reportBtn}>{r.btn}</button>
              </div>
            ))}
          </div>
        )}

        {/* System Health */}
        {tab === 'system' && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div style={{ display:'grid', gridTemplateColumns: isMobile?'1fr':' repeat(auto-fill,minmax(280px,1fr))', gap:16 }}>
              {SYSTEM_HEALTH.map(svc => (
                <div key={svc.service} style={{ ...s.svcCard, borderLeft:`4px solid ${STATUS_COLORS[svc.status]}` }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
                    <span style={{ fontSize:22 }}>{svc.icon}</span>
                    <span style={{ ...s.chip, background:`${STATUS_COLORS[svc.status]}18`, color:STATUS_COLORS[svc.status] }}>{svc.status}</span>
                  </div>
                  <div style={{ fontSize:15, fontWeight:800, color:'#0f172a', marginBottom:8 }}>{svc.service}</div>
                  <div style={{ display:'flex', gap:16 }}>
                    <div><div style={s.svcLabel}>Uptime</div><div style={s.svcVal}>{svc.uptime}</div></div>
                    <div><div style={s.svcLabel}>Latency</div><div style={s.svcVal}>{svc.latency}</div></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const s = {
  page:        { background:'#f8fafc', minHeight:'100vh', paddingBottom:'4rem' },
  banner:      { background:'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color:'#fff', padding:'2rem 0' },
  bannerInner: { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem' },
  h1:          { fontSize:'clamp(20px,3vw,28px)', fontWeight:900, margin:0 },
  sub:         { fontSize:13, opacity:0.75, marginTop:4 },
  tabBar:      { background:'#fff', borderBottom:'1px solid #e2e8f0', position:'sticky', top:60, zIndex:100, boxShadow:'0 1px 8px rgba(0,0,0,0.04)' },
  tabInner:    { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem', display:'flex', gap:2, overflowX:'auto' },
  tab:         { background:'none', border:'none', padding:'14px 16px', fontSize:14, fontWeight:600, color:'#64748b', cursor:'pointer', borderBottom:'3px solid transparent', whiteSpace:'nowrap', transition:'all 0.15s' },
  tabActive:   { color:'#1a56db', borderBottom:'3px solid #1a56db', fontWeight:800 },
  wrap:        { maxWidth:1240, margin:'0 auto', padding:'2rem 1.5rem' },
  card:        { background:'#fff', borderRadius:18, padding:'24px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:   { fontSize:18, fontWeight:800, color:'#0f172a', margin:'0 0 18px' },
  actRow:      { display:'flex', gap:12, alignItems:'flex-start', padding:'12px 0', borderBottom:'1px solid #f1f5f9' },
  table:       { width:'100%', borderCollapse:'collapse', background:'#fff', borderRadius:16, overflow:'hidden', border:'1px solid #e2e8f0', boxShadow:'0 1px 8px rgba(0,0,0,0.05)', minWidth:700 },
  th:          { padding:'12px 14px', textAlign:'left', fontSize:12, fontWeight:800, color:'#64748b', textTransform:'uppercase', letterSpacing:0.5, borderBottom:'2px solid #e2e8f0', whiteSpace:'nowrap' },
  td:          { padding:'13px 14px', fontSize:14, color:'#0f172a', borderBottom:'1px solid #f1f5f9', verticalAlign:'middle' },
  chip:        { borderRadius:20, padding:'3px 12px', fontSize:12, fontWeight:700 },
  aBtn:        { background:'#d1fae5', color:'#065f46', border:'none', borderRadius:8, padding:'5px 10px', fontSize:12, fontWeight:700, cursor:'pointer', whiteSpace:'nowrap' },
  flagRow:     { display:'flex', alignItems:'center', gap:16, padding:'16px 0' },
  toggle:      { width:44, height:24, borderRadius:99, border:'none', cursor:'pointer', position:'relative', transition:'background 0.2s', flexShrink:0 },
  toggleThumb: { position:'absolute', top:3, width:18, height:18, borderRadius:'50%', background:'#fff', boxShadow:'0 1px 4px rgba(0,0,0,0.2)', transition:'transform 0.2s' },
  reportBtn:   { background:'#eff6ff', color:'#1a56db', border:'1px solid #bfdbfe', borderRadius:10, padding:'10px 16px', fontSize:13, fontWeight:700, cursor:'pointer', width:'100%' },
  svcCard:     { background:'#fff', borderRadius:14, padding:'18px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  svcLabel:    { fontSize:11, color:'#94a3b8', fontWeight:700, textTransform:'uppercase', letterSpacing:0.5, marginBottom:2 },
  svcVal:      { fontSize:15, fontWeight:800, color:'#0f172a' },
}
