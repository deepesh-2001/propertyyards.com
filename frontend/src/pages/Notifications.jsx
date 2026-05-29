import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const NOTIFS = [
  { id:1,  type:'inquiry',  icon:'📩', title:'New Inquiry on your 3BHK listing',            body:'Rajesh Kumar is interested in your Sector 45 property. Reply now.',   time:'2 min ago',  read:false, channel:'in-app' },
  { id:2,  type:'price',    icon:'📈', title:'Price Alert — Gurgaon prices up 3%',           body:'Average prices in Sector 55-56 rose ₹450/sqft this week.',            time:'1 hr ago',   read:false, channel:'whatsapp' },
  { id:3,  type:'match',    icon:'🏠', title:'New match for your search criteria',            body:'2 new 3BHK properties found in Gurgaon under ₹1.5 Cr.',               time:'3 hr ago',   read:false, channel:'email' },
  { id:4,  type:'payment',  icon:'💳', title:'Payment successful — Premium Listing',         body:'Your listing has been upgraded to premium. Expires Jun 15, 2025.',      time:'5 hr ago',   read:true,  channel:'email' },
  { id:5,  type:'crm',      icon:'📋', title:'Lead "Amit Verma" moved to Qualified',         body:'Your CRM lead has been auto-qualified based on activity score 91.',    time:'Yesterday',  read:true,  channel:'in-app' },
  { id:6,  type:'alert',    icon:'⚠️', title:'Listing about to expire in 3 days',            body:'Your 3BHK Gurgaon listing expires on June 1. Renew now.',              time:'Yesterday',  read:true,  channel:'whatsapp' },
  { id:7,  type:'referral', icon:'🎁', title:'Referral bonus credited — ₹500',               body:'Priya Singh signed up with your code PROP-DEEPESH-2025.',              time:'2 days ago', read:true,  channel:'in-app' },
  { id:8,  type:'system',   icon:'⚙️', title:'WhatsApp notifications re-enabled',            body:'Your WhatsApp integration has been restored after maintenance.',       time:'3 days ago', read:true,  channel:'in-app' },
]

const CHANNELS = ['All','In-App','WhatsApp','Email']
const CHANNEL_ICON = { 'in-app':'💬', 'whatsapp':'💚', 'email':'📧' }

const PREFS = [
  { key:'price_alerts',    label:'Price Alerts',             sub:'When property prices change in your saved areas',  whatsapp:true,  email:true,  inapp:true  },
  { key:'new_matches',     label:'New Property Matches',     sub:'When new listings match your search criteria',      whatsapp:true,  email:true,  inapp:true  },
  { key:'inquiries',       label:'Inquiry Responses',        sub:'When someone responds to your inquiry',             whatsapp:true,  email:true,  inapp:true  },
  { key:'crm_updates',     label:'CRM Lead Updates',         sub:'When lead status changes in your pipeline',         whatsapp:false, email:true,  inapp:true  },
  { key:'payment_alerts',  label:'Payment Confirmations',    sub:'Transaction and invoice notifications',             whatsapp:false, email:true,  inapp:true  },
  { key:'listing_expiry',  label:'Listing Expiry Reminders', sub:'3 days before your listing expires',                whatsapp:true,  email:true,  inapp:true  },
  { key:'market_reports',  label:'Weekly Market Reports',    sub:'Sunday digest of market trends',                    whatsapp:false, email:true,  inapp:false },
  { key:'ai_insights',     label:'AI Insights',              sub:'AI-generated property insights and tips',           whatsapp:false, email:false, inapp:true  },
]

export default function Notifications() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()
  const [notifs, setNotifs]   = useState(NOTIFS)
  const [filter, setFilter]   = useState('All')
  const [tab,    setTab]       = useState('inbox')
  const [prefs,  setPrefs]     = useState(PREFS)

  const filtered = notifs.filter(n =>
    filter === 'All' ||
    (filter === 'In-App' && n.channel === 'in-app') ||
    (filter === 'WhatsApp' && n.channel === 'whatsapp') ||
    (filter === 'Email' && n.channel === 'email')
  )
  const unread = notifs.filter(n => !n.read).length

  const markAll = () => {
    setNotifs(prev => prev.map(n => ({ ...n, read:true })))
    toast('All notifications marked as read', 'success')
  }

  const markRead = (id) => setNotifs(prev => prev.map(n => n.id===id ? { ...n, read:true } : n))

  const togglePref = (key, channel) => {
    setPrefs(prev => prev.map(p => p.key===key ? { ...p, [channel]: !p[channel] } : p))
  }

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>🔔 Notification Center</h1>
            <p style={s.sub}>In-app · WhatsApp · Email · Manage all your alerts in one place</p>
          </div>
          {unread > 0 && (
            <div style={s.unreadBadge}>{unread} unread</div>
          )}
        </div>
      </div>

      <div style={s.wrap}>
        {/* Tabs */}
        <div style={s.tabRow}>
          {[['inbox','📥 Inbox'],['preferences','⚙️ Preferences'],['whatsapp','💚 WhatsApp'],['email','📧 Email Setup']].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              style={{ ...s.tab, ...(tab===id ? s.tabActive : {}) }}>{label}</button>
          ))}
        </div>

        {/* INBOX */}
        {tab === 'inbox' && (
          <div style={s.card}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16, flexWrap:'wrap', gap:10 }}>
              <div style={{ display:'flex', gap:8 }}>
                {CHANNELS.map(c => (
                  <button key={c} onClick={() => setFilter(c)}
                    style={{ ...s.filterBtn, ...(filter===c ? s.filterActive : {}) }}>{c}</button>
                ))}
              </div>
              {unread > 0 && (
                <button onClick={markAll} style={s.markBtn}>✓ Mark all read</button>
              )}
            </div>

            {filtered.length === 0 ? (
              <div style={s.empty}><div style={{ fontSize:48 }}>🔕</div><p>No notifications</p></div>
            ) : (
              filtered.map(n => (
                <div key={n.id} onClick={() => markRead(n.id)}
                  style={{ ...s.notifRow, background: n.read ? 'transparent' : '#eff6ff', borderLeft: n.read ? '4px solid transparent' : '4px solid #1a56db' }}>
                  <div style={s.notifIcon}>{n.icon}</div>
                  <div style={{ flex:1 }}>
                    <div style={{ display:'flex', justifyContent:'space-between', gap:8, flexWrap:'wrap' }}>
                      <span style={{ fontSize:14, fontWeight: n.read ? 600 : 800, color:'#0f172a' }}>{n.title}</span>
                      <div style={{ display:'flex', gap:6, alignItems:'center' }}>
                        <span style={s.channelChip}>{CHANNEL_ICON[n.channel]} {n.channel}</span>
                        <span style={{ fontSize:11, color:'#94a3b8', whiteSpace:'nowrap' }}>{n.time}</span>
                      </div>
                    </div>
                    <div style={{ fontSize:13, color:'#64748b', marginTop:3, lineHeight:1.5 }}>{n.body}</div>
                  </div>
                  {!n.read && <div style={s.unreadDot} />}
                </div>
              ))
            )}
          </div>
        )}

        {/* PREFERENCES */}
        {tab === 'preferences' && (
          <div style={s.card}>
            <h3 style={s.cardTitle}>Notification Preferences</h3>
            <div style={{ overflowX:'auto' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', minWidth:500 }}>
                <thead>
                  <tr style={{ background:'#f8fafc' }}>
                    <th style={{ ...s.th, textAlign:'left' }}>Alert Type</th>
                    <th style={s.th}>💚 WhatsApp</th>
                    <th style={s.th}>📧 Email</th>
                    <th style={s.th}>💬 In-App</th>
                  </tr>
                </thead>
                <tbody>
                  {prefs.map(p => (
                    <tr key={p.key}>
                      <td style={{ padding:'14px 10px', borderBottom:'1px solid #f1f5f9' }}>
                        <div style={{ fontSize:14, fontWeight:700, color:'#0f172a' }}>{p.label}</div>
                        <div style={{ fontSize:12, color:'#94a3b8', marginTop:2 }}>{p.sub}</div>
                      </td>
                      {['whatsapp','email','inapp'].map(ch => (
                        <td key={ch} style={{ padding:'14px 10px', textAlign:'center', borderBottom:'1px solid #f1f5f9' }}>
                          <button onClick={() => togglePref(p.key, ch)}
                            style={{ ...s.toggle, background: p[ch] ? '#059669' : '#e2e8f0' }}>
                            <div style={{ ...s.toggleThumb, transform: p[ch] ? 'translateX(20px)' : 'translateX(2px)' }} />
                          </button>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button onClick={() => toast('Preferences saved!','success')} style={s.saveBtn}>💾 Save Preferences</button>
          </div>
        )}

        {/* WHATSAPP SETUP */}
        {tab === 'whatsapp' && (
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap:24 }}>
            <div style={s.card}>
              <div style={{ fontSize:48, textAlign:'center', marginBottom:16 }}>💚</div>
              <h3 style={{ ...s.cardTitle, textAlign:'center' }}>Connect WhatsApp</h3>
              <p style={{ fontSize:14, color:'#64748b', textAlign:'center', lineHeight:1.7, marginBottom:20 }}>
                Get instant property alerts, inquiry notifications and CRM updates directly on WhatsApp.
              </p>
              <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                <input placeholder="+91 98XXXXXXXX" style={s.input} type="tel" />
                <button onClick={() => toast('OTP sent to your WhatsApp!','success')} style={s.saveBtn}>
                  📲 Send Verification OTP
                </button>
              </div>
            </div>
            <div style={s.card}>
              <h3 style={s.cardTitle}>WhatsApp Alert Types</h3>
              {['New inquiry received','Price drop on saved property','New property matching saved search','Listing expiry reminder','Payment confirmation','Lead status update in CRM'].map(item => (
                <div key={item} style={{ display:'flex', alignItems:'center', gap:10, padding:'9px 0', borderBottom:'1px solid #f1f5f9', fontSize:14, color:'#374151' }}>
                  <span style={{ color:'#059669', fontWeight:700 }}>✓</span> {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* EMAIL SETUP */}
        {tab === 'email' && (
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap:24 }}>
            <div style={s.card}>
              <h3 style={s.cardTitle}>📧 Email Preferences</h3>
              <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                <div>
                  <label style={s.label}>Primary Email</label>
                  <input defaultValue="deepesh@email.com" style={s.input} type="email" />
                </div>
                <div>
                  <label style={s.label}>Email Frequency</label>
                  <select style={s.input}>
                    <option>Immediately</option>
                    <option>Hourly digest</option>
                    <option>Daily digest</option>
                    <option>Weekly digest</option>
                  </select>
                </div>
                <div>
                  <label style={s.label}>Email Format</label>
                  <select style={s.input}>
                    <option>Rich HTML (recommended)</option>
                    <option>Plain text</option>
                  </select>
                </div>
                <button onClick={() => toast('Email settings saved!','success')} style={s.saveBtn}>Save Email Settings</button>
              </div>
            </div>
            <div style={s.card}>
              <h3 style={s.cardTitle}>📨 Email Templates Preview</h3>
              {['Weekly Market Report','New Property Alert','Inquiry Response','Payment Invoice','Lead Status Update'].map(t => (
                <div key={t} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'10px 0', borderBottom:'1px solid #f1f5f9' }}>
                  <span style={{ fontSize:14, color:'#374151' }}>📄 {t}</span>
                  <button onClick={() => toast(`Previewing ${t}...`,'info')} style={{ background:'#eff6ff', color:'#1a56db', border:'none', borderRadius:8, padding:'5px 12px', fontSize:12, fontWeight:700, cursor:'pointer' }}>
                    Preview
                  </button>
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
  bannerInner: { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:12 },
  h1:          { fontSize:'clamp(20px,3vw,28px)', fontWeight:900, margin:0 },
  sub:         { fontSize:13, opacity:0.75, marginTop:4 },
  unreadBadge: { background:'#ef4444', color:'#fff', borderRadius:20, padding:'6px 16px', fontSize:14, fontWeight:800 },
  wrap:        { maxWidth:1240, margin:'0 auto', padding:'2rem 1.5rem' },
  tabRow:      { display:'flex', gap:4, marginBottom:20, flexWrap:'wrap' },
  tab:         { background:'#fff', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'9px 16px', fontSize:13, fontWeight:600, cursor:'pointer', color:'#64748b', transition:'all 0.15s' },
  tabActive:   { background:'#eff6ff', border:'1.5px solid #1a56db', color:'#1a56db', fontWeight:800 },
  card:        { background:'#fff', borderRadius:18, padding:'22px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:   { fontSize:17, fontWeight:800, color:'#0f172a', margin:'0 0 16px' },
  filterBtn:   { background:'#f1f5f9', border:'1px solid #e2e8f0', borderRadius:20, padding:'5px 14px', fontSize:12, fontWeight:600, cursor:'pointer', color:'#374151' },
  filterActive:{ background:'#eff6ff', border:'1px solid #1a56db', color:'#1a56db' },
  markBtn:     { background:'#f0fdf4', color:'#059669', border:'1px solid #bbf7d0', borderRadius:10, padding:'7px 14px', fontSize:13, fontWeight:700, cursor:'pointer' },
  notifRow:    { display:'flex', gap:14, alignItems:'flex-start', padding:'14px 12px', borderRadius:12, marginBottom:4, cursor:'pointer', transition:'background 0.1s' },
  notifIcon:   { fontSize:24, flexShrink:0, marginTop:2 },
  channelChip: { fontSize:11, fontWeight:700, background:'#f1f5f9', borderRadius:20, padding:'2px 8px', color:'#374151' },
  unreadDot:   { width:8, height:8, borderRadius:'50%', background:'#1a56db', flexShrink:0, marginTop:6 },
  empty:       { textAlign:'center', padding:'3rem', color:'#94a3b8' },
  th:          { padding:'10px 12px', fontSize:12, fontWeight:800, color:'#64748b', textTransform:'uppercase', letterSpacing:0.5, borderBottom:'2px solid #e2e8f0', textAlign:'center' },
  toggle:      { width:44, height:24, borderRadius:99, border:'none', cursor:'pointer', position:'relative', transition:'background 0.2s', flexShrink:0 },
  toggleThumb: { position:'absolute', top:3, width:18, height:18, borderRadius:'50%', background:'#fff', boxShadow:'0 1px 4px rgba(0,0,0,0.2)', transition:'transform 0.2s' },
  saveBtn:     { background:'linear-gradient(135deg,#1a56db,#2563eb)', color:'#fff', border:'none', borderRadius:12, padding:'12px', fontSize:14, fontWeight:800, cursor:'pointer', width:'100%', marginTop:8 },
  input:       { border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 14px', fontSize:14, outline:'none', fontFamily:'inherit', width:'100%', boxSizing:'border-box', background:'#fafafa' },
  label:       { fontSize:13, fontWeight:700, color:'#374151', display:'block', marginBottom:6 },
}
