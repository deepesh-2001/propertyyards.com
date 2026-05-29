import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const TABS = [
  { id: 'wallet',        label: '👛 Wallet',        icon: '👛' },
  { id: 'transactions',  label: '🔄 Transactions',  icon: '🔄' },
  { id: 'invoices',      label: '🧾 Invoices',       icon: '🧾' },
  { id: 'installments',  label: '📅 Installments',   icon: '📅' },
  { id: 'subscriptions', label: '⭐ Subscriptions',  icon: '⭐' },
  { id: 'methods',       label: '💳 Payment Methods', icon: '💳' },
]

const TRANSACTIONS = [
  { id:'TXN001', date:'2025-05-28', desc:'Property Listing Fee — 3BHK Gurgaon',  amount: -2999,   status:'success', method:'UPI' },
  { id:'TXN002', date:'2025-05-26', desc:'Cashback Credit — Referral Bonus',      amount: +500,    status:'success', method:'Wallet' },
  { id:'TXN003', date:'2025-05-24', desc:'Premium Listing Upgrade',               amount: -4999,   status:'success', method:'Card' },
  { id:'TXN004', date:'2025-05-20', desc:'Home Loan Processing Fee — SBI',        amount: -15000,  status:'success', method:'NetBanking' },
  { id:'TXN005', date:'2025-05-18', desc:'Site Visit Booking — DLF Arbour',       amount: -500,    status:'refunded',method:'UPI' },
  { id:'TXN006', date:'2025-05-15', desc:'PropertyYards Pro Subscription',        amount: -999,    status:'success', method:'Card' },
  { id:'TXN007', date:'2025-05-10', desc:'Stamp Duty Registration Assistance',    amount: -5000,   status:'pending', method:'NEFT' },
]

const INVOICES = [
  { id:'INV-2025-0142', date:'2025-05-01', due:'2025-06-01', desc:'Premium Broker Plan — May 2025',      amount: 4999,  status:'paid' },
  { id:'INV-2025-0121', date:'2025-04-01', due:'2025-05-01', desc:'Premium Broker Plan — April 2025',    amount: 4999,  status:'paid' },
  { id:'INV-2025-0098', date:'2025-03-01', due:'2025-04-01', desc:'Featured Listing × 3 — March 2025',  amount: 8997,  status:'paid' },
  { id:'INV-2025-0167', date:'2025-05-28', due:'2025-06-28', desc:'AI Tools Package — June 2025',        amount: 2499,  status:'due' },
]

const INSTALLMENTS = [
  { property: 'Godrej Horizon 3BHK, Gurgaon',   total: 18000000, paid: 5400000,  next: '2025-06-15', amount: 1800000, no: 4,  of: 10 },
  { property: 'DLF Plots Sector 63, Gurgaon',   total: 4500000,  paid: 4500000,  next: null,          amount: 0,       no: 10, of: 10 },
]

const PAYMENT_METHODS = [
  { id: 1, type: 'card',       label: 'HDFC Credit Card', detail: '•••• •••• •••• 4242', expiry: '08/27', primary: true,  icon: '💳' },
  { id: 2, type: 'upi',        label: 'Google Pay UPI',   detail: 'deepesh@okaxis',       expiry: null,   primary: false, icon: '📱' },
  { id: 3, type: 'netbanking', label: 'SBI Net Banking',  detail: 'Account ••••1234',     expiry: null,   primary: false, icon: '🏦' },
]

const SUBS = [
  { plan: 'PropertyYards Pro', price: 999,   billing: 'Monthly', features: ['Unlimited Listings','Featured Badge','CRM Access','Analytics'], status: 'active', renewal: '2025-06-15' },
  { plan: 'AI Tools Bundle',   price: 2499,  billing: 'Monthly', features: ['3D Models','AI Descriptions','Image Gen','Price Predictor'],     status: 'active', renewal: '2025-06-28' },
]

const STATUS_COLOR = { success:'#059669', refunded:'#f59e0b', pending:'#0284c7', paid:'#059669', due:'#dc2626', active:'#059669', inactive:'#94a3b8' }

export default function Payments() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()
  const [tab, setTab] = useState('wallet')
  const [showTopup, setShowTopup] = useState(false)
  const [topupAmt, setTopupAmt]   = useState('')

  const balance   = 3241
  const spent     = TRANSACTIONS.filter(t => t.amount < 0).reduce((a,b) => a + Math.abs(b.amount), 0)

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <h1 style={s.h1}>💳 Payments & Wallet</h1>
          <p style={s.sub}>Manage transactions, invoices, installments and subscriptions</p>
        </div>
      </div>

      {/* Tab bar */}
      <div style={s.tabBar}>
        <div style={s.tabInner}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{ ...s.tab, ...(tab === t.id ? s.tabActive : {}) }}>
              {t.icon}{!isMobile && ` ${t.label.split(' ').slice(1).join(' ')}`}
            </button>
          ))}
        </div>
      </div>

      <div style={s.wrap}>

        {/* WALLET */}
        {tab === 'wallet' && (
          <div style={{ display:'flex', flexDirection:'column', gap:24 }}>
            <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3,1fr)', gap:16 }}>
              <div style={s.walletCard}>
                <div style={{ fontSize:13, fontWeight:700, color:'rgba(255,255,255,0.7)', marginBottom:6 }}>Wallet Balance</div>
                <div style={{ fontSize:36, fontWeight:900, letterSpacing:'-1px' }}>₹{balance.toLocaleString('en-IN')}</div>
                <div style={{ marginTop:16, display:'flex', gap:10 }}>
                  <button onClick={() => setShowTopup(true)} style={s.walletBtn}>+ Add Money</button>
                  <button onClick={() => toast('Withdrawal initiated','success')} style={{ ...s.walletBtn, background:'rgba(255,255,255,0.15)' }}>Withdraw</button>
                </div>
              </div>
              <div style={s.statCard}>
                <div style={{ fontSize:24 }}>💸</div>
                <div style={{ fontSize:26, fontWeight:900, color:'#dc2626', letterSpacing:'-0.5px' }}>₹{spent.toLocaleString('en-IN')}</div>
                <div style={{ fontSize:13, fontWeight:600, color:'#374151', marginTop:4 }}>Total Spent</div>
                <div style={{ fontSize:11, color:'#94a3b8' }}>All time</div>
              </div>
              <div style={s.statCard}>
                <div style={{ fontSize:24 }}>📈</div>
                <div style={{ fontSize:26, fontWeight:900, color:'#059669', letterSpacing:'-0.5px' }}>₹500</div>
                <div style={{ fontSize:13, fontWeight:600, color:'#374151', marginTop:4 }}>Cashback Earned</div>
                <div style={{ fontSize:11, color:'#94a3b8' }}>This month</div>
              </div>
            </div>
            <div style={s.card}>
              <h3 style={s.cardTitle}>Recent Activity</h3>
              {TRANSACTIONS.slice(0,5).map(t => <TxnRow key={t.id} t={t} />)}
            </div>
          </div>
        )}

        {/* TRANSACTIONS */}
        {tab === 'transactions' && (
          <div style={s.card}>
            <h3 style={s.cardTitle}>All Transactions</h3>
            <div style={{ overflowX:'auto' }}>
              <table style={s.table}>
                <thead>
                  <tr style={{ background:'#f8fafc' }}>
                    {['ID','Date','Description','Method','Amount','Status'].map(h => <th key={h} style={s.th}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {TRANSACTIONS.map((t, i) => (
                    <tr key={t.id} style={i%2===0?{}:{background:'#fafafa'}}>
                      <td style={s.td}><span style={{ fontFamily:'monospace', fontSize:12, color:'#64748b' }}>{t.id}</span></td>
                      <td style={s.td}>{t.date}</td>
                      <td style={s.td}><span style={{ fontWeight:600 }}>{t.desc}</span></td>
                      <td style={s.td}>{t.method}</td>
                      <td style={{ ...s.td, fontWeight:800, color: t.amount > 0 ? '#059669' : '#dc2626' }}>
                        {t.amount > 0 ? '+' : ''}₹{Math.abs(t.amount).toLocaleString('en-IN')}
                      </td>
                      <td style={s.td}><span style={{ ...s.badge, background:`${STATUS_COLOR[t.status]}18`, color:STATUS_COLOR[t.status] }}>{t.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* INVOICES */}
        {tab === 'invoices' && (
          <div style={s.card}>
            <h3 style={s.cardTitle}>Invoices</h3>
            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              {INVOICES.map(inv => (
                <div key={inv.id} style={s.invRow}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontWeight:700, fontSize:15, color:'#0f172a' }}>{inv.desc}</div>
                    <div style={{ fontSize:12, color:'#64748b', marginTop:4 }}>
                      <span style={{ fontFamily:'monospace' }}>{inv.id}</span> · Issued {inv.date} · Due {inv.due}
                    </div>
                  </div>
                  <div style={{ display:'flex', gap:12, alignItems:'center' }}>
                    <span style={{ fontSize:18, fontWeight:900, color:'#1a56db' }}>₹{inv.amount.toLocaleString('en-IN')}</span>
                    <span style={{ ...s.badge, background:`${STATUS_COLOR[inv.status]}18`, color:STATUS_COLOR[inv.status] }}>{inv.status}</span>
                    <button onClick={() => toast(`Downloading ${inv.id}...`,'info')} style={s.dlBtn}>⬇ PDF</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* INSTALLMENTS */}
        {tab === 'installments' && (
          <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
            {INSTALLMENTS.map((inst, i) => {
              const pct = Math.round((inst.paid / inst.total) * 100)
              return (
                <div key={i} style={s.card}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:12 }}>
                    <div>
                      <div style={{ fontSize:16, fontWeight:800, color:'#0f172a', marginBottom:4 }}>{inst.property}</div>
                      <div style={{ fontSize:13, color:'#64748b' }}>Installment {inst.no} of {inst.of}</div>
                    </div>
                    {inst.next ? (
                      <div style={s.nextDue}>
                        <div style={{ fontSize:11, color:'#dc2626', fontWeight:700, textTransform:'uppercase' }}>Next Due</div>
                        <div style={{ fontSize:16, fontWeight:900, color:'#dc2626' }}>₹{inst.amount.toLocaleString('en-IN')}</div>
                        <div style={{ fontSize:12, color:'#64748b' }}>{inst.next}</div>
                      </div>
                    ) : (
                      <span style={{ ...s.badge, background:'#d1fae5', color:'#065f46', fontSize:14, padding:'6px 16px' }}>✅ Fully Paid</span>
                    )}
                  </div>
                  <div style={{ margin:'16px 0 6px', display:'flex', justifyContent:'space-between' }}>
                    <span style={{ fontSize:13, fontWeight:600, color:'#374151' }}>₹{inst.paid.toLocaleString('en-IN')} paid</span>
                    <span style={{ fontSize:13, fontWeight:800, color:'#1a56db' }}>{pct}%</span>
                  </div>
                  <div style={s.progBar}><div style={{ ...s.progFill, width:`${pct}%` }} /></div>
                  <div style={{ fontSize:12, color:'#94a3b8', marginTop:4 }}>Total: ₹{inst.total.toLocaleString('en-IN')}</div>
                  {inst.next && (
                    <button onClick={() => toast('Payment initiated','success')} style={{ ...s.payBtn, marginTop:14 }}>
                      💳 Pay ₹{inst.amount.toLocaleString('en-IN')} Now
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* SUBSCRIPTIONS */}
        {tab === 'subscriptions' && (
          <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)', gap:20 }}>
            {SUBS.map(sub => (
              <div key={sub.plan} style={{ ...s.card, borderTop:`4px solid #1a56db` }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:16 }}>
                  <div>
                    <div style={{ fontSize:18, fontWeight:900, color:'#0f172a' }}>{sub.plan}</div>
                    <div style={{ fontSize:13, color:'#64748b', marginTop:2 }}>₹{sub.price}/mo · {sub.billing}</div>
                  </div>
                  <span style={{ ...s.badge, background:'#d1fae5', color:'#065f46' }}>{sub.status}</span>
                </div>
                <div style={{ display:'flex', flexDirection:'column', gap:6, marginBottom:16 }}>
                  {sub.features.map(f => <div key={f} style={{ fontSize:13, color:'#374151' }}>✓ {f}</div>)}
                </div>
                <div style={{ fontSize:12, color:'#94a3b8', marginBottom:14 }}>Renews {sub.renewal}</div>
                <div style={{ display:'flex', gap:10 }}>
                  <button onClick={() => toast('Plan upgraded','success')} style={s.payBtn}>⬆ Upgrade</button>
                  <button onClick={() => toast('Cancellation requested','info')} style={{ ...s.dlBtn }}>Cancel</button>
                </div>
              </div>
            ))}
            <div style={{ ...s.card, border:'2px dashed #e2e8f0', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:12, minHeight:200, cursor:'pointer' }}
              onClick={() => toast('Showing all plans...','info')}>
              <div style={{ fontSize:36 }}>➕</div>
              <div style={{ fontSize:16, fontWeight:700, color:'#64748b' }}>Add New Plan</div>
            </div>
          </div>
        )}

        {/* PAYMENT METHODS */}
        {tab === 'methods' && (
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            {PAYMENT_METHODS.map(m => (
              <div key={m.id} style={{ ...s.card, display:'flex', alignItems:'center', gap:16 }}>
                <span style={{ fontSize:32 }}>{m.icon}</span>
                <div style={{ flex:1 }}>
                  <div style={{ fontWeight:700, fontSize:15, color:'#0f172a' }}>{m.label}</div>
                  <div style={{ fontSize:13, color:'#64748b', fontFamily:'monospace', marginTop:2 }}>{m.detail}</div>
                  {m.expiry && <div style={{ fontSize:12, color:'#94a3b8' }}>Expires {m.expiry}</div>}
                </div>
                {m.primary && <span style={{ ...s.badge, background:'#d1fae5', color:'#065f46' }}>Primary</span>}
                <button onClick={() => toast('Removed','success')} style={{ ...s.dlBtn }}>Remove</button>
              </div>
            ))}
            <button onClick={() => toast('Add method flow...','info')} style={s.payBtn}>+ Add Payment Method</button>
          </div>
        )}
      </div>

      {/* Topup Modal */}
      {showTopup && (
        <div style={s.overlay} onClick={() => setShowTopup(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()} className="fade-in">
            <div style={{ display:'flex', justifyContent:'space-between', padding:'20px 24px', borderBottom:'1px solid #e2e8f0' }}>
              <h3 style={{ margin:0, fontWeight:900, fontSize:18 }}>Add Money to Wallet</h3>
              <button onClick={() => setShowTopup(false)} style={s.closeBtn}>✕</button>
            </div>
            <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:16 }}>
              <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
                {[500,1000,2000,5000].map(a => (
                  <button key={a} onClick={() => setTopupAmt(String(a))}
                    style={{ ...s.dlBtn, ...(topupAmt===String(a)?{background:'#eff6ff',color:'#1a56db',border:'1.5px solid #1a56db'}:{}) }}>
                    ₹{a}
                  </button>
                ))}
              </div>
              <input value={topupAmt} onChange={e => setTopupAmt(e.target.value)} placeholder="Or enter custom amount"
                style={{ border:'1.5px solid #e2e8f0', borderRadius:10, padding:'11px 14px', fontSize:15, outline:'none' }} type="number" />
              <button onClick={() => { toast(`₹${topupAmt} added to wallet!`,'success'); setShowTopup(false) }} style={s.payBtn}>
                💳 Add ₹{topupAmt || '0'} via UPI / Card
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TxnRow({ t }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:14, padding:'12px 0', borderBottom:'1px solid #f1f5f9' }}>
      <div style={{ width:36, height:36, borderRadius:'50%', background: t.amount>0?'#d1fae5':'#fee2e2', display:'flex', alignItems:'center', justifyContent:'center', fontSize:16 }}>
        {t.amount > 0 ? '⬇' : '⬆'}
      </div>
      <div style={{ flex:1 }}>
        <div style={{ fontSize:14, fontWeight:600, color:'#0f172a' }}>{t.desc}</div>
        <div style={{ fontSize:12, color:'#94a3b8', marginTop:2 }}>{t.date} · {t.method}</div>
      </div>
      <div style={{ textAlign:'right' }}>
        <div style={{ fontWeight:800, fontSize:15, color: t.amount>0?'#059669':'#dc2626' }}>
          {t.amount>0?'+':''}₹{Math.abs(t.amount).toLocaleString('en-IN')}
        </div>
        <span style={{ fontSize:11, fontWeight:700, color:STATUS_COLOR[t.status] }}>{t.status}</span>
      </div>
    </div>
  )
}

const s = {
  page:       { background:'#f8fafc', minHeight:'100vh', paddingBottom:'4rem' },
  banner:     { background:'linear-gradient(135deg,#0f172a 0%,#059669 100%)', color:'#fff', padding:'2rem 0' },
  bannerInner:{ maxWidth:1240, margin:'0 auto', padding:'0 1.5rem' },
  h1:         { fontSize:'clamp(20px,3vw,28px)', fontWeight:900, margin:0 },
  sub:        { fontSize:13, opacity:0.75, marginTop:4 },
  tabBar:     { background:'#fff', borderBottom:'1px solid #e2e8f0', position:'sticky', top:60, zIndex:100, boxShadow:'0 1px 8px rgba(0,0,0,0.04)' },
  tabInner:   { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem', display:'flex', gap:2, overflowX:'auto' },
  tab:        { background:'none', border:'none', padding:'13px 14px', fontSize:14, fontWeight:600, color:'#64748b', cursor:'pointer', borderBottom:'3px solid transparent', whiteSpace:'nowrap' },
  tabActive:  { color:'#1a56db', borderBottom:'3px solid #1a56db', fontWeight:800 },
  wrap:       { maxWidth:1240, margin:'0 auto', padding:'2rem 1.5rem' },
  walletCard: { background:'linear-gradient(135deg,#1a56db,#7c3aed)', color:'#fff', borderRadius:20, padding:'28px', boxShadow:'0 8px 32px rgba(26,86,219,0.3)' },
  walletBtn:  { background:'rgba(255,255,255,0.2)', border:'1px solid rgba(255,255,255,0.3)', color:'#fff', borderRadius:10, padding:'9px 16px', fontSize:14, fontWeight:700, cursor:'pointer' },
  statCard:   { background:'#fff', borderRadius:16, padding:'20px', border:'1px solid #e2e8f0', display:'flex', flexDirection:'column', gap:4 },
  card:       { background:'#fff', borderRadius:18, padding:'22px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:  { fontSize:18, fontWeight:800, color:'#0f172a', margin:'0 0 16px' },
  table:      { width:'100%', borderCollapse:'collapse', minWidth:600 },
  th:         { padding:'11px 12px', textAlign:'left', fontSize:12, fontWeight:800, color:'#64748b', textTransform:'uppercase', letterSpacing:0.5, borderBottom:'2px solid #e2e8f0', whiteSpace:'nowrap' },
  td:         { padding:'12px 12px', fontSize:14, color:'#0f172a', borderBottom:'1px solid #f1f5f9' },
  badge:      { borderRadius:20, padding:'3px 12px', fontSize:12, fontWeight:700 },
  invRow:     { display:'flex', alignItems:'center', gap:16, padding:'16px', background:'#f8fafc', borderRadius:14, border:'1px solid #e2e8f0', flexWrap:'wrap' },
  dlBtn:      { background:'#f1f5f9', border:'1px solid #e2e8f0', borderRadius:10, padding:'7px 14px', fontSize:13, fontWeight:700, cursor:'pointer', color:'#374151', whiteSpace:'nowrap' },
  payBtn:     { background:'linear-gradient(135deg,#1a56db,#2563eb)', color:'#fff', border:'none', borderRadius:12, padding:'12px 22px', fontSize:14, fontWeight:800, cursor:'pointer', boxShadow:'0 4px 14px rgba(26,86,219,0.3)' },
  progBar:    { height:10, background:'#f1f5f9', borderRadius:99, overflow:'hidden' },
  progFill:   { height:'100%', background:'linear-gradient(90deg,#1a56db,#059669)', borderRadius:99 },
  nextDue:    { background:'#fef2f2', borderRadius:14, padding:'12px 16px', textAlign:'right', border:'1px solid #fecaca' },
  overlay:    { position:'fixed', inset:0, background:'rgba(0,0,0,0.6)', zIndex:500, display:'flex', alignItems:'center', justifyContent:'center', padding:'1rem' },
  modal:      { background:'#fff', borderRadius:20, width:'100%', maxWidth:440, boxShadow:'0 24px 80px rgba(0,0,0,0.3)', overflow:'hidden' },
  closeBtn:   { background:'#f1f5f9', border:'none', borderRadius:8, padding:'6px 12px', cursor:'pointer', fontSize:16, fontWeight:700 },
}
