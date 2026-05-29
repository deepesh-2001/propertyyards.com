import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const REVIEWS = [
  { id:1, author:'Rajesh Kumar',   avatar:'R', rating:5, date:'2025-05-27', property:'3BHK Gurgaon Sector 45', text:'Excellent service! The team was very professional and helped us find our dream home within our budget. The AI-powered search made it so easy to filter properties.', sentiment:'positive', helpful:24 },
  { id:2, author:'Priya Singh',    avatar:'P', rating:4, date:'2025-05-25', property:'2BHK Noida Sector 62',   text:'Good platform overall. The property descriptions were accurate and the broker was responsive. Would have given 5 stars if the virtual tour was available for more listings.', sentiment:'positive', helpful:18 },
  { id:3, author:'Amit Verma',     avatar:'A', rating:5, date:'2025-05-22', property:'Villa Gurgaon DLF',      text:'Bought a villa through PropertyYards. The entire process from listing to registration was smooth. Highly recommend the premium service — worth every rupee.', sentiment:'positive', helpful:31 },
  { id:4, author:'Sunita Patel',   avatar:'S', rating:3, date:'2025-05-20', property:'Apartment Mumbai Bandra', text:'Average experience. The listing photos were outdated and the actual property looked different. Needs better quality control on images and descriptions.', sentiment:'neutral',  helpful:8 },
  { id:5, author:'Vikram Nair',    avatar:'V', rating:2, date:'2025-05-18', property:'Office Space Noida',     text:'The broker was unresponsive for 2 days. Finally got a response but the property was already sold. Real-time availability updates would help a lot.', sentiment:'negative', helpful:14 },
  { id:6, author:'Meera Reddy',    avatar:'M', rating:5, date:'2025-05-15', property:'3BHK Bangalore Whitefield', text:'PropertyYards CRM is amazing for brokers! I manage all my leads, schedule visits and track conversions in one place. Revenue has increased 40% since joining.', sentiment:'positive', helpful:42 },
]

const SENTIMENTS = { positive:'#059669', neutral:'#f59e0b', negative:'#dc2626' }
const CATS = ['All','Property Listings','Broker Service','Platform UX','AI Features','Payment','Mobile App']

export default function Feedback() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()

  const [reviews, setReviews]   = useState(REVIEWS)
  const [cat, setCat]           = useState('All')
  const [sort, setSort]         = useState('recent')
  const [replyOpen, setReplyOpen] = useState(null)
  const [replyText, setReplyText] = useState('')
  const [newReview, setNewReview] = useState({ rating:5, text:'', property:'' })
  const [showForm, setShowForm]   = useState(false)
  const [helpful, setHelpful]     = useState({})

  const avgRating = (reviews.reduce((a,b) => a+b.rating, 0) / reviews.length).toFixed(1)
  const dist = [5,4,3,2,1].map(r => ({ r, count: reviews.filter(rev=>rev.rating===r).length }))

  const submitReview = () => {
    if (!newReview.text) { toast('Write your review first','error'); return }
    setReviews(prev => [{
      id: Date.now(), author:'You', avatar:'Y', rating: newReview.rating,
      date: new Date().toISOString().slice(0,10), property: newReview.property || 'General',
      text: newReview.text, sentiment:'positive', helpful:0
    }, ...prev])
    toast('Review submitted!','success')
    setShowForm(false)
    setNewReview({ rating:5, text:'', property:'' })
  }

  const submitReply = (id) => {
    toast('Reply posted!','success')
    setReplyOpen(null)
    setReplyText('')
  }

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>⭐ Reviews & Feedback</h1>
            <p style={s.sub}>Transparent ratings, AI sentiment analysis, and genuine user reviews</p>
          </div>
          <button onClick={() => setShowForm(true)} style={s.writebtn}>✍️ Write Review</button>
        </div>
      </div>

      <div style={s.wrap}>
        {/* Summary */}
        <div style={{ display:'grid', gridTemplateColumns: isMobile ? '1fr' : '280px 1fr', gap:24, marginBottom:28 }}>
          <div style={{ ...s.card, textAlign:'center', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
            <div style={{ fontSize:60, fontWeight:900, color:'#f59e0b', letterSpacing:'-3px', lineHeight:1 }}>{avgRating}</div>
            <div style={{ fontSize:24, margin:'8px 0 4px' }}>{'⭐'.repeat(Math.round(avgRating))}</div>
            <div style={{ fontSize:14, color:'#64748b' }}>Based on {reviews.length} reviews</div>
          </div>
          <div style={s.card}>
            <h3 style={s.cardTitle}>Rating Distribution</h3>
            {dist.map(d => (
              <div key={d.r} style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
                <span style={{ fontSize:13, fontWeight:700, color:'#374151', width:14 }}>{d.r}</span>
                <span style={{ fontSize:14 }}>⭐</span>
                <div style={{ flex:1, height:10, background:'#f1f5f9', borderRadius:99, overflow:'hidden' }}>
                  <div style={{ height:'100%', background:'#f59e0b', borderRadius:99, width:`${reviews.length ? (d.count/reviews.length)*100 : 0}%` }} />
                </div>
                <span style={{ fontSize:13, color:'#94a3b8', width:20 }}>{d.count}</span>
              </div>
            ))}
            <div style={{ display:'flex', gap:20, marginTop:14, flexWrap:'wrap' }}>
              {Object.entries({ positive:reviews.filter(r=>r.sentiment==='positive').length, neutral:reviews.filter(r=>r.sentiment==='neutral').length, negative:reviews.filter(r=>r.sentiment==='negative').length }).map(([k,v]) => (
                <div key={k} style={{ display:'flex', gap:6, alignItems:'center' }}>
                  <div style={{ width:10, height:10, borderRadius:'50%', background:SENTIMENTS[k] }} />
                  <span style={{ fontSize:12, color:'#374151', fontWeight:600 }}>{v} {k}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display:'flex', gap:8, marginBottom:20, flexWrap:'wrap', alignItems:'center' }}>
          <div style={{ flex:1, display:'flex', gap:6, flexWrap:'wrap' }}>
            {CATS.map(c => (
              <button key={c} onClick={() => setCat(c)}
                style={{ ...s.filterBtn, ...(cat===c?s.filterActive:{}) }}>{c}</button>
            ))}
          </div>
          <select value={sort} onChange={e => setSort(e.target.value)} style={s.sortSelect}>
            <option value="recent">Most Recent</option>
            <option value="highest">Highest Rated</option>
            <option value="lowest">Lowest Rated</option>
            <option value="helpful">Most Helpful</option>
          </select>
        </div>

        {/* Reviews */}
        <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
          {[...reviews].sort((a,b) => sort==='highest'?b.rating-a.rating:sort==='lowest'?a.rating-b.rating:sort==='helpful'?b.helpful-a.helpful:b.id-a.id).map(rev => (
            <div key={rev.id} style={s.card}>
              <div style={{ display:'flex', gap:14, alignItems:'flex-start' }}>
                <div style={s.avatar}>{rev.avatar}</div>
                <div style={{ flex:1 }}>
                  <div style={{ display:'flex', justifyContent:'space-between', flexWrap:'wrap', gap:8 }}>
                    <div>
                      <span style={{ fontWeight:800, fontSize:15, color:'#0f172a' }}>{rev.author}</span>
                      <span style={{ fontSize:12, color:'#94a3b8', marginLeft:10 }}>{rev.date}</span>
                    </div>
                    <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                      <span style={{ ...s.sentBadge, background:`${SENTIMENTS[rev.sentiment]}18`, color:SENTIMENTS[rev.sentiment] }}>{rev.sentiment}</span>
                      <span style={{ fontSize:14 }}>{'⭐'.repeat(rev.rating)}{'☆'.repeat(5-rev.rating)}</span>
                    </div>
                  </div>
                  <div style={{ fontSize:12, color:'#64748b', margin:'4px 0 8px' }}>📍 {rev.property}</div>
                  <p style={{ fontSize:14, color:'#374151', lineHeight:1.7, margin:'0 0 12px' }}>{rev.text}</p>
                  <div style={{ display:'flex', gap:12, alignItems:'center' }}>
                    <button onClick={() => setHelpful(prev => ({...prev,[rev.id]:(prev[rev.id]||rev.helpful)+1}))}
                      style={s.helpBtn}>👍 Helpful ({helpful[rev.id] || rev.helpful})</button>
                    <button onClick={() => setReplyOpen(replyOpen===rev.id?null:rev.id)} style={s.helpBtn}>
                      💬 Reply
                    </button>
                  </div>
                  {replyOpen === rev.id && (
                    <div style={{ marginTop:12, display:'flex', gap:10 }} className="fade-in">
                      <input value={replyText} onChange={e => setReplyText(e.target.value)}
                        placeholder="Write a professional reply..." style={{ ...s.replyInput, flex:1 }} />
                      <button onClick={() => submitReply(rev.id)} style={s.replyBtn}>Send</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Write Review Modal */}
      {showForm && (
        <div style={s.overlay} onClick={() => setShowForm(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()} className="fade-in">
            <div style={{ display:'flex', justifyContent:'space-between', padding:'20px 24px', borderBottom:'1px solid #e2e8f0' }}>
              <h3 style={{ margin:0, fontWeight:900, fontSize:18 }}>Write a Review</h3>
              <button onClick={() => setShowForm(false)} style={s.closeBtn}>✕</button>
            </div>
            <div style={{ padding:'20px 24px', display:'flex', flexDirection:'column', gap:16 }}>
              <div>
                <div style={s.fieldLabel}>Your Rating</div>
                <div style={{ display:'flex', gap:8 }}>
                  {[1,2,3,4,5].map(r => (
                    <button key={r} onClick={() => setNewReview(p=>({...p,rating:r}))}
                      style={{ fontSize:28, background:'none', border:'none', cursor:'pointer', opacity: r<=newReview.rating?1:0.3 }}>⭐</button>
                  ))}
                </div>
              </div>
              <div>
                <div style={s.fieldLabel}>Property (optional)</div>
                <input value={newReview.property} onChange={e => setNewReview(p=>({...p,property:e.target.value}))}
                  placeholder="e.g. 3BHK Gurgaon Sector 45" style={s.inputField} />
              </div>
              <div>
                <div style={s.fieldLabel}>Your Review</div>
                <textarea value={newReview.text} onChange={e => setNewReview(p=>({...p,text:e.target.value}))}
                  rows={4} placeholder="Share your experience with PropertyYards..." style={{ ...s.inputField, resize:'vertical' }} />
              </div>
              <button onClick={submitReview} style={s.submitBtn}>Submit Review →</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const s = {
  page:        { background:'#f8fafc', minHeight:'100vh', paddingBottom:'4rem' },
  banner:      { background:'linear-gradient(135deg,#0f172a 0%,#f59e0b 100%)', color:'#fff', padding:'2rem 0' },
  bannerInner: { maxWidth:1240, margin:'0 auto', padding:'0 1.5rem', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:12 },
  h1:          { fontSize:'clamp(20px,3vw,28px)', fontWeight:900, margin:0 },
  sub:         { fontSize:13, opacity:0.75, marginTop:4 },
  writebtn:    { background:'#fff', color:'#0f172a', border:'none', borderRadius:12, padding:'10px 20px', fontWeight:800, fontSize:14, cursor:'pointer' },
  wrap:        { maxWidth:1240, margin:'0 auto', padding:'2rem 1.5rem' },
  card:        { background:'#fff', borderRadius:18, padding:'22px', border:'1px solid #e2e8f0', boxShadow:'0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:   { fontSize:17, fontWeight:800, color:'#0f172a', margin:'0 0 14px' },
  filterBtn:   { background:'#f1f5f9', border:'1px solid #e2e8f0', borderRadius:20, padding:'5px 14px', fontSize:12, fontWeight:600, cursor:'pointer', color:'#374151' },
  filterActive:{ background:'#eff6ff', border:'1px solid #1a56db', color:'#1a56db' },
  sortSelect:  { border:'1.5px solid #e2e8f0', borderRadius:10, padding:'7px 12px', fontSize:13, fontWeight:600, outline:'none', background:'#fff', cursor:'pointer' },
  avatar:      { width:42, height:42, borderRadius:'50%', background:'linear-gradient(135deg,#f59e0b,#ef4444)', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:900, fontSize:16, flexShrink:0 },
  sentBadge:   { borderRadius:20, padding:'3px 10px', fontSize:11, fontWeight:700 },
  helpBtn:     { background:'#f1f5f9', border:'1px solid #e2e8f0', borderRadius:20, padding:'5px 12px', fontSize:12, fontWeight:600, cursor:'pointer', color:'#374151' },
  replyInput:  { border:'1.5px solid #e2e8f0', borderRadius:10, padding:'9px 14px', fontSize:14, outline:'none' },
  replyBtn:    { background:'#1a56db', color:'#fff', border:'none', borderRadius:10, padding:'9px 16px', fontSize:13, fontWeight:700, cursor:'pointer' },
  overlay:     { position:'fixed', inset:0, background:'rgba(0,0,0,0.6)', zIndex:500, display:'flex', alignItems:'center', justifyContent:'center', padding:'1rem' },
  modal:       { background:'#fff', borderRadius:20, width:'100%', maxWidth:520, boxShadow:'0 24px 80px rgba(0,0,0,0.3)', overflow:'hidden' },
  closeBtn:    { background:'#f1f5f9', border:'none', borderRadius:8, padding:'6px 12px', cursor:'pointer', fontSize:16, fontWeight:700 },
  fieldLabel:  { fontSize:13, fontWeight:700, color:'#374151', marginBottom:8 },
  inputField:  { width:'100%', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 14px', fontSize:14, outline:'none', fontFamily:'inherit', boxSizing:'border-box', background:'#fafafa' },
  submitBtn:   { background:'linear-gradient(135deg,#1a56db,#7c3aed)', color:'#fff', border:'none', borderRadius:12, padding:'13px', fontSize:15, fontWeight:800, cursor:'pointer' },
}
