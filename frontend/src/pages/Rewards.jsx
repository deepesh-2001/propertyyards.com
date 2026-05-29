import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const GIFT_CARDS = [
  { brand: 'Amazon',   icon: '📦', color: '#FF9900', points: 500 },
  { brand: 'Flipkart', icon: '🛒', color: '#2874f0', points: 500 },
  { brand: 'Swiggy',   icon: '🍔', color: '#FC8019', points: 200 },
  { brand: 'Zomato',   icon: '🍕', color: '#E23744', points: 200 },
  { brand: 'Uber',     icon: '🚗', color: '#000000', points: 300 },
  { brand: 'MakeMyTrip',icon:'✈️',  color: '#005999', points: 800 },
]

const HISTORY = [
  { date:'2025-05-28', action:'Referred Priya Singh — Registered',              points: +200, type:'earn' },
  { date:'2025-05-25', action:'Property Inquiry Submitted',                     points: +50,  type:'earn' },
  { date:'2025-05-22', action:'Redeemed — Amazon Gift Card ₹500',              points: -500, type:'redeem' },
  { date:'2025-05-18', action:'Listed Property — 3BHK Gurgaon',                points: +100, type:'earn' },
  { date:'2025-05-15', action:'Referred Amit Verma — First Purchase',          points: +500, type:'earn' },
  { date:'2025-05-10', action:'Completed Profile (100%)',                       points: +150, type:'earn' },
  { date:'2025-05-05', action:'First Property View after Login',                points: +10,  type:'earn' },
]

const REFERRALS = [
  { name: 'Priya Singh',   email: 'priya@email.com',  status: 'Registered', earned: 200,  date: '2025-05-28' },
  { name: 'Amit Verma',    email: 'amit@email.com',   status: 'Purchased',  earned: 500,  date: '2025-05-15' },
  { name: 'Sunita Patel',  email: 'sunita@email.com', status: 'Invited',    earned: 0,    date: '2025-05-01' },
]

const TIERS = [
  { name: 'Silver',   min: 0,    max: 999,   color: '#94a3b8', perks: ['5% cashback on listings','Priority support'] },
  { name: 'Gold',     min: 1000, max: 4999,  color: '#f59e0b', perks: ['8% cashback','Featured badge','CRM access'] },
  { name: 'Platinum', min: 5000, max: 14999, color: '#7c3aed', perks: ['12% cashback','AI tools free','Dedicated manager'] },
  { name: 'Diamond',  min: 15000,max: 99999, color: '#0284c7', perks: ['15% cashback','All features free','VIP concierge'] },
]

export default function Rewards() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()

  const totalPoints = 1640
  const cashback    = 380
  const referralCode = 'PROP-DEEPESH-2025'
  const currentTier = TIERS.find(t => totalPoints >= t.min && totalPoints <= t.max) || TIERS[0]
  const nextTier    = TIERS[TIERS.indexOf(currentTier) + 1]
  const toNextTier  = nextTier ? nextTier.min - totalPoints : 0
  const tierPct     = nextTier ? Math.round(((totalPoints - currentTier.min) / (nextTier.min - currentTier.min)) * 100) : 100

  const [copied, setCopied] = useState(false)
  const copyCode = () => {
    navigator.clipboard?.writeText(referralCode)
    setCopied(true)
    toast('Referral code copied!', 'success')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <h1 style={s.h1}>🎁 Rewards & Referrals</h1>
          <p style={s.sub}>Earn points, get cashback, redeem gift cards and grow your rewards</p>
        </div>
      </div>

      <div style={s.wrap}>
        {/* Top row */}
        <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3,1fr)', gap:20, marginBottom:28 }}>

          {/* Points card */}
          <div style={s.pointsCard}>
            <div style={{ fontSize:13, fontWeight:700, opacity:0.8, marginBottom:4 }}>Total Points</div>
            <div style={{ fontSize:48, fontWeight:900, letterSpacing:'-2px', lineHeight:1 }}>{totalPoints.toLocaleString()}</div>
            <div style={{ fontSize:13, opacity:0.7, marginTop:6 }}>≈ ₹{Math.floor(totalPoints * 0.1)} wallet value</div>
            <div style={{ marginTop:16 }}>
              <div style={{ display:'flex', justifyContent:'space-between', fontSize:12, marginBottom:6 }}>
                <span style={{ fontWeight:700, color:currentTier.color }}>{currentTier.name}</span>
                {nextTier && <span style={{ opacity:0.7 }}>{toNextTier} pts to {nextTier.name}</span>}
              </div>
              <div style={{ height:8, background:'rgba(255,255,255,0.2)', borderRadius:99, overflow:'hidden' }}>
                <div style={{ height:'100%', width:`${tierPct}%`, background:'#fff', borderRadius:99 }} />
              </div>
            </div>
          </div>

          {/* Cashback card */}
          <div style={s.statCard}>
            <div style={{ fontSize:32, marginBottom:8 }}>💵</div>
            <div style={{ fontSize:32, fontWeight:900, color:'#059669', letterSpacing:'-0.5px' }}>₹{cashback}</div>
            <div style={{ fontSize:14, fontWeight:700, color:'#0f172a' }}>Cashback Balance</div>
            <div style={{ fontSize:12, color:'#64748b', marginTop:4 }}>Ready to redeem</div>
            <button onClick={() => toast('Cashback transferred to wallet!','success')} style={{ ...s.ctaBtn, marginTop:14 }}>
              Transfer to Wallet
            </button>
          </div>

          {/* Referral card */}
          <div style={s.statCard}>
            <div style={{ fontSize:32, marginBottom:8 }}>🔗</div>
            <div style={{ fontSize:14, fontWeight:700, color:'#0f172a', marginBottom:8 }}>Your Referral Code</div>
            <div style={{ background:'#f1f5f9', borderRadius:10, padding:'10px 14px', fontFamily:'monospace', fontWeight:800, fontSize:15, color:'#1a56db', letterSpacing:2, marginBottom:12 }}>
              {referralCode}
            </div>
            <button onClick={copyCode} style={s.ctaBtn}>{copied ? '✅ Copied!' : '📋 Copy & Share'}</button>
            <div style={{ fontSize:11, color:'#94a3b8', marginTop:8 }}>Earn 200–500 pts per referral</div>
          </div>
        </div>

        <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 380px', gap:24 }}>
          <div style={{ display:'flex', flexDirection:'column', gap:24 }}>

            {/* Redeem Gift Cards */}
            <div style={s.card}>
              <h3 style={s.cardTitle}>🎁 Redeem Gift Cards</h3>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(150px,1fr))', gap:12 }}>
                {GIFT_CARDS.map(gc => (
                  <div key={gc.brand} style={{ ...s.gcCard, borderTop:`3px solid ${gc.color}` }}>
                    <div style={{ fontSize:28 }}>{gc.icon}</div>
                    <div style={{ fontWeight:800, fontSize:14, color:'#0f172a' }}>{gc.brand}</div>
                    <div style={{ fontSize:12, color:'#64748b' }}>{gc.points} pts = ₹100</div>
                    <button
                      onClick={() => totalPoints >= gc.points ? toast(`${gc.brand} gift card redeemed!`,'success') : toast('Not enough points','error')}
                      style={{ ...s.gcBtn, opacity: totalPoints >= gc.points ? 1 : 0.5 }}>
                      Redeem
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Points History */}
            <div style={s.card}>
              <h3 style={s.cardTitle}>📜 Points History</h3>
              {HISTORY.map((h, i) => (
                <div key={i} style={{ display:'flex', alignItems:'center', gap:14, padding:'11px 0', borderBottom:'1px solid #f1f5f9' }}>
                  <div style={{ width:34, height:34, borderRadius:'50%', background: h.type==='earn'?'#d1fae5':'#fee2e2', display:'flex', alignItems:'center', justifyContent:'center', fontSize:16 }}>
                    {h.type === 'earn' ? '⬆' : '⬇'}
                  </div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13, fontWeight:600, color:'#0f172a' }}>{h.action}</div>
                    <div style={{ fontSize:11, color:'#94a3b8', marginTop:2 }}>{h.date}</div>
                  </div>
                  <span style={{ fontWeight:800, fontSize:15, color: h.points>0?'#059669':'#dc2626' }}>
                    {h.points>0?'+':''}{h.points} pts
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display:'flex', flexDirection:'column', gap:24 }}>
            {/* Tier Benefits */}
            <div style={s.card}>
              <h3 style={s.cardTitle}>🏆 Membership Tiers</h3>
              {TIERS.map(t => (
                <div key={t.name} style={{ ...s.tierRow, borderLeft:`4px solid ${t.color}`, background: t.name===currentTier.name ? `${t.color}0d` : 'transparent' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6 }}>
                    <span style={{ fontWeight:800, fontSize:14, color: t.color }}>{t.name}</span>
                    <span style={{ fontSize:12, color:'#94a3b8' }}>{t.min.toLocaleString()}+ pts</span>
                    {t.name === currentTier.name && <span style={{ fontSize:11, fontWeight:800, background:`${t.color}18`, color:t.color, borderRadius:20, padding:'2px 10px' }}>Current</span>}
                  </div>
                  {t.perks.map(p => <div key={p} style={{ fontSize:12, color:'#374151' }}>✓ {p}</div>)}
                </div>
              ))}
            </div>

            {/* Referrals */}
            <div style={s.card}>
              <h3 style={s.cardTitle}>👥 My Referrals</h3>
              {REFERRALS.map((r, i) => (
                <div key={i} style={{ display:'flex', alignItems:'center', gap:12, padding:'11px 0', borderBottom:'1px solid #f1f5f9' }}>
                  <div style={s.refAvatar}>{r.name[0]}</div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13, fontWeight:700, color:'#0f172a' }}>{r.name}</div>
                    <div style={{ fontSize:11, color:'#64748b' }}>{r.date}</div>
                  </div>
                  <div style={{ textAlign:'right' }}>
                    <div style={{ fontSize:13, fontWeight:800, color: r.earned>0?'#059669':'#94a3b8' }}>+{r.earned} pts</div>
                    <div style={{ fontSize:11, color: r.status==='Purchased'?'#059669':r.status==='Registered'?'#f59e0b':'#94a3b8', fontWeight:700 }}>{r.status}</div>
                  </div>
                </div>
              ))}
              <div style={{ background:'#fffbeb', border:'1px solid #fcd34d', borderRadius:12, padding:'12px', marginTop:12, fontSize:13, color:'#78350f' }}>
                💡 Share your code and earn <strong>₹500</strong> when your friend makes their first purchase!
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const s = {
  page:       { background:'#f8fafc', minHeight:'100vh', paddingBottom:'4rem' },
  banner:     { background:'linear-gradient(135deg,#0f172a 0%,#7c3aed 100%)', color:'#fff', padding:'2rem 0' },
  bannerInner:{ maxWidth:1240, margin:'0 auto', padding:'0 1.5rem' },
  h1:         { fontSize:'clamp(20px,3vw,28px)', fontWeight:900, margin:0 },
  sub:        { fontSize:13, opacity:0.75, marginTop:4 },
  wrap:       { maxWidth:1240, margin:'0 auto', padding:'2rem 1.5rem' },
  pointsCard: { background:'linear-gradient(135deg,#7c3aed,#1a56db)', color:'#fff', borderRadius:20, padding:'28px', boxShadow:'0 8px 32px rgba(124,58,237,0.3)' },
  statCard:   { background:'#fff', borderRadius:20, padding:'24px', border:'1px solid #e2e8f0', display:'flex', flexDirection:'column', alignItems:'center', textAlign:'center' },
  ctaBtn:     { background:'linear-gradient(135deg,#1a56db,#7c3aed)', color:'#fff', border:'none', borderRadius:10, padding:'10px 20px', fontSize:14, fontWeight:700, cursor:'pointer', width:'100%' },
  card:       { background:'#fff', borderRadius:18, padding:'22px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:  { fontSize:17, fontWeight:800, color:'#0f172a', margin:'0 0 16px' },
  gcCard:     { background:'#f8fafc', borderRadius:14, padding:'16px', border:'1px solid #e2e8f0', display:'flex', flexDirection:'column', alignItems:'center', gap:6 },
  gcBtn:      { background:'linear-gradient(135deg,#1a56db,#7c3aed)', color:'#fff', border:'none', borderRadius:8, padding:'6px 16px', fontSize:12, fontWeight:700, cursor:'pointer', marginTop:4, width:'100%' },
  tierRow:    { borderRadius:10, padding:'12px 14px', marginBottom:10 },
  refAvatar:  { width:34, height:34, borderRadius:'50%', background:'linear-gradient(135deg,#7c3aed,#1a56db)', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:800, fontSize:15 },
}
