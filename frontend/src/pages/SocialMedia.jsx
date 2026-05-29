import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const PLATFORMS = [
  { id:'instagram', label:'Instagram',  icon:'📸', color:'#E1306C', followers:'12.4K' },
  { id:'facebook',  label:'Facebook',   icon:'👥', color:'#1877F2', followers:'8.2K' },
  { id:'twitter',   label:'Twitter/X',  icon:'🐦', color:'#1DA1F2', followers:'5.6K' },
  { id:'linkedin',  label:'LinkedIn',   icon:'💼', color:'#0A66C2', followers:'3.1K' },
  { id:'youtube',   label:'YouTube',    icon:'▶️', color:'#FF0000', followers:'1.8K' },
]

const SCHEDULED = [
  { id:1, platform:'instagram', content:'🏠 Luxury 3BHK in Gurgaon Sector 45 — ₹1.8 Cr. DM for site visit! #PropertyYards #Gurgaon #LuxuryHomes', time:'2025-05-30 10:00', img:'https://picsum.photos/seed/post1/400/300', status:'scheduled' },
  { id:2, platform:'facebook',  content:'🔑 New listing alert! 2BHK in Noida Sector 62 @ ₹75L. RERA verified. Call +91 98100-XXXXX', time:'2025-05-30 14:00', img:'https://picsum.photos/seed/post2/400/300', status:'scheduled' },
  { id:3, platform:'linkedin',  content:'Market Update: Gurgaon property prices rose 14.2% YoY. Premium locations seeing highest demand from tech professionals.', time:'2025-05-31 09:00', img:null, status:'scheduled' },
  { id:4, platform:'instagram', content:'Virtual tour of this stunning penthouse with city views 🌃 Swipe to see more! Link in bio.', time:'2025-05-28 10:00', img:'https://picsum.photos/seed/post4/400/300', status:'published' },
]

const TEMPLATES = [
  { id:'new_listing',  label:'New Listing Announcement', emoji:'🏠', preview:'Just listed! {bedrooms}BHK in {city} @ ₹{price}. RERA verified. DM for site visit! #{city}RealEstate #PropertyYards' },
  { id:'price_drop',   label:'Price Drop Alert',         emoji:'📉', preview:'🔥 Price reduced! {property_name} now at ₹{new_price} (was ₹{old_price}). Limited time offer. Act fast!' },
  { id:'sold',         label:'Property Sold',            emoji:'🎉', preview:'SOLD! 🎊 Congratulations to our client on the purchase of {property_name}. Another happy family finds their dream home!' },
  { id:'market_update',label:'Weekly Market Update',     emoji:'📊', preview:'This week in {city}: Avg prices at ₹{price}/sqft (+{change}% WoW). {listings} new listings. Call us for free property advice!' },
  { id:'open_house',   label:'Open House Invitation',    emoji:'🚪', preview:'You\'re invited! Open House at {property_name} this {day}. Free site visit, complimentary consultation. RSVP now!' },
]

const ANALYTICS = [
  { platform:'instagram', reach:14200, engagement:'4.8%', clicks:342, leads:18 },
  { platform:'facebook',  reach:9800,  engagement:'3.2%', clicks:218, leads:12 },
  { platform:'linkedin',  reach:5400,  engagement:'6.1%', clicks:187, leads:21 },
  { platform:'twitter',   reach:3200,  engagement:'2.1%', clicks:98,  leads:5 },
]

const PLATFORM_COLORS = { instagram:'#E1306C', facebook:'#1877F2', twitter:'#1DA1F2', linkedin:'#0A66C2', youtube:'#FF0000' }

export default function SocialMedia() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()
  const [tab, setTab]         = useState('compose')
  const [selected, setSelected] = useState(['instagram','facebook'])
  const [content, setContent]   = useState('')
  const [schedTime, setSchedTime] = useState('')
  const [posts, setPosts]       = useState(SCHEDULED)
  const [vars, setVars]         = useState({ city:'Gurgaon', bedrooms:'3', price:'1.8 Cr' })

  const charCount = content.length
  const charLimit = selected.includes('twitter') ? 280 : 2200

  const toggle = (id) => setSelected(prev => prev.includes(id) ? prev.filter(p=>p!==id) : [...prev, id])

  const publish = (schedule) => {
    if (!content) { toast('Write some content first','error'); return }
    if (!selected.length) { toast('Select at least one platform','error'); return }
    const newPost = {
      id: Date.now(), platform: selected[0], content, time: schedTime || 'Now',
      img: null, status: schedule ? 'scheduled' : 'published'
    }
    setPosts(prev => [newPost, ...prev])
    toast(schedule ? `Post scheduled for ${schedTime}` : 'Post published!', 'success')
    setContent('')
  }

  const applyTemplate = (tmpl) => {
    let text = tmpl.preview
    Object.entries(vars).forEach(([k,v]) => { text = text.replaceAll(`{${k}}`, v) })
    setContent(text)
  }

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <h1 style={s.h1}>📱 Social Media Manager</h1>
          <p style={s.sub}>Schedule posts, track analytics, manage all platforms — powered by social_media_manager.py</p>
        </div>
      </div>

      {/* Platform Stats Bar */}
      <div style={s.statsBar}>
        <div style={s.statsInner}>
          {PLATFORMS.map(p => (
            <div key={p.id} style={s.platformStat}>
              <span style={{ fontSize:20 }}>{p.icon}</span>
              <div>
                <div style={{ fontSize:13, fontWeight:800, color:'#0f172a' }}>{p.label}</div>
                <div style={{ fontSize:12, color:'#64748b' }}>{p.followers} followers</div>
              </div>
              <div style={{ width:10, height:10, borderRadius:'50%', background:'#059669' }} title="Connected" />
            </div>
          ))}
        </div>
      </div>

      <div style={s.wrap}>
        <div style={s.tabRow}>
          {[['compose','✍️ Compose'],['scheduled','📅 Scheduled'],['analytics','📊 Analytics'],['templates','📋 Templates']].map(([id,label]) => (
            <button key={id} onClick={() => setTab(id)}
              style={{ ...s.tab, ...(tab===id ? s.tabActive : {}) }}>{label}</button>
          ))}
        </div>

        {/* COMPOSE */}
        {tab === 'compose' && (
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 360px', gap:24 }}>
            <div style={s.card}>
              <h3 style={s.cardTitle}>Create Post</h3>
              {/* Platform selector */}
              <div style={{ marginBottom:16 }}>
                <div style={s.fieldLabel}>Select Platforms</div>
                <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
                  {PLATFORMS.map(p => (
                    <button key={p.id} onClick={() => toggle(p.id)}
                      style={{ ...s.platBtn, border:`2px solid ${selected.includes(p.id) ? p.color : '#e2e8f0'}`, background: selected.includes(p.id) ? `${p.color}15` : '#fff', color: selected.includes(p.id) ? p.color : '#374151' }}>
                      {p.icon} {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Content */}
              <div style={{ marginBottom:8 }}>
                <div style={s.fieldLabel}>Post Content</div>
                <textarea value={content} onChange={e => setContent(e.target.value)} rows={6} style={s.textarea}
                  placeholder="Write your post... Use AI to generate content from the Templates tab" />
                <div style={{ fontSize:12, color: charCount > charLimit ? '#dc2626' : '#94a3b8', textAlign:'right', marginTop:4 }}>
                  {charCount}/{charLimit} chars
                </div>
              </div>

              {/* Image */}
              <div style={{ marginBottom:16 }}>
                <div style={s.fieldLabel}>Attach Image (optional)</div>
                <div style={s.imgDrop} onClick={() => toast('Image picker would open here','info')}>
                  🖼 Click to upload or drag & drop · Or use AI Image Generator
                </div>
              </div>

              {/* Schedule */}
              <div style={{ marginBottom:20 }}>
                <div style={s.fieldLabel}>Schedule Time (optional)</div>
                <input type="datetime-local" value={schedTime} onChange={e => setSchedTime(e.target.value)} style={s.input} />
              </div>

              <div style={{ display:'flex', gap:12 }}>
                <button onClick={() => publish(false)} style={s.publishBtn}>🚀 Post Now</button>
                <button onClick={() => publish(true)} style={s.scheduleBtn}>📅 Schedule</button>
              </div>
            </div>

            {/* Preview */}
            <div style={s.card}>
              <h3 style={s.cardTitle}>👁 Live Preview</h3>
              {selected.length === 0 ? (
                <div style={s.emptyPreview}>Select a platform to preview</div>
              ) : (
                <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                  {selected.slice(0,2).map(pid => {
                    const plat = PLATFORMS.find(p => p.id===pid)
                    return (
                      <div key={pid} style={s.previewCard}>
                        <div style={{ display:'flex', gap:10, alignItems:'center', marginBottom:10 }}>
                          <span style={{ fontSize:20 }}>{plat.icon}</span>
                          <div>
                            <div style={{ fontWeight:700, fontSize:13, color:'#0f172a' }}>PropertyYards</div>
                            <div style={{ fontSize:11, color:'#94a3b8' }}>Just now · {plat.label}</div>
                          </div>
                        </div>
                        <p style={{ fontSize:13, color:'#374151', lineHeight:1.6, margin:'0 0 10px', wordBreak:'break-word' }}>
                          {content || <span style={{ color:'#94a3b8' }}>Start typing your post...</span>}
                        </p>
                        <div style={{ display:'flex', gap:16, fontSize:12, color:'#94a3b8' }}>
                          <span>❤️ Like</span><span>💬 Comment</span><span>🔗 Share</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* SCHEDULED */}
        {tab === 'scheduled' && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            {posts.map(post => {
              const plat = PLATFORMS.find(p => p.id===post.platform)
              return (
                <div key={post.id} style={{ ...s.card, display:'flex', gap:16, alignItems:'flex-start', flexWrap:'wrap' }}>
                  {post.img && <img src={post.img} alt="post" style={{ width:80, height:80, borderRadius:10, objectFit:'cover', flexShrink:0 }} onError={e=>{e.target.style.display='none'}} />}
                  <div style={{ flex:1, minWidth:200 }}>
                    <div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:8, flexWrap:'wrap' }}>
                      <span style={{ fontSize:18 }}>{plat?.icon}</span>
                      <span style={{ fontWeight:700, fontSize:13, color: PLATFORM_COLORS[post.platform] }}>{plat?.label}</span>
                      <span style={{ ...s.statusChip, background: post.status==='published'?'#d1fae5':'#eff6ff', color: post.status==='published'?'#065f46':'#1a56db' }}>{post.status}</span>
                      <span style={{ fontSize:12, color:'#94a3b8' }}>📅 {post.time}</span>
                    </div>
                    <p style={{ fontSize:14, color:'#374151', margin:0, lineHeight:1.6, display:'-webkit-box', WebkitLineClamp:2, WebkitBoxOrient:'vertical', overflow:'hidden' }}>
                      {post.content}
                    </p>
                  </div>
                  <div style={{ display:'flex', gap:8 }}>
                    <button onClick={() => { setPosts(prev=>prev.filter(p=>p.id!==post.id)); toast('Post deleted','success') }}
                      style={{ background:'#fee2e2', color:'#dc2626', border:'none', borderRadius:8, padding:'6px 12px', fontSize:12, fontWeight:700, cursor:'pointer' }}>
                      🗑 Delete
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* ANALYTICS */}
        {tab === 'analytics' && (
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)', gap:20 }}>
            {ANALYTICS.map(a => {
              const plat = PLATFORMS.find(p => p.id===a.platform)
              return (
                <div key={a.platform} style={{ ...s.card, borderTop:`4px solid ${PLATFORM_COLORS[a.platform]}` }}>
                  <div style={{ display:'flex', gap:10, alignItems:'center', marginBottom:16 }}>
                    <span style={{ fontSize:28 }}>{plat?.icon}</span>
                    <div>
                      <div style={{ fontWeight:800, fontSize:16, color:'#0f172a' }}>{plat?.label}</div>
                      <div style={{ fontSize:12, color:'#64748b' }}>{plat?.followers} followers</div>
                    </div>
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                    {[['👁 Reach', a.reach.toLocaleString()],['💬 Engagement', a.engagement],['🔗 Link Clicks', a.clicks],['📋 Leads', a.leads]].map(([label, val]) => (
                      <div key={label} style={{ background:'#f8fafc', borderRadius:10, padding:'12px' }}>
                        <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, textTransform:'uppercase', letterSpacing:0.5 }}>{label}</div>
                        <div style={{ fontSize:20, fontWeight:900, color:'#0f172a', marginTop:4 }}>{val}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* TEMPLATES */}
        {tab === 'templates' && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div style={{ ...s.card, background:'#fffbeb', border:'1px solid #fcd34d' }}>
              <div style={{ fontSize:13, color:'#78350f' }}>💡 Customize variables, then click <strong>Use Template</strong> to load it into the compose editor.</div>
              <div style={{ display:'flex', gap:12, marginTop:12, flexWrap:'wrap' }}>
                {[['city','City'],['bedrooms','Bedrooms'],['price','Price']].map(([key, label]) => (
                  <div key={key} style={{ display:'flex', gap:6, alignItems:'center' }}>
                    <span style={{ fontSize:12, fontWeight:700, color:'#92400e' }}>{label}:</span>
                    <input value={vars[key]||''} onChange={e => setVars(p=>({...p,[key]:e.target.value}))}
                      style={{ border:'1px solid #fcd34d', borderRadius:8, padding:'4px 10px', fontSize:13, width:100 }} />
                  </div>
                ))}
              </div>
            </div>
            {TEMPLATES.map(t => (
              <div key={t.id} style={s.card}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:10, flexWrap:'wrap', gap:8 }}>
                  <span style={{ fontSize:16, fontWeight:800, color:'#0f172a' }}>{t.emoji} {t.label}</span>
                  <button onClick={() => { applyTemplate(t); setTab('compose'); toast('Template loaded!','success') }} style={s.useBtn}>
                    ✍️ Use Template
                  </button>
                </div>
                <p style={{ fontSize:13, color:'#64748b', margin:0, background:'#f8fafc', borderRadius:10, padding:'12px', lineHeight:1.7, fontFamily:'monospace' }}>
                  {t.preview}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const s = {
  page:        { background:'#f8fafc', minHeight:'100vh', paddingBottom:'4rem' },
  banner:      { background:'linear-gradient(135deg,#E1306C,#833ab4,#405DE6)', color:'#fff', padding:'2rem 0' },
  bannerInner: { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem' },
  h1:          { fontSize:'clamp(20px,3vw,28px)', fontWeight:900, margin:0 },
  sub:         { fontSize:13, opacity:0.85, marginTop:4 },
  statsBar:    { background:'#fff', borderBottom:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  statsInner:  { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem', display:'flex', gap:0, overflowX:'auto' },
  platformStat:{ display:'flex', gap:10, alignItems:'center', padding:'14px 20px', borderRight:'1px solid #f1f5f9', flexShrink:0 },
  wrap:        { maxWidth:1240, margin:'0 auto', padding:'2rem 1.5rem' },
  tabRow:      { display:'flex', gap:4, marginBottom:20, flexWrap:'wrap' },
  tab:         { background:'#fff', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'9px 16px', fontSize:13, fontWeight:600, cursor:'pointer', color:'#64748b' },
  tabActive:   { background:'#eff6ff', border:'1.5px solid #1a56db', color:'#1a56db', fontWeight:800 },
  card:        { background:'#fff', borderRadius:18, padding:'22px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:   { fontSize:17, fontWeight:800, color:'#0f172a', margin:'0 0 16px' },
  fieldLabel:  { fontSize:13, fontWeight:700, color:'#374151', marginBottom:8 },
  platBtn:     { borderRadius:10, padding:'7px 14px', fontSize:13, fontWeight:700, cursor:'pointer', transition:'all 0.15s', whiteSpace:'nowrap' },
  textarea:    { width:'100%', border:'1.5px solid #e2e8f0', borderRadius:12, padding:'12px 14px', fontSize:14, outline:'none', resize:'vertical', fontFamily:'inherit', boxSizing:'border-box', background:'#fafafa' },
  input:       { width:'100%', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 14px', fontSize:14, outline:'none', fontFamily:'inherit', boxSizing:'border-box', background:'#fafafa' },
  imgDrop:     { border:'2px dashed #e2e8f0', borderRadius:12, padding:'20px', textAlign:'center', fontSize:13, color:'#94a3b8', cursor:'pointer' },
  publishBtn:  { background:'linear-gradient(135deg,#E1306C,#833ab4)', color:'#fff', border:'none', borderRadius:12, padding:'12px 22px', fontSize:14, fontWeight:800, cursor:'pointer', flex:1 },
  scheduleBtn: { background:'#eff6ff', color:'#1a56db', border:'1.5px solid #1a56db', borderRadius:12, padding:'12px 22px', fontSize:14, fontWeight:800, cursor:'pointer', flex:1 },
  previewCard: { background:'#f8fafc', borderRadius:14, padding:'16px', border:'1px solid #e2e8f0' },
  emptyPreview:{ textAlign:'center', padding:'3rem', color:'#94a3b8', fontSize:14 },
  statusChip:  { borderRadius:20, padding:'3px 10px', fontSize:11, fontWeight:700 },
  useBtn:      { background:'linear-gradient(135deg,#1a56db,#7c3aed)', color:'#fff', border:'none', borderRadius:10, padding:'8px 16px', fontSize:13, fontWeight:700, cursor:'pointer' },
}
