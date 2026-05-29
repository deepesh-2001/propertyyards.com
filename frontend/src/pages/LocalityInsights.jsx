import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'

const LOCALITIES = {
  Gurgaon: {
    avgPrice: 12500, priceChange: +14.2, rentYield: 3.8,
    trend: [8200, 8900, 9800, 10200, 10900, 11400, 12000, 12500],
    months: ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May'],
    score: { safety: 78, connectivity: 88, schools: 82, hospitals: 75, markets: 90 },
    nearby: {
      schools:   [{ name: 'DPS Sector 45', dist: '0.8 km', rating: 4.7 }, { name: 'The Shriram Millennium', dist: '1.2 km', rating: 4.5 }, { name: 'GD Goenka World School', dist: '2.1 km', rating: 4.6 }],
      hospitals: [{ name: 'Medanta Hospital', dist: '1.5 km', rating: 4.8 }, { name: 'Fortis Memorial', dist: '2.3 km', rating: 4.6 }, { name: 'Max Hospital', dist: '3.1 km', rating: 4.4 }],
      metro:     [{ name: 'Cyber City Metro', dist: '0.6 km' }, { name: 'MG Road Metro', dist: '1.4 km' }, { name: 'IFFCO Chowk', dist: '2.0 km' }],
      malls:     [{ name: 'Ambience Mall', dist: '1.1 km' }, { name: 'DLF Mall of India', dist: '3.2 km' }, { name: 'Cyberhub', dist: '0.9 km' }],
    },
    overview: 'Gurgaon (Gurugram) is India\'s leading corporate hub with Fortune 500 companies, premium malls, and excellent connectivity via Delhi Metro and NH-48.',
  },
  Noida: {
    avgPrice: 8400, priceChange: +11.5, rentYield: 4.1,
    trend: [5800, 6200, 6700, 7100, 7600, 7900, 8100, 8400],
    months: ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May'],
    score: { safety: 72, connectivity: 84, schools: 79, hospitals: 70, markets: 83 },
    nearby: {
      schools:   [{ name: 'Amity International', dist: '1.2 km', rating: 4.6 }, { name: 'Lotus Valley', dist: '0.9 km', rating: 4.4 }, { name: 'Ryan International', dist: '1.8 km', rating: 4.3 }],
      hospitals: [{ name: 'Jaypee Hospital', dist: '2.1 km', rating: 4.5 }, { name: 'Felix Hospital', dist: '1.4 km', rating: 4.3 }, { name: 'Kailash Hospital', dist: '2.8 km', rating: 4.2 }],
      metro:     [{ name: 'Sector 18 Metro', dist: '0.5 km' }, { name: 'Sector 62 Metro', dist: '1.3 km' }, { name: 'Botanical Garden', dist: '2.1 km' }],
      malls:     [{ name: 'The Great India Place', dist: '0.7 km' }, { name: 'DLF Mall Noida', dist: '1.5 km' }, { name: 'Logix City Centre', dist: '2.2 km' }],
    },
    overview: 'Noida is a planned IT/ITES hub offering great value for money with wide roads, green spaces, and seamless metro connectivity to Delhi.',
  },
  Mumbai: {
    avgPrice: 28600, priceChange: +9.8, rentYield: 2.9,
    trend: [22000, 23500, 24200, 25100, 26000, 26800, 27500, 28600],
    months: ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May'],
    score: { safety: 74, connectivity: 95, schools: 88, hospitals: 85, markets: 96 },
    nearby: {
      schools:   [{ name: 'Dhirubhai Ambani International', dist: '1.8 km', rating: 4.9 }, { name: 'Cathedral & John Connon', dist: '3.2 km', rating: 4.8 }, { name: 'Bombay Scottish', dist: '2.1 km', rating: 4.7 }],
      hospitals: [{ name: 'Lilavati Hospital', dist: '1.2 km', rating: 4.8 }, { name: 'Kokilaben Dhirubhai', dist: '2.4 km', rating: 4.7 }, { name: 'Breach Candy Hospital', dist: '3.0 km', rating: 4.6 }],
      metro:     [{ name: 'Andheri Metro', dist: '0.4 km' }, { name: 'BKC Metro Line 3', dist: '1.1 km' }, { name: 'Bandra Station', dist: '1.8 km' }],
      malls:     [{ name: 'Palladium Mall', dist: '0.8 km' }, { name: 'Phoenix Marketcity', dist: '1.6 km' }, { name: 'High Street Phoenix', dist: '0.9 km' }],
    },
    overview: 'Mumbai is India\'s financial capital with unparalleled connectivity, the best schools and hospitals, and a vibrant lifestyle — commanding a premium in property prices.',
  },
  Bangalore: {
    avgPrice: 9800, priceChange: +16.3, rentYield: 4.4,
    trend: [6200, 6800, 7200, 7800, 8300, 8800, 9200, 9800],
    months: ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May'],
    score: { safety: 76, connectivity: 80, schools: 85, hospitals: 82, markets: 87 },
    nearby: {
      schools:   [{ name: 'National Public School', dist: '1.0 km', rating: 4.7 }, { name: 'Inventure Academy', dist: '1.5 km', rating: 4.6 }, { name: 'TISB International', dist: '2.0 km', rating: 4.8 }],
      hospitals: [{ name: 'Manipal Hospital', dist: '1.8 km', rating: 4.7 }, { name: 'Apollo Bangalore', dist: '2.5 km', rating: 4.6 }, { name: 'Sakra World Hospital', dist: '1.2 km', rating: 4.5 }],
      metro:     [{ name: 'Whitefield Metro', dist: '0.7 km' }, { name: 'Marathahalli Junction', dist: '1.4 km' }, { name: 'Bellandur Metro', dist: '2.2 km' }],
      malls:     [{ name: 'Phoenix Marketcity', dist: '1.3 km' }, { name: 'VR Bengaluru', dist: '2.1 km' }, { name: 'Orion East', dist: '3.0 km' }],
    },
    overview: 'Bangalore\'s tech corridors (Whitefield, Koramangala, HSR Layout) are seeing the highest price appreciation in India, driven by strong IT demand and quality of life.',
  },
}

const SCORE_LABELS = { safety: '🔒 Safety', connectivity: '🚇 Connectivity', schools: '🏫 Schools', hospitals: '🏥 Hospitals', markets: '🛒 Markets' }

export default function LocalityInsights() {
  const { isMobile, isTablet } = useBreakpoint()
  const [city, setCity] = useState('Gurgaon')
  const [activeTab, setActiveTab] = useState('overview')
  const d = LOCALITIES[city]

  const maxTrend = Math.max(...d.trend)
  const minTrend = Math.min(...d.trend)
  const chartH   = 120

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <div style={s.heroBadge}>📊 Locality Insights</div>
            <h1 style={s.h1}>Make Data-Driven<br />Property Decisions</h1>
            <p style={s.sub}>Price trends · Schools · Hospitals · Metro · Safety scores</p>
          </div>
        </div>
      </div>

      <div style={s.wrap}>
        {/* City selector */}
        <div style={s.cityRow}>
          {Object.keys(LOCALITIES).map(c => (
            <button key={c} onClick={() => setCity(c)}
              style={{ ...s.cityBtn, ...(city === c ? s.cityActive : {}) }}>
              {c}
            </button>
          ))}
        </div>

        {/* Top metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap: 16, marginBottom: 28 }}>
          <MetricCard icon="💰" label="Avg Price (₹/sq ft)" val={`₹${d.avgPrice.toLocaleString('en-IN')}`} sub="May 2025" color="#1a56db" />
          <MetricCard icon="📈" label="YoY Appreciation" val={`+${d.priceChange}%`} sub="vs last year" color="#059669" />
          <MetricCard icon="🏘" label="Rental Yield" val={`${d.rentYield}%`} sub="Annual gross yield" color="#7c3aed" />
          <MetricCard icon="🏆" label="Livability Score" val={`${Math.round(Object.values(d.score).reduce((a,b)=>a+b,0)/Object.values(d.score).length)}/100`} sub="Composite score" color="#f59e0b" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : isTablet ? '1fr' : '1fr 380px', gap: 24 }}>
          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

            {/* Price trend chart */}
            <div style={s.card}>
              <h2 style={s.cardTitle}>📈 Price Trend (₹/sq ft)</h2>
              <div style={s.chartWrap}>
                <svg viewBox={`0 0 ${d.trend.length * 80} ${chartH + 30}`} style={{ width: '100%', height: chartH + 30 }}>
                  {d.trend.map((v, i) => {
                    const x = i * 80 + 40
                    const barH = ((v - minTrend) / (maxTrend - minTrend + 1000)) * chartH
                    const y   = chartH - barH
                    return (
                      <g key={i}>
                        <rect x={x - 22} y={y} width={44} height={barH}
                          fill={i === d.trend.length - 1 ? '#1a56db' : '#bfdbfe'} rx={6} />
                        <text x={x} y={chartH + 20} textAnchor="middle" fontSize={11} fill="#94a3b8">{d.months[i]}</text>
                        <text x={x} y={y - 6} textAnchor="middle" fontSize={10} fill="#374151" fontWeight="700">
                          {(v/1000).toFixed(0)}K
                        </text>
                      </g>
                    )
                  })}
                </svg>
              </div>
              <div style={s.chartFooter}>
                <span style={{ color: '#059669', fontWeight: 800 }}>↑ {d.priceChange}% growth</span>
                &nbsp;in the last 8 months · Current: <strong>₹{d.avgPrice.toLocaleString('en-IN')}/sq ft</strong>
              </div>
            </div>

            {/* Livability scores */}
            <div style={s.card}>
              <h2 style={s.cardTitle}>🏆 Livability Scores</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {Object.entries(d.score).map(([k, v]) => (
                  <div key={k}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{SCORE_LABELS[k]}</span>
                      <span style={{ fontSize: 14, fontWeight: 800, color: v >= 85 ? '#059669' : v >= 70 ? '#f59e0b' : '#dc2626' }}>{v}/100</span>
                    </div>
                    <div style={s.scoreBar}>
                      <div style={{ ...s.scoreFill, width: `${v}%`, background: v >= 85 ? '#059669' : v >= 70 ? '#f59e0b' : '#dc2626' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Overview */}
            <div style={s.card}>
              <h2 style={s.cardTitle}>🗺 About {city}</h2>
              <p style={{ fontSize: 15, color: '#374151', lineHeight: 1.75, margin: 0 }}>{d.overview}</p>
            </div>
          </div>

          {/* Right column: Nearby */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Tabs */}
            <div style={s.tabRow}>
              {[['schools','🏫 Schools'],['hospitals','🏥 Hospitals'],['metro','🚇 Metro'],['malls','🛒 Malls']].map(([key, label]) => (
                <button key={key} onClick={() => setActiveTab(key)}
                  style={{ ...s.tab, ...(activeTab === key ? s.tabActive : {}) }}>{label}</button>
              ))}
            </div>

            <div style={s.card}>
              <h2 style={s.cardTitle}>
                {activeTab === 'schools' && '🏫 Nearby Schools'}
                {activeTab === 'hospitals' && '🏥 Nearby Hospitals'}
                {activeTab === 'metro' && '🚇 Metro Stations'}
                {activeTab === 'malls' && '🛒 Shopping & Markets'}
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {d.nearby[activeTab].map((item, i) => (
                  <div key={i} style={s.nearbyRow}>
                    <div style={s.nearbyIcon}>
                      {activeTab === 'schools' ? '🏫' : activeTab === 'hospitals' ? '🏥' : activeTab === 'metro' ? '🚇' : '🛒'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={s.nearbyName}>{item.name}</div>
                      <div style={s.nearbyDist}>📍 {item.dist}</div>
                    </div>
                    {item.rating && (
                      <div style={s.nearbyRating}>⭐ {item.rating}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Investment verdict */}
            <div style={s.verdictCard}>
              <div style={s.verdictTitle}>💡 Investment Verdict</div>
              <div style={s.verdictBody}>
                {city} shows <strong style={{ color: '#059669' }}>strong appreciation (+{d.priceChange}%)</strong> with a rental yield of <strong>{d.rentYield}%</strong>.
                {d.rentYield >= 4
                  ? ' Excellent for both end-use and investment.'
                  : ' Better suited for capital appreciation than rental income.'}
              </div>
              <div style={s.verdictTags}>
                {d.priceChange > 12 && <span style={s.verdictTag}>🔥 High Growth</span>}
                {d.rentYield >= 4  && <span style={s.verdictTag}>💰 Good Yield</span>}
                {d.score.connectivity >= 85 && <span style={s.verdictTag}>🚇 Well Connected</span>}
                {d.score.schools >= 80 && <span style={s.verdictTag}>🏫 Good Schools</span>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, val, sub, color }) {
  return (
    <div style={{ background: '#fff', borderRadius: 16, padding: '20px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
      <div style={{ fontSize: 24, marginBottom: 8 }}>{icon}</div>
      <div style={{ fontSize: 24, fontWeight: 900, color, letterSpacing: '-0.5px', lineHeight: 1 }}>{val}</div>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', marginTop: 4 }}>{label}</div>
      <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{sub}</div>
    </div>
  )
}

const s = {
  page:         { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:       { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '3rem 0' },
  bannerInner:  { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem' },
  heroBadge:    { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 700, marginBottom: 12 },
  h1:           { fontSize: 'clamp(22px,4vw,38px)', fontWeight: 900, margin: '0 0 8px', letterSpacing: '-0.5px', lineHeight: 1.2 },
  sub:          { fontSize: 14, opacity: 0.7 },
  wrap:         { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  cityRow:      { display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' },
  cityBtn:      { background: '#fff', border: '1.5px solid #e2e8f0', borderRadius: 12, padding: '9px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', color: '#374151', transition: 'all 0.15s' },
  cityActive:   { background: 'linear-gradient(135deg,#1a56db,#2563eb)', border: '1.5px solid #1a56db', color: '#fff', boxShadow: '0 4px 12px rgba(26,86,219,0.3)' },
  card:         { background: '#fff', borderRadius: 18, padding: '24px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:    { fontSize: 18, fontWeight: 800, color: '#0f172a', margin: '0 0 18px', letterSpacing: '-0.3px' },
  chartWrap:    { marginBottom: 10 },
  chartFooter:  { fontSize: 13, color: '#64748b', textAlign: 'center' },
  scoreBar:     { height: 10, background: '#f1f5f9', borderRadius: 99, overflow: 'hidden' },
  scoreFill:    { height: '100%', borderRadius: 99, transition: 'width 0.5s' },
  tabRow:       { display: 'flex', gap: 4, flexWrap: 'wrap' },
  tab:          { background: '#fff', border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '7px 14px', fontSize: 12, fontWeight: 700, cursor: 'pointer', color: '#64748b', transition: 'all 0.15s' },
  tabActive:    { background: '#eff6ff', border: '1.5px solid #1a56db', color: '#1a56db' },
  nearbyRow:    { display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f1f5f9' },
  nearbyIcon:   { fontSize: 22, flexShrink: 0 },
  nearbyName:   { fontSize: 14, fontWeight: 700, color: '#0f172a' },
  nearbyDist:   { fontSize: 12, color: '#64748b', marginTop: 2 },
  nearbyRating: { fontSize: 13, fontWeight: 800, color: '#f59e0b', flexShrink: 0 },
  verdictCard:  { background: 'linear-gradient(135deg,#f0fdf4,#eff6ff)', border: '1px solid #bbf7d0', borderRadius: 18, padding: '22px' },
  verdictTitle: { fontSize: 16, fontWeight: 800, color: '#0f172a', marginBottom: 10 },
  verdictBody:  { fontSize: 14, color: '#374151', lineHeight: 1.7, marginBottom: 14 },
  verdictTags:  { display: 'flex', gap: 8, flexWrap: 'wrap' },
  verdictTag:   { background: '#fff', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 700, color: '#065f46' },
}
