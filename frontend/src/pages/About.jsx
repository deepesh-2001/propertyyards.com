import { useBreakpoint } from '../hooks/useBreakpoint'
import { Link } from 'react-router-dom'

const TEAM = [
  { name: 'Deepesh Gupta',    role: 'Founder & CEO',        avatar: 'D', g: ['#1a56db','#7c3aed'], bio: '10+ years in real estate tech. Previously at Housing.com & 99acres.' },
  { name: 'Priya Sharma',     role: 'Head of Product',      avatar: 'P', g: ['#059669','#0284c7'], bio: 'Ex-Flipkart PM. Passionate about making property search seamless.' },
  { name: 'Arjun Mehta',      role: 'CTO',                  avatar: 'A', g: ['#dc2626','#f59e0b'], bio: 'Full-stack architect with expertise in distributed systems and ML.' },
  { name: 'Sneha Patel',      role: 'Head of Operations',   avatar: 'S', g: ['#7c3aed','#ec4899'], bio: 'Runs partnerships with 500+ RERA-verified brokers across India.' },
]

const MILESTONES = [
  { year: '2020', title: 'Founded', desc: 'PropertyYards launched with 100 listings in Gurgaon.' },
  { year: '2021', title: 'Series A', desc: 'Raised ₹12 Cr. Expanded to 5 cities, 5,000 listings.' },
  { year: '2022', title: 'AI Launch', desc: 'Introduced AI-powered property descriptions and smart search.' },
  { year: '2023', title: '50K Users', desc: 'Crossed 50,000 active users. Launched Finance & Insurance.' },
  { year: '2024', title: 'Multi-Lingual', desc: 'Added 6 Indian languages. Expanded to 10+ cities.' },
  { year: '2025', title: 'Today',    desc: '15,000+ listings · ₹50Cr+ properties sold · 500+ brokers.' },
]

const VALUES = [
  { icon: '🔍', title: 'Transparency',  desc: 'Every listing is verified. No hidden fees, no fake properties.' },
  { icon: '🤝', title: 'Trust',         desc: 'RERA-certified brokers only. Your investment is safe with us.' },
  { icon: '⚡', title: 'Speed',         desc: 'AI-powered search. Find your ideal home in under 2 minutes.' },
  { icon: '🌍', title: 'Inclusivity',   desc: 'Available in 6 languages so every Indian can find a home.' },
]

export default function About() {
  const { isMobile } = useBreakpoint()

  return (
    <div style={s.page}>
      {/* Hero */}
      <div style={s.hero}>
        <div style={s.heroInner}>
          <div style={s.heroBadge}>🏠 About PropertyYards</div>
          <h1 style={s.heroH1}>India's Most Trusted<br />Property Platform</h1>
          <p style={s.heroP}>
            We're on a mission to make finding, buying, and renting property simple, transparent, and accessible for every Indian family.
          </p>
          <div style={s.heroStats}>
            {[['15K+','Active Listings'],['50K+','Happy Users'],['500+','Verified Brokers'],['10+','Cities']].map(([v,l]) => (
              <div key={l} style={s.hStat}>
                <span style={s.hStatV}>{v}</span>
                <span style={s.hStatL}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mission */}
      <div style={s.section}>
        <div style={s.sectionInner}>
          <div style={{ ...s.twoCol, gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr' }}>
            <div>
              <div style={s.label}>OUR MISSION</div>
              <h2 style={s.h2}>Making Real Estate<br />Accessible for All</h2>
              <p style={s.para}>
                PropertyYards was born from a simple frustration — finding a home in India was broken. Listings were fake, brokers were unverified, and the process was opaque. We set out to fix that.
              </p>
              <p style={s.para}>
                Today, we connect millions of homebuyers, renters, and sellers with RERA-certified agents, AI-verified listings, and transparent pricing — all in one place.
              </p>
              <div style={{ display: 'flex', gap: 12, marginTop: 24, flexWrap: 'wrap' }}>
                <Link to="/" style={s.primaryBtn}>Browse Properties →</Link>
                <Link to="/brokers" style={s.outlineBtn}>Meet Our Brokers</Link>
              </div>
            </div>
            <div style={s.imgBox}>
              <img src="https://picsum.photos/seed/aboutmission/600/400" alt="Mission" style={s.missionImg} />
              <div style={s.imgOverlay}>
                <div style={s.imgBadge}>🏆 #1 Property Platform in India</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Values */}
      <div style={{ ...s.section, background: '#f8fafc' }}>
        <div style={s.sectionInner}>
          <div style={s.centerHeader}>
            <div style={s.label}>WHAT WE STAND FOR</div>
            <h2 style={s.h2}>Our Core Values</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)', gap: 20, marginTop: 32 }}>
            {VALUES.map(v => (
              <div key={v.title} style={s.valueCard}>
                <span style={s.valueIcon}>{v.icon}</span>
                <div>
                  <div style={s.valueTitle}>{v.title}</div>
                  <div style={s.valueDesc}>{v.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div style={s.section}>
        <div style={s.sectionInner}>
          <div style={s.centerHeader}>
            <div style={s.label}>OUR JOURNEY</div>
            <h2 style={s.h2}>From Startup to India's<br />Trusted Platform</h2>
          </div>
          <div style={s.timeline}>
            {MILESTONES.map((m, i) => (
              <div key={m.year} style={{ ...s.tlItem, flexDirection: isMobile || i % 2 === 0 ? 'row' : 'row-reverse' }}>
                <div style={s.tlCard}>
                  <div style={s.tlTitle}>{m.title}</div>
                  <div style={s.tlDesc}>{m.desc}</div>
                </div>
                <div style={s.tlDot}>
                  <div style={s.tlYear}>{m.year}</div>
                </div>
                {!isMobile && <div style={{ flex: 1 }} />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team */}
      <div style={{ ...s.section, background: '#f8fafc' }}>
        <div style={s.sectionInner}>
          <div style={s.centerHeader}>
            <div style={s.label}>THE TEAM</div>
            <h2 style={s.h2}>People Behind PropertyYards</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap: 24, marginTop: 32 }}>
            {TEAM.map(m => (
              <div key={m.name} style={s.teamCard}>
                <div style={{ ...s.teamAvatar, background: `linear-gradient(135deg,${m.g[0]},${m.g[1]})` }}>{m.avatar}</div>
                <div style={s.teamName}>{m.name}</div>
                <div style={s.teamRole}>{m.role}</div>
                <div style={s.teamBio}>{m.bio}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div style={s.cta}>
        <h2 style={{ fontSize: 'clamp(22px,4vw,36px)', fontWeight: 900, color: '#fff', margin: '0 0 12px', letterSpacing: '-0.5px' }}>
          Ready to Find Your Dream Home?
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 16, marginBottom: 28 }}>
          Join 50,000+ happy homebuyers and renters on PropertyYards.
        </p>
        <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/register" style={s.ctaBtn}>Get Started Free →</Link>
          <Link to="/finance"  style={s.ctaOutline}>Explore Finance</Link>
        </div>
      </div>
    </div>
  )
}

const s = {
  page:         { background: '#fff', minHeight: '100vh' },
  hero:         { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 60%,#0e3a8c 100%)', color: '#fff', padding: '5rem 0' },
  heroInner:    { maxWidth: 860, margin: '0 auto', padding: '0 1.5rem', textAlign: 'center' },
  heroBadge:    { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600, marginBottom: 20 },
  heroH1:       { fontSize: 'clamp(28px,5vw,50px)', fontWeight: 900, margin: '0 0 16px', letterSpacing: '-1.5px', lineHeight: 1.1 },
  heroP:        { fontSize: 18, opacity: 0.85, marginBottom: 36, lineHeight: 1.6 },
  heroStats:    { display: 'flex', justifyContent: 'center', gap: 40, flexWrap: 'wrap' },
  hStat:        { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 },
  hStatV:       { fontSize: 28, fontWeight: 900, letterSpacing: '-1px' },
  hStatL:       { fontSize: 12, opacity: 0.7 },
  section:      { padding: '5rem 0' },
  sectionInner: { maxWidth: 1100, margin: '0 auto', padding: '0 1.5rem' },
  label:        { fontSize: 11, fontWeight: 800, letterSpacing: 2, color: '#1a56db', textTransform: 'uppercase', marginBottom: 8 },
  h2:           { fontSize: 'clamp(24px,4vw,38px)', fontWeight: 900, color: '#0f172a', margin: '0 0 20px', letterSpacing: '-0.5px', lineHeight: 1.2 },
  para:         { fontSize: 16, color: '#374151', lineHeight: 1.75, marginBottom: 16 },
  twoCol:       { display: 'grid', gap: 48, alignItems: 'center' },
  imgBox:       { position: 'relative', borderRadius: 20, overflow: 'hidden' },
  missionImg:   { width: '100%', height: 360, objectFit: 'cover', display: 'block' },
  imgOverlay:   { position: 'absolute', bottom: 16, left: 16 },
  imgBadge:     { background: 'rgba(0,0,0,0.7)', color: '#fff', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, backdropFilter: 'blur(8px)' },
  primaryBtn:   { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', padding: '12px 24px', borderRadius: 12, fontWeight: 700, textDecoration: 'none', fontSize: 15, boxShadow: '0 4px 14px rgba(26,86,219,0.35)' },
  outlineBtn:   { background: '#fff', color: '#1a56db', padding: '12px 24px', borderRadius: 12, fontWeight: 700, textDecoration: 'none', fontSize: 15, border: '2px solid #1a56db' },
  centerHeader: { textAlign: 'center' },
  valueCard:    { display: 'flex', gap: 16, alignItems: 'flex-start', background: '#fff', borderRadius: 16, padding: '24px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  valueIcon:    { fontSize: 32, flexShrink: 0 },
  valueTitle:   { fontSize: 17, fontWeight: 800, color: '#0f172a', marginBottom: 6 },
  valueDesc:    { fontSize: 14, color: '#64748b', lineHeight: 1.6 },
  timeline:     { display: 'flex', flexDirection: 'column', gap: 0, marginTop: 40, position: 'relative' },
  tlItem:       { display: 'flex', gap: 20, alignItems: 'center', marginBottom: 28 },
  tlCard:       { flex: 1, background: '#f8fafc', borderRadius: 14, padding: '18px 20px', border: '1px solid #e2e8f0' },
  tlTitle:      { fontSize: 16, fontWeight: 800, color: '#0f172a', marginBottom: 4 },
  tlDesc:       { fontSize: 14, color: '#64748b', lineHeight: 1.5 },
  tlDot:        { width: 64, height: 64, borderRadius: '50%', background: 'linear-gradient(135deg,#1a56db,#7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 4px 14px rgba(26,86,219,0.3)' },
  tlYear:       { color: '#fff', fontWeight: 900, fontSize: 14, letterSpacing: '-0.3px' },
  teamCard:     { background: '#fff', borderRadius: 18, padding: '24px 20px', border: '1px solid #e2e8f0', textAlign: 'center', boxShadow: '0 1px 4px rgba(0,0,0,0.04)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 },
  teamAvatar:   { width: 72, height: 72, borderRadius: '50%', color: '#fff', fontSize: 28, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 4, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' },
  teamName:     { fontSize: 16, fontWeight: 800, color: '#0f172a' },
  teamRole:     { fontSize: 12, color: '#1a56db', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 },
  teamBio:      { fontSize: 12, color: '#64748b', lineHeight: 1.5, marginTop: 4 },
  cta:          { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', padding: '5rem 1.5rem', textAlign: 'center' },
  ctaBtn:       { background: '#fff', color: '#1a56db', padding: '14px 28px', borderRadius: 12, fontWeight: 800, textDecoration: 'none', fontSize: 16, boxShadow: '0 4px 14px rgba(0,0,0,0.2)' },
  ctaOutline:   { background: 'transparent', color: '#fff', padding: '14px 28px', borderRadius: 12, fontWeight: 700, textDecoration: 'none', fontSize: 16, border: '2px solid rgba(255,255,255,0.5)' },
}
