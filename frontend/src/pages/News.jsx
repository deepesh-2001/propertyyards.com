import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { Link } from 'react-router-dom'

const ARTICLES = [
  {
    id: 1, category: 'Market Trends', tag: '📈',
    title: 'Mumbai Real Estate Hits Record High in Q1 2025',
    excerpt: 'Property prices in Mumbai soared 18% year-on-year driven by luxury segment demand in Bandra, Worli and Powai. Experts predict sustained growth through 2026.',
    author: 'Ravi Sharma', date: 'May 28, 2025', readTime: '4 min',
    image: 'https://picsum.photos/seed/news1/800/450',
    featured: true,
  },
  {
    id: 2, category: 'Policy & RERA', tag: '⚖️',
    title: 'RERA Tightens Rules for Under-Construction Properties',
    excerpt: 'The Real Estate Regulatory Authority has mandated 70% escrow for all new project launches. Here's what it means for buyers and developers.',
    author: 'Priya Nair', date: 'May 26, 2025', readTime: '5 min',
    image: 'https://picsum.photos/seed/news2/800/450',
    featured: true,
  },
  {
    id: 3, category: 'Home Loans', tag: '🏦',
    title: 'RBI Holds Repo Rate — What It Means for Home Loan EMIs',
    excerpt: 'The Reserve Bank of India kept the repo rate unchanged at 6.5%. Floating rate borrowers can breathe easy for now, but fixed-rate deals are drying up.',
    author: 'Ankit Gupta', date: 'May 24, 2025', readTime: '3 min',
    image: 'https://picsum.photos/seed/news3/800/450',
    featured: false,
  },
  {
    id: 4, category: 'Investing', tag: '💰',
    title: '7 Tier-2 Cities to Watch for Real Estate Investment in 2025',
    excerpt: 'Indore, Surat, Coimbatore, Kochi, Jaipur, Lucknow, and Bhubaneswar are emerging as hotspots with 15–25% rental yield growth.',
    author: 'Meera Joshi', date: 'May 22, 2025', readTime: '6 min',
    image: 'https://picsum.photos/seed/news4/800/450',
    featured: false,
  },
  {
    id: 5, category: 'Legal', tag: '📝',
    title: 'Stamp Duty Reforms: States Slashing Rates to Boost Housing',
    excerpt: 'Maharashtra, Karnataka and Rajasthan have reduced stamp duty by 1–2%. Buyers can save up to ₹3 lakhs on a ₹1.5 Cr property.',
    author: 'Suresh Pillai', date: 'May 20, 2025', readTime: '4 min',
    image: 'https://picsum.photos/seed/news5/800/450',
    featured: false,
  },
  {
    id: 6, category: 'NRI', tag: '✈️',
    title: 'NRI Investment in Indian Real Estate Crosses ₹1 Lakh Crore',
    excerpt: 'Driven by a strong rupee and stable market fundamentals, NRI remittances into Indian real estate hit an all-time high in FY2025.',
    author: 'Deepa Kapoor', date: 'May 18, 2025', readTime: '5 min',
    image: 'https://picsum.photos/seed/news6/800/450',
    featured: false,
  },
  {
    id: 7, category: 'Rental Market', tag: '🏘️',
    title: 'Bengaluru Rentals Up 22%: The IT Surge Behind the Numbers',
    excerpt: 'The return-to-office wave and fresh hiring in Bengaluru's tech corridors have sent rental demand skyrocketing in Whitefield and Marathahalli.',
    author: 'Karthik R', date: 'May 15, 2025', readTime: '3 min',
    image: 'https://picsum.photos/seed/news7/800/450',
    featured: false,
  },
  {
    id: 8, category: 'Smart Homes', tag: '🤖',
    title: 'AI & PropTech: How Technology is Reshaping Indian Real Estate',
    excerpt: 'From AI-generated property descriptions to virtual tours and chatbot-driven inquiries — PropertyYards and peers are leading the PropTech revolution.',
    author: 'Tech Desk', date: 'May 12, 2025', readTime: '7 min',
    image: 'https://picsum.photos/seed/news8/800/450',
    featured: false,
  },
]

const CATEGORIES = ['All', 'Market Trends', 'Policy & RERA', 'Home Loans', 'Investing', 'Legal', 'NRI', 'Rental Market', 'Smart Homes']

export default function News() {
  const { isMobile } = useBreakpoint()
  const [activeCat, setActiveCat] = useState('All')
  const [search, setSearch]       = useState('')

  const filtered = ARTICLES.filter(a => {
    if (activeCat !== 'All' && a.category !== activeCat) return false
    if (search && !a.title.toLowerCase().includes(search.toLowerCase()) &&
        !a.excerpt.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const featured  = filtered.filter(a => a.featured)
  const rest      = filtered.filter(a => !a.featured)

  return (
    <div style={s.page}>
      {/* Hero */}
      <div style={s.hero}>
        <div style={s.heroInner}>
          <div style={s.heroBadge}>📰 PropertyYards News</div>
          <h1 style={s.heroH1}>Real Estate Insights<br />& Market Updates</h1>
          <p style={s.heroP}>Stay ahead with the latest news, policy changes, market trends and investment tips.</p>
          <div style={s.searchRow}>
            <span style={{ fontSize: 18 }}>🔍</span>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search articles..."
              style={s.heroInput}
            />
          </div>
        </div>
      </div>

      {/* Category bar */}
      <div style={s.catBar}>
        <div style={s.catInner}>
          {CATEGORIES.map(c => (
            <button key={c} onClick={() => setActiveCat(c)}
              style={{ ...s.catBtn, ...(activeCat === c ? s.catActive : {}) }}>
              {c}
            </button>
          ))}
        </div>
      </div>

      <div style={s.wrap}>
        {filtered.length === 0 ? (
          <div style={s.empty}>
            <div style={{ fontSize: 48 }}>🔍</div>
            <p>No articles found. Try a different search or category.</p>
          </div>
        ) : (
          <>
            {/* Featured articles */}
            {featured.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <h2 style={s.sectionTitle}>📌 Featured</h2>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)', gap: 24 }}>
                  {featured.map(a => <ArticleCard key={a.id} article={a} featured />)}
                </div>
              </div>
            )}

            {/* All others */}
            {rest.length > 0 && (
              <div>
                <h2 style={s.sectionTitle}>Latest Articles</h2>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill,minmax(320px,1fr))', gap: 24 }}>
                  {rest.map(a => <ArticleCard key={a.id} article={a} />)}
                </div>
              </div>
            )}
          </>
        )}

        {/* Newsletter CTA */}
        <div style={s.newsletter}>
          <div style={s.nlLeft}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📬</div>
            <h3 style={s.nlTitle}>Get Market Updates in Your Inbox</h3>
            <p style={s.nlSub}>Weekly digest of property news, rate changes and investment tips.</p>
          </div>
          <div style={s.nlRight}>
            <input placeholder="Your email address" style={s.nlInput} />
            <button style={s.nlBtn}>Subscribe Free →</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function ArticleCard({ article: a, featured }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      style={{ ...s.card, ...(hovered ? s.cardHover : {}), ...(featured ? s.cardFeatured : {}) }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="fade-in"
    >
      <div style={s.imgWrap}>
        <img src={a.image} alt={a.title} style={s.img}
          onError={e => { e.target.src = `https://picsum.photos/seed/fallback${a.id}/800/450` }} />
        <span style={s.catChip}>{a.tag} {a.category}</span>
      </div>
      <div style={s.cardBody}>
        <h3 style={s.cardTitle}>{a.title}</h3>
        <p style={s.cardExcerpt}>{a.excerpt}</p>
        <div style={s.cardMeta}>
          <span style={s.metaAuthor}>✍️ {a.author}</span>
          <span style={s.metaDot}>·</span>
          <span style={s.metaDate}>{a.date}</span>
          <span style={s.metaDot}>·</span>
          <span style={s.metaRead}>⏱ {a.readTime}</span>
        </div>
        <button style={s.readBtn}>Read Full Article →</button>
      </div>
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  hero:        { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 60%,#0e3a8c 100%)', color: '#fff', padding: '4rem 0 3rem' },
  heroInner:   { maxWidth: 700, margin: '0 auto', padding: '0 1.5rem', textAlign: 'center' },
  heroBadge:   { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600, marginBottom: 16 },
  heroH1:      { fontSize: 'clamp(26px,5vw,44px)', fontWeight: 900, margin: '0 0 12px', letterSpacing: '-1px', lineHeight: 1.15 },
  heroP:       { fontSize: 16, opacity: 0.8, marginBottom: 28, lineHeight: 1.6 },
  searchRow:   { display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.25)', borderRadius: 14, padding: '10px 18px', maxWidth: 500, margin: '0 auto' },
  heroInput:   { flex: 1, background: 'none', border: 'none', outline: 'none', color: '#fff', fontSize: 15, placeholder: '#aaa' },
  catBar:      { background: '#fff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 60, zIndex: 100, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' },
  catInner:    { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', overflowX: 'auto', gap: 4 },
  catBtn:      { background: 'none', border: 'none', padding: '12px 16px', fontSize: 13, fontWeight: 600, color: '#64748b', cursor: 'pointer', whiteSpace: 'nowrap', borderBottom: '3px solid transparent', transition: 'all 0.15s' },
  catActive:   { color: '#1a56db', borderBottom: '3px solid #1a56db' },
  wrap:        { maxWidth: 1240, margin: '0 auto', padding: '2.5rem 1.5rem' },
  sectionTitle:{ fontSize: 20, fontWeight: 800, color: '#0f172a', margin: '0 0 20px', letterSpacing: '-0.3px' },
  empty:       { textAlign: 'center', padding: '5rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 },
  card:        { background: '#fff', borderRadius: 18, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.04)', transition: 'all 0.25s cubic-bezier(.4,0,.2,1)', cursor: 'pointer', display: 'flex', flexDirection: 'column' },
  cardHover:   { transform: 'translateY(-4px)', boxShadow: '0 12px 40px rgba(0,0,0,0.12)' },
  cardFeatured:{ borderTop: '4px solid #1a56db' },
  imgWrap:     { position: 'relative', overflow: 'hidden' },
  img:         { width: '100%', height: 220, objectFit: 'cover', display: 'block' },
  catChip:     { position: 'absolute', top: 12, left: 12, background: 'rgba(15,23,42,0.75)', color: '#fff', borderRadius: 8, padding: '4px 12px', fontSize: 11, fontWeight: 700, backdropFilter: 'blur(4px)' },
  cardBody:    { padding: '20px', display: 'flex', flexDirection: 'column', gap: 10, flex: 1 },
  cardTitle:   { fontSize: 17, fontWeight: 800, color: '#0f172a', lineHeight: 1.35, margin: 0, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' },
  cardExcerpt: { fontSize: 13, color: '#64748b', lineHeight: 1.6, margin: 0, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden', flex: 1 },
  cardMeta:    { display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' },
  metaAuthor:  { fontSize: 12, color: '#374151', fontWeight: 600 },
  metaDate:    { fontSize: 12, color: '#94a3b8' },
  metaRead:    { fontSize: 12, color: '#94a3b8' },
  metaDot:     { color: '#d1d5db', fontSize: 12 },
  readBtn:     { background: '#eff6ff', color: '#1a56db', border: 'none', borderRadius: 8, padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', alignSelf: 'flex-start', marginTop: 'auto' },
  newsletter:  { background: 'linear-gradient(135deg,#0f172a,#1a56db)', borderRadius: 20, padding: '40px', marginTop: 56, display: 'flex', gap: 32, alignItems: 'center', flexWrap: 'wrap' },
  nlLeft:      { flex: 1, color: '#fff', minWidth: 220 },
  nlTitle:     { fontSize: 22, fontWeight: 900, margin: '0 0 8px', color: '#fff', letterSpacing: '-0.3px' },
  nlSub:       { fontSize: 14, opacity: 0.75, margin: 0 },
  nlRight:     { display: 'flex', gap: 10, flex: 1, minWidth: 220 },
  nlInput:     { flex: 1, border: 'none', borderRadius: 10, padding: '12px 16px', fontSize: 14, outline: 'none', background: 'rgba(255,255,255,0.15)', color: '#fff', backdropFilter: 'blur(4px)' },
  nlBtn:       { background: '#fff', color: '#1a56db', border: 'none', borderRadius: 10, padding: '12px 20px', fontSize: 14, fontWeight: 800, cursor: 'pointer', whiteSpace: 'nowrap', boxShadow: '0 2px 8px rgba(0,0,0,0.2)' },
}
