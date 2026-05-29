import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'

const PROJECTS = [
  {
    id: 'np1', name: 'Godrej Horizon', developer: 'Godrej Properties', city: 'Gurgaon', location: 'Sector 85, Gurgaon',
    type: 'Residential Apartments', units: 480, launched: '2024-01', possession: 'Dec 2027',
    priceFrom: 9200000, priceTo: 18500000, area: '1,150 – 2,400 sq ft',
    progress: 32, status: 'Under Construction', rera: 'RERA/GGN/2024/0182',
    images: ['https://picsum.photos/seed/np1/800/500'], amenities: ['Clubhouse','Swimming Pool','Gym','Jogging Track','Kids Play Area','Amphitheatre'],
    badge: '🔥 Hot', badgeColor: '#dc2626', description: '3 & 4 BHK luxury apartments with panoramic Aravalli views. IGBC Gold certified green building.',
    config: ['3 BHK – 1,150 sq ft','4 BHK – 1,850 sq ft','4.5 BHK – 2,400 sq ft'],
  },
  {
    id: 'np2', name: 'DLF The Arbour', developer: 'DLF Limited', city: 'Gurgaon', location: 'Sector 63, Gurgaon',
    type: 'Luxury Apartments', units: 1137, launched: '2023-09', possession: 'Jun 2028',
    priceFrom: 17500000, priceTo: 35000000, area: '3,500 – 6,500 sq ft',
    progress: 18, status: 'Under Construction', rera: 'RERA/GGN/2023/0341',
    images: ['https://picsum.photos/seed/np2/800/500'], amenities: ['Golf Course View','Concierge','Spa','Infinity Pool','Yoga Deck','Business Lounge'],
    badge: '⭐ Premium', badgeColor: '#7c3aed', description: 'Ultra-luxury 4 & 5 BHK residences set amidst 30 acres of curated greens. DLF\'s most exclusive offering.',
    config: ['4 BHK – 3,500 sq ft','5 BHK – 5,000 sq ft','Penthouse – 6,500 sq ft'],
  },
  {
    id: 'np3', name: 'Prestige Nautilus', developer: 'Prestige Group', city: 'Bangalore', location: 'Hebbal, Bangalore',
    type: 'High-Rise Apartments', units: 650, launched: '2024-03', possession: 'Mar 2027',
    priceFrom: 8800000, priceTo: 15200000, area: '1,200 – 2,100 sq ft',
    progress: 45, status: 'Under Construction', rera: 'RERA/KAR/2024/0091',
    images: ['https://picsum.photos/seed/np3/800/500'], amenities: ['Lake View','Rooftop Lounge','Co-working Space','EV Charging','Pet Park','Sky Garden'],
    badge: '🆕 New Launch', badgeColor: '#059669', description: '2 & 3 BHK smart homes with stunning Hebbal Lake views. IoT-enabled apartments with Alexa integration.',
    config: ['2 BHK – 1,200 sq ft','3 BHK – 1,650 sq ft','3.5 BHK – 2,100 sq ft'],
  },
  {
    id: 'np4', name: 'Lodha Bellagio', developer: 'Lodha Group', city: 'Mumbai', location: 'Powai, Mumbai',
    type: 'Mixed-Use Towers', units: 924, launched: '2023-11', possession: 'Sep 2026',
    priceFrom: 22000000, priceTo: 55000000, area: '1,800 – 4,200 sq ft',
    progress: 62, status: 'Nearing Completion', rera: 'RERA/MH/2023/0782',
    images: ['https://picsum.photos/seed/np4/800/500'], amenities: ['Private Pool','Helipad','Concierge','Fine Dining','Cinema','Wine Cellar'],
    badge: '✅ RERA Approved', badgeColor: '#0284c7', description: 'Iconic twin towers on the Powai lakefront. Signature ultra-luxury residences by Lodha.',
    config: ['3 BHK – 1,800 sq ft','4 BHK – 2,800 sq ft','Penthouse – 4,200 sq ft'],
  },
  {
    id: 'np5', name: 'Sobha City', developer: 'Sobha Developers', city: 'Hyderabad', location: 'Gachibowli, Hyderabad',
    type: 'Integrated Township', units: 1840, launched: '2024-06', possession: 'Dec 2028',
    priceFrom: 6500000, priceTo: 12000000, area: '1,000 – 2,000 sq ft',
    progress: 8, status: 'Pre-Launch', rera: 'Pending', 
    images: ['https://picsum.photos/seed/np5/800/500'], amenities: ['School','Hospital','Mall','Sports Academy','Temple','Metro Connectivity'],
    badge: '🚀 Pre-Launch', badgeColor: '#f59e0b', description: '200-acre integrated township with residences, schools, hospitals, retail and office spaces.',
    config: ['2 BHK – 1,000 sq ft','3 BHK – 1,450 sq ft','4 BHK – 2,000 sq ft'],
  },
  {
    id: 'np6', name: 'Puravankara Zenium', developer: 'Puravankara', city: 'Pune', location: 'Hinjewadi, Pune',
    type: 'IT Corridor Apartments', units: 710, launched: '2024-02', possession: 'Jun 2027',
    priceFrom: 5800000, priceTo: 9500000, area: '950 – 1,650 sq ft',
    progress: 38, status: 'Under Construction', rera: 'RERA/MH/2024/0231',
    images: ['https://picsum.photos/seed/np6/800/500'], amenities: ['Coworking Hub','Gym','Cricket Ground','Creche','Salon','EV Parking'],
    badge: '💼 IT Hub', badgeColor: '#1a56db', description: 'Premium residences next to Hinjewadi IT Park. Perfect for tech professionals.',
    config: ['2 BHK – 950 sq ft','2.5 BHK – 1,200 sq ft','3 BHK – 1,650 sq ft'],
  },
]

const CITIES = ['All', ...new Set(PROJECTS.map(p => p.city))]
const STATUSES = ['All', 'Pre-Launch', 'Under Construction', 'Nearing Completion']

export default function NewProjects() {
  const { isMobile, isTablet } = useBreakpoint()
  const [city,   setCity]   = useState('All')
  const [status, setStatus] = useState('All')
  const [open,   setOpen]   = useState(null)

  const filtered = PROJECTS.filter(p =>
    (city === 'All' || p.city === city) &&
    (status === 'All' || p.status === status)
  )

  const cols = isMobile ? '1fr' : isTablet ? 'repeat(2,1fr)' : 'repeat(3,1fr)'

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <div style={s.heroBadge}>🏗 New Projects 2024–2025</div>
            <h1 style={s.h1}>Fresh Launches & Under-<br />Construction Properties</h1>
            <p style={s.sub}>Pre-launch prices · RERA certified · Top developers</p>
          </div>
          <div style={s.bannerStats}>
            {[['6+','Active Projects'],['₹50K Cr+','Total GDV'],['4,700+','Units Available'],['6','Cities']].map(([v,l]) => (
              <div key={l} style={s.bStat}><span style={s.bStatV}>{v}</span><span style={s.bStatL}>{l}</span></div>
            ))}
          </div>
        </div>
      </div>

      <div style={s.wrap}>
        {/* Filters */}
        <div style={s.filtersRow}>
          {CITIES.map(c => (
            <button key={c} onClick={() => setCity(c)}
              style={{ ...s.filterChip, ...(city === c ? s.filterActive : {}) }}>{c}</button>
          ))}
          <div style={s.separator} />
          {STATUSES.map(st => (
            <button key={st} onClick={() => setStatus(st)}
              style={{ ...s.filterChip, ...(status === st ? s.filterActive : {}) }}>{st}</button>
          ))}
        </div>

        <div style={s.resultCount}>{filtered.length} project{filtered.length !== 1 ? 's' : ''} found</div>

        <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 28 }}>
          {filtered.map(proj => (
            <ProjectCard key={proj.id} proj={proj} open={open === proj.id} onToggle={() => setOpen(open === proj.id ? null : proj.id)} />
          ))}
        </div>
      </div>
    </div>
  )
}

function ProjectCard({ proj, open, onToggle }) {
  const [hovered, setHovered] = useState(false)
  const progressColor = proj.progress < 20 ? '#f59e0b' : proj.progress < 50 ? '#3b82f6' : '#059669'

  return (
    <div style={{ ...s.card, ...(hovered ? s.cardHover : {}) }}
      onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>
      <div style={s.imgWrap}>
        <img src={proj.images[0]} alt={proj.name} style={s.img}
          onError={e => { e.target.src = `https://picsum.photos/seed/fallback${proj.id}/800/500` }} />
        <span style={{ ...s.badge, background: proj.badgeColor }}>{proj.badge}</span>
        <span style={s.reraChip}>{proj.rera === 'Pending' ? '⏳ RERA Pending' : '✓ RERA'}</span>
      </div>

      <div style={s.body}>
        <div style={s.developer}>{proj.developer}</div>
        <h3 style={s.name}>{proj.name}</h3>
        <div style={s.location}>📍 {proj.location}</div>

        {/* Progress bar */}
        <div style={s.progressWrap}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>Construction Progress</span>
            <span style={{ fontSize: 12, fontWeight: 800, color: progressColor }}>{proj.progress}%</span>
          </div>
          <div style={s.progressBar}>
            <div style={{ ...s.progressFill, width: `${proj.progress}%`, background: progressColor }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>Launched {proj.launched}</span>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>Possession {proj.possession}</span>
          </div>
        </div>

        <div style={s.priceRow}>
          <div>
            <div style={s.priceLabel}>Starting From</div>
            <div style={s.price}>₹{(proj.priceFrom / 10000000).toFixed(1)} Cr</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={s.priceLabel}>Area Range</div>
            <div style={s.areaText}>{proj.area}</div>
          </div>
        </div>

        {/* Config chips */}
        <div style={s.configRow}>
          {proj.config.map(c => <span key={c} style={s.configChip}>{c}</span>)}
        </div>

        <button onClick={onToggle} style={s.detailToggle}>
          {open ? '▲ Hide Details' : '▼ View Details'}
        </button>

        {open && (
          <div style={s.details} className="fade-in">
            <p style={s.desc}>{proj.description}</p>
            <div style={s.amenGrid}>
              {proj.amenities.map(a => <span key={a} style={s.amenChip}>✓ {a}</span>)}
            </div>
            <div style={s.ctaRow}>
              <button style={s.enquireBtn}>📞 Enquire Now</button>
              <button style={s.brochureBtn}>📄 Download Brochure</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const s = {
  page:         { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:       { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '3rem 0' },
  bannerInner:  { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 24 },
  heroBadge:    { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 700, marginBottom: 12 },
  h1:           { fontSize: 'clamp(22px,4vw,36px)', fontWeight: 900, margin: '0 0 8px', letterSpacing: '-0.5px', lineHeight: 1.2 },
  sub:          { fontSize: 14, opacity: 0.7 },
  bannerStats:  { display: 'flex', gap: 28, flexWrap: 'wrap' },
  bStat:        { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 },
  bStatV:       { fontSize: 22, fontWeight: 900, letterSpacing: '-0.5px' },
  bStatL:       { fontSize: 11, opacity: 0.7 },
  wrap:         { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  filtersRow:   { display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' },
  filterChip:   { background: '#fff', border: '1.5px solid #e2e8f0', borderRadius: 20, padding: '6px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', color: '#374151', transition: 'all 0.15s' },
  filterActive: { background: '#eff6ff', border: '1.5px solid #1a56db', color: '#1a56db' },
  separator:    { width: 1, height: 24, background: '#e2e8f0', flexShrink: 0 },
  resultCount:  { fontSize: 13, color: '#64748b', marginBottom: 20, fontWeight: 500 },
  card:         { background: '#fff', borderRadius: 20, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.05)', transition: 'all 0.25s' },
  cardHover:    { transform: 'translateY(-4px)', boxShadow: '0 16px 48px rgba(0,0,0,0.12)' },
  imgWrap:      { position: 'relative' },
  img:          { width: '100%', height: 220, objectFit: 'cover', display: 'block' },
  badge:        { position: 'absolute', top: 12, left: 12, color: '#fff', borderRadius: 8, padding: '4px 12px', fontSize: 12, fontWeight: 800 },
  reraChip:     { position: 'absolute', bottom: 12, right: 12, background: 'rgba(5,150,105,0.9)', color: '#fff', borderRadius: 8, padding: '3px 10px', fontSize: 11, fontWeight: 700, backdropFilter: 'blur(4px)' },
  body:         { padding: '20px' },
  developer:    { fontSize: 11, fontWeight: 800, color: '#1a56db', textTransform: 'uppercase', letterSpacing: 1 },
  name:         { fontSize: 20, fontWeight: 900, color: '#0f172a', margin: '4px 0 6px', letterSpacing: '-0.3px' },
  location:     { fontSize: 13, color: '#64748b', marginBottom: 14 },
  progressWrap: { marginBottom: 16 },
  progressBar:  { height: 8, background: '#f1f5f9', borderRadius: 99, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 99, transition: 'width 0.5s' },
  priceRow:     { display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', borderRadius: 12, padding: '12px 14px', marginBottom: 12 },
  priceLabel:   { fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 },
  price:        { fontSize: 22, fontWeight: 900, color: '#1a56db', letterSpacing: '-0.5px' },
  areaText:     { fontSize: 14, fontWeight: 700, color: '#0f172a' },
  configRow:    { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 },
  configChip:   { background: '#eff6ff', color: '#1d4ed8', borderRadius: 8, padding: '3px 10px', fontSize: 11, fontWeight: 700 },
  detailToggle: { background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 16px', fontSize: 13, fontWeight: 700, color: '#64748b', cursor: 'pointer', width: '100%' },
  details:      { marginTop: 16, borderTop: '1px solid #f1f5f9', paddingTop: 16 },
  desc:         { fontSize: 13, color: '#374151', lineHeight: 1.65, marginBottom: 12 },
  amenGrid:     { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 },
  amenChip:     { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', borderRadius: 20, padding: '3px 10px', fontSize: 11, fontWeight: 600 },
  ctaRow:       { display: 'flex', gap: 8 },
  enquireBtn:   { flex: 1, background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 10, padding: '11px', fontSize: 13, fontWeight: 800, cursor: 'pointer' },
  brochureBtn:  { background: '#f8fafc', border: '1.5px solid #e2e8f0', color: '#374151', borderRadius: 10, padding: '11px 14px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
}
