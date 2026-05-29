import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import PropertyCard, { PropertyCardSkeleton } from '../components/PropertyCard'
import SearchBar from '../components/SearchBar'
import { propertiesAPI } from '../services/api'
import { TEST_PROPERTIES } from '../data/testData'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useTimeGreeting } from '../hooks/useTimeGreeting'

const CITIES = ['All', 'Gurgaon', 'Noida', 'Delhi', 'Greater Noida', 'Faridabad', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune']

export default function Home() {
  const { tr } = useLang()
  const { isMobile, isTablet } = useBreakpoint()
  const greetKey = useTimeGreeting()
  const cols = isMobile ? '1fr' : isTablet ? 'repeat(2,1fr)' : 'repeat(auto-fill,minmax(300px,1fr))'
  const [searchParams] = useSearchParams()
  const [properties, setProperties] = useState([])
  const [loading, setLoading]       = useState(true)
  const [filters, setFilters]       = useState({
    search:      '',
    city:        'All',
    propType:    'All',
    listingType: searchParams.get('type') || 'all',
    minPrice:    '',
    maxPrice:    '',
    beds:        'Any',
  })

  const updateFilters = (partial) => setFilters(prev => ({ ...prev, ...partial }))

  useEffect(() => {
    propertiesAPI.list({ limit: 100 })
      .then(r => setProperties(r.data?.properties || r.data || []))
      .catch(() => setProperties(TEST_PROPERTIES))
      .finally(() => setLoading(false))
  }, [])

  const { search, city, propType, listingType, minPrice, maxPrice, beds } = filters

  const filtered = properties.filter(p => {
    if (search && !p.title?.toLowerCase().includes(search.toLowerCase()) &&
        !p.city?.toLowerCase().includes(search.toLowerCase()) &&
        !p.location?.toLowerCase().includes(search.toLowerCase()) &&
        !p.property_type?.toLowerCase().includes(search.toLowerCase())) return false
    if (city !== 'All' && p.city !== city) return false
    if (propType !== 'All' && p.property_type !== propType) return false
    if (listingType !== 'all' && p.listing_type !== listingType) return false
    if (minPrice && p.price < Number(minPrice)) return false
    if (maxPrice && p.price > Number(maxPrice)) return false
    if (beds !== 'Any' && p.bedrooms !== Number(beds)) return false
    return true
  })

  const featured  = filtered.filter(p => p.featured)
  const gurgaon   = filtered.filter(p => p.city === 'Gurgaon')
  const nearby    = filtered.filter(p => ['Noida','Greater Noida','Faridabad','Delhi'].includes(p.city))
  const others    = filtered.filter(p => !['Gurgaon','Noida','Greater Noida','Faridabad','Delhi'].includes(p.city))

  const QUICK_LINKS = [
    { icon: '🏠', label: 'Buy',             to: '/?type=sale' },
    { icon: '🔑', label: 'Rent',            to: '/?type=rent' },
    { icon: '🏗',  label: 'New Projects',    to: '/new-projects' },
    { icon: '🧑‍💼', label: 'Brokers',       to: '/brokers' },
    { icon: '💰', label: 'Home Loans',      to: '/finance' },
    { icon: '📊', label: 'Insights',        to: '/locality' },
    { icon: '✨', label: 'AI Tools',         to: '/ai-tools' },
    { icon: '⚖️', label: 'Compare',         to: '/compare' },
    { icon: '❤️', label: 'Wishlist',        to: '/wishlist' },
    { icon: '📋', label: 'CRM',             to: '/crm' },
  ]

  const FEATURES = [
    { icon: '🤖', title: 'AI-Powered Search',      desc: 'Voice search, smart filters, and ML-based property recommendations tailored to your preferences.' },
    { icon: '🏗',  title: '3D Model Generator',     desc: 'Visualize any property in 10 architecture styles using Google Imagen AI before you visit.' },
    { icon: '📊', title: 'Real-Time Analytics',    desc: 'Live price trends, demand heatmaps and locality scores for 50+ micro-markets across India.' },
    { icon: '📋', title: 'Built-in CRM',           desc: 'Full lead management pipeline with Kanban board, interaction history and auto lead scoring.' },
    { icon: '💬', title: 'WhatsApp Alerts',        desc: 'Instant price alerts, inquiry notifications and deal updates delivered to WhatsApp.' },
    { icon: '🔒', title: 'RERA Verified',          desc: 'Every listing is cross-checked against state RERA portals. Zero unverified developers.' },
  ]

  return (
    <div style={{ background: '#f9fafb', minHeight: '100vh' }}>

      {/* ─── Hero ─── */}
      <div style={s.hero}>
        <div style={s.greetBadge}>{tr(greetKey)} 👋</div>
        <h1 style={s.heroH1}>{tr('heroTitle')}</h1>
        <p style={s.heroP}>{tr('heroSub')}</p>
        <SearchBar filters={filters} onChange={updateFilters} />
        <div style={s.cityPills}>
          {CITIES.map(c => (
            <button key={c} onClick={() => updateFilters({ city: c })}
              style={{ ...s.pill, ...(city === c ? s.pillActive : {}) }}>{c}</button>
          ))}
        </div>
        {/* Trust badges */}
        <div style={s.trustRow}>
          {['✅ RERA Verified', '🔒 Secure Payments', '🏆 50,000+ Happy Buyers', '⭐ 4.8/5 Rating', '🤖 AI Powered'].map(b => (
            <span key={b} style={s.trustBadge}>{b}</span>
          ))}
        </div>
      </div>

      {/* ─── Stats Bar ─── */}
      <div style={s.statBar}>
        <div style={s.statWrap}>
          {[['15,000+', tr('activeListings')], ['10+', tr('citiesCovered')], ['50,000+', tr('happyBuyers')], ['₹50Cr+', tr('propertiesSold')], ['4.8★', 'Avg Rating'], ['99%', 'RERA Verified']].map(([v, l]) => (
            <div key={l} style={s.stat}>
              <span style={s.statVal}>{v}</span>
              <span style={s.statLabel}>{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ─── Quick Links ─── */}
      <div style={s.quickWrap}>
        <div style={s.quickInner}>
          {QUICK_LINKS.map(ql => (
            <Link key={ql.label} to={ql.to} style={s.quickLink}>
              <div style={s.quickIcon}>{ql.icon}</div>
              <span style={s.quickLabel}>{ql.label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* ─── Properties ─── */}
      <div style={s.main}>
        {loading ? (
          <div style={s.grid}>{Array(6).fill(0).map((_, i) => <PropertyCardSkeleton key={i} />)}</div>
        ) : filtered.length === 0 ? (
          <div style={s.empty}>{tr('noResults')}</div>
        ) : (
          <>
            {featured.length > 0 && <Section title={tr('featured')}    items={featured} cols={cols} />}
            {gurgaon.length  > 0 && <Section title={tr('gurgaon')}     items={gurgaon}  cols={cols} />}
            {nearby.length   > 0 && <Section title={tr('nearby')}      items={nearby}   cols={cols} />}
            {others.length   > 0 && <Section title={tr('otherCities')} items={others}   cols={cols} />}
            {featured.length === 0 && gurgaon.length === 0 && nearby.length === 0 && others.length === 0 && (
              <Section title="All Properties" items={filtered} cols={cols} />
            )}
          </>
        )}
      </div>

      {/* ─── Virtual Tour CTA ─── */}
      <div style={s.ctaSection}>
        <div style={s.ctaInner}>
          <div>
            <div style={s.ctaBadge}>🏗 AI-Powered 3D Visualization</div>
            <h2 style={s.ctaH2}>See Your Dream Home<br />Before You Visit</h2>
            <p style={s.ctaSub}>Generate photorealistic 3D renders of any property in 10 architecture styles — Modern, Luxury, Minimalist and more — in under 3 seconds.</p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Link to="/ai-tools" style={s.ctaBtn}>✨ Try AI 3D Generator</Link>
              <Link to="/new-projects" style={s.ctaBtnOutline}>🏗 New Projects</Link>
            </div>
          </div>
          <div style={s.ctaImgWrap}>
            <img src="https://picsum.photos/seed/cta_home/600/400" alt="3D render" style={s.ctaImg} />
            <div style={s.ctaImgBadge}>⚡ Generated in 2.3s</div>
          </div>
        </div>
      </div>

      {/* ─── Feature Highlights ─── */}
      <div style={s.featuresWrap}>
        <div style={s.featuresInner}>
          <h2 style={s.featuresTitle}>Why PropertyYards?</h2>
          <p style={s.featuresSub}>India's most feature-rich real estate platform — built for buyers, sellers and brokers</p>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : isTablet ? 'repeat(2,1fr)' : 'repeat(3,1fr)', gap: 24 }}>
            {FEATURES.map(f => (
              <div key={f.title} style={s.featureCard}>
                <div style={s.featureIcon}>{f.icon}</div>
                <div style={s.featureTitle}>{f.title}</div>
                <div style={s.featureDesc}>{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Rewards CTA ─── */}
      <div style={s.rewardsBanner}>
        <div style={s.rewardsInner}>
          <div style={{ fontSize: 48 }}>🎁</div>
          <div style={{ flex: 1 }}>
            <h3 style={s.rewardsH3}>Earn Rewards on Every Action</h3>
            <p style={s.rewardsSub}>Get points for inquiries, referrals and listings. Redeem as Amazon gift cards, cashback or wallet credits.</p>
          </div>
          <Link to="/rewards" style={s.rewardsBtn}>View Rewards →</Link>
        </div>
      </div>

    </div>
  )
}

function Section({ title, items, cols }) {
  return (
    <div style={{ marginBottom: '3rem' }}>
      <h2 style={s.sectionTitle}>{title} <span style={s.count}>({items.length})</span></h2>
      <div style={{ ...s.grid, gridTemplateColumns: cols }}>
        {items.map(p => <PropertyCard key={p.id || p._id} property={p} />)}
      </div>
    </div>
  )
}

const s = {
  hero:          { background: 'linear-gradient(135deg, #0f172a 0%, #1a56db 60%, #0e3a8c 100%)', padding: '5rem 2rem 3rem', textAlign: 'center', color: '#fff' },
  greetBadge:    { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600, marginBottom: 16, backdropFilter: 'blur(4px)' },
  heroH1:        { fontSize: 'clamp(28px, 5vw, 50px)', fontWeight: 900, margin: '0 0 0.75rem', letterSpacing: '-1.5px', lineHeight: 1.1 },
  heroP:         { fontSize: 18, opacity: 0.85, margin: '0 0 2rem' },
  cityPills:     { display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap', marginTop: 20 },
  pill:          { background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.25)', color: '#fff', padding: '6px 18px', borderRadius: 20, fontSize: 14, cursor: 'pointer', transition: 'all 0.15s' },
  pillActive:    { background: '#fff', color: '#1a56db', fontWeight: 700 },
  trustRow:      { display: 'flex', justifyContent: 'center', gap: 10, flexWrap: 'wrap', marginTop: 24 },
  trustBadge:    { background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: 20, padding: '5px 14px', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.9)' },
  statBar:       { background: '#fff', borderBottom: '1px solid #e2e8f0', boxShadow: '0 1px 8px rgba(0,0,0,0.05)' },
  statWrap:      { maxWidth: 1240, margin: '0 auto', padding: '0 1rem', display: 'flex', justifyContent: 'space-around', height: 76, alignItems: 'center', flexWrap: 'wrap', gap: 0 },
  stat:          { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, padding: '0 8px' },
  statVal:       { fontSize: 20, fontWeight: 800, color: '#1a56db', letterSpacing: '-0.5px' },
  statLabel:     { fontSize: 11, color: '#64748b', fontWeight: 500 },
  quickWrap:     { background: '#fff', borderBottom: '1px solid #f1f5f9', padding: '0' },
  quickInner:    { maxWidth: 1240, margin: '0 auto', padding: '16px 1.5rem', display: 'flex', gap: 8, overflowX: 'auto', justifyContent: 'center', flexWrap: 'wrap' },
  quickLink:     { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, textDecoration: 'none', minWidth: 70, padding: '10px 6px', borderRadius: 14, transition: 'background 0.15s', cursor: 'pointer' },
  quickIcon:     { width: 48, height: 48, borderRadius: 14, background: 'linear-gradient(135deg,#eff6ff,#f5f3ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' },
  quickLabel:    { fontSize: 11, fontWeight: 700, color: '#374151', textAlign: 'center' },
  main:          { maxWidth: 1240, margin: '0 auto', padding: '3rem 1.5rem' },
  sectionTitle:  { fontSize: 24, fontWeight: 700, marginBottom: '1.2rem', color: '#111827' },
  count:         { fontSize: 16, color: '#6b7280', fontWeight: 400 },
  grid:          { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 },
  empty:         { textAlign: 'center', fontSize: 16, padding: '4rem', color: '#9ca3af' },
  ctaSection:    { background: 'linear-gradient(135deg,#0f172a,#1e1b4b)', padding: '5rem 1.5rem', color: '#fff' },
  ctaInner:      { maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(300px,1fr))', gap: 48, alignItems: 'center' },
  ctaBadge:      { display: 'inline-block', background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 700, marginBottom: 16 },
  ctaH2:         { fontSize: 'clamp(26px,4vw,40px)', fontWeight: 900, margin: '0 0 16px', letterSpacing: '-0.5px', lineHeight: 1.2 },
  ctaSub:        { fontSize: 15, opacity: 0.8, lineHeight: 1.7, marginBottom: 28 },
  ctaBtn:        { background: 'linear-gradient(135deg,#7c3aed,#1a56db)', color: '#fff', textDecoration: 'none', borderRadius: 12, padding: '13px 24px', fontSize: 14, fontWeight: 800, boxShadow: '0 4px 16px rgba(124,58,237,0.4)' },
  ctaBtnOutline: { background: 'rgba(255,255,255,0.1)', color: '#fff', textDecoration: 'none', borderRadius: 12, padding: '13px 24px', fontSize: 14, fontWeight: 700, border: '1px solid rgba(255,255,255,0.25)' },
  ctaImgWrap:    { position: 'relative' },
  ctaImg:        { width: '100%', borderRadius: 20, boxShadow: '0 24px 80px rgba(0,0,0,0.5)', display: 'block' },
  ctaImgBadge:   { position: 'absolute', bottom: 16, right: 16, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', color: '#fff', borderRadius: 20, padding: '6px 14px', fontSize: 12, fontWeight: 700 },
  featuresWrap:  { background: '#f8fafc', padding: '5rem 1.5rem' },
  featuresInner: { maxWidth: 1100, margin: '0 auto' },
  featuresTitle: { fontSize: 'clamp(24px,4vw,36px)', fontWeight: 900, color: '#0f172a', textAlign: 'center', marginBottom: 10, letterSpacing: '-0.5px' },
  featuresSub:   { fontSize: 16, color: '#64748b', textAlign: 'center', marginBottom: 40 },
  featureCard:   { background: '#fff', borderRadius: 18, padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 1px 8px rgba(0,0,0,0.04)', transition: 'transform 0.2s, box-shadow 0.2s' },
  featureIcon:   { fontSize: 36, marginBottom: 14 },
  featureTitle:  { fontSize: 16, fontWeight: 800, color: '#0f172a', marginBottom: 8 },
  featureDesc:   { fontSize: 14, color: '#64748b', lineHeight: 1.7 },
  rewardsBanner: { background: 'linear-gradient(135deg,#7c3aed,#1a56db)', padding: '3rem 1.5rem' },
  rewardsInner:  { maxWidth: 1100, margin: '0 auto', display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' },
  rewardsH3:     { fontSize: 'clamp(18px,3vw,24px)', fontWeight: 900, color: '#fff', margin: '0 0 8px' },
  rewardsSub:    { fontSize: 14, color: 'rgba(255,255,255,0.8)', margin: 0 },
  rewardsBtn:    { background: '#fff', color: '#7c3aed', textDecoration: 'none', borderRadius: 12, padding: '12px 24px', fontSize: 14, fontWeight: 800, whiteSpace: 'nowrap', flexShrink: 0 },
}
