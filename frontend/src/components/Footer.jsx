import { Link } from 'react-router-dom'

const LINKS = {
  'Explore': [
    { label: '🏠 Buy Property',      to: '/?type=sale' },
    { label: '🔑 Rent Property',     to: '/?type=rent' },
    { label: '🏗 New Projects',      to: '/new-projects' },
    { label: '🧑‍💼 Find Brokers',   to: '/brokers' },
    { label: '💰 Finance & Loans',   to: '/finance' },
    { label: '📊 Locality Insights', to: '/locality' },
    { label: '📰 News & Insights',   to: '/news' },
  ],
  'Quick Links': [
    { label: '📝 Post Your Property', to: '/post-property' },
    { label: '📊 My Dashboard',       to: '/dashboard' },
    { label: '❤️ Wishlist',           to: '/wishlist' },
    { label: '⚖️ Compare',            to: '/compare' },
    { label: '💳 Payments & Wallet',  to: '/payments' },
    { label: '🎁 Rewards',            to: '/rewards' },
    { label: '🔔 Notifications',      to: '/notifications' },
    { label: '⭐ Feedback',           to: '/feedback' },
  ],
  'Tools & Pro': [
    { label: '📋 CRM',                to: '/crm' },
    { label: '✨ AI Tools',           to: '/ai-tools' },
    { label: '📈 Analytics',          to: '/analytics' },
    { label: '📱 Social Media',       to: '/social-media' },
    { label: '⚙️ Admin Portal',       to: '/admin' },
  ],
  'Company': [
    { label: '🏢 About Us',      to: '/about' },
    { label: '📞 Contact Us',    to: '/contact' },
    { label: '🤝 Careers',       to: '/about' },
    { label: '📣 Press',         to: '/news' },
    { label: '🔒 Privacy Policy',to: '/contact' },
  ],
  'Cities': [
    { label: '🏙 Gurgaon',         to: '/' },
    { label: '🌆 Noida',           to: '/' },
    { label: '🌇 Mumbai',          to: '/' },
    { label: '🌃 Bangalore',       to: '/' },
    { label: '🌉 Hyderabad',       to: '/' },
  ],
}

export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer style={s.footer}>
      <div style={s.top}>
        <div style={s.brand}>
          <div style={s.logo}>🏠 PropertyYards</div>
          <p style={s.tagline}>
            India's most trusted platform for buying, selling and renting property. RERA-verified brokers, AI-powered search, and finance solutions — all in one place.
          </p>
          <div style={s.socialRow}>
            {['📘','📸','🐦','💼','📺','💬'].map((icon, i) => (
              <button key={i} style={s.socialBtn} title="Social">{icon}</button>
            ))}
          </div>
          <div style={s.appRow}>
            <div style={s.appBtn}>📱 App Store</div>
            <div style={s.appBtn}>🤖 Google Play</div>
          </div>
        </div>

        <div style={s.linksGrid}>
          {Object.entries(LINKS).map(([section, links]) => (
            <div key={section} style={s.linkCol}>
              <div style={s.colTitle}>{section}</div>
              {links.map(({ label, to }) => (
                <Link key={label} to={to} style={s.link}>{label}</Link>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div style={s.divider} />

      <div style={s.bottom}>
        <div style={s.bottomLeft}>
          <span>© {year} PropertyYards. All rights reserved.</span>
          <span style={s.dot}>·</span>
          <span>RERA Certified Platform</span>
          <span style={s.dot}>·</span>
          <span>Made with ❤️ in India</span>
        </div>
        <div style={s.bottomRight}>
          <span style={s.badge}>🔒 SSL Secured</span>
          <span style={s.badge}>✅ RERA Verified</span>
          <span style={s.badge}>🤖 AI Powered</span>
        </div>
      </div>
    </footer>
  )
}

const s = {
  footer:     { background: '#0f172a', color: '#e2e8f0', padding: '4rem 0 0' },
  top:        { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem 3rem', display: 'grid', gridTemplateColumns: '280px 1fr', gap: 48, flexWrap: 'wrap' },
  brand:      { display: 'flex', flexDirection: 'column', gap: 16 },
  logo:       { fontSize: 22, fontWeight: 900, color: '#fff', letterSpacing: '-0.5px' },
  tagline:    { fontSize: 13, color: '#94a3b8', lineHeight: 1.7, margin: 0 },
  socialRow:  { display: 'flex', gap: 8, flexWrap: 'wrap' },
  socialBtn:  { background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '7px 10px', fontSize: 16, cursor: 'pointer', color: '#e2e8f0' },
  appRow:     { display: 'flex', gap: 10, flexWrap: 'wrap' },
  appBtn:     { background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, color: '#e2e8f0', cursor: 'pointer' },
  linksGrid:  { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(150px,1fr))', gap: 32 },
  linkCol:    { display: 'flex', flexDirection: 'column', gap: 10 },
  colTitle:   { fontSize: 12, fontWeight: 800, color: '#fff', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 4 },
  link:       { fontSize: 13, color: '#94a3b8', textDecoration: 'none', transition: 'color 0.15s', lineHeight: 1.4 },
  divider:    { borderTop: '1px solid rgba(255,255,255,0.08)', margin: '0 1.5rem' },
  bottom:     { maxWidth: 1240, margin: '0 auto', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 },
  bottomLeft: { fontSize: 12, color: '#64748b', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' },
  dot:        { color: '#334155' },
  bottomRight:{ display: 'flex', gap: 8, flexWrap: 'wrap' },
  badge:      { background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 20, padding: '4px 12px', fontSize: 11, fontWeight: 700, color: '#94a3b8' },
}
