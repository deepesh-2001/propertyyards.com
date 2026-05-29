import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'

const MONTHS = ['Nov','Dec','Jan','Feb','Mar','Apr','May']
const TRAFFIC  = [18400, 22100, 26800, 24200, 31500, 36800, 42300]
const LEADS    = [310, 420, 510, 465, 620, 710, 840]
const REVENUE  = [1.2, 1.8, 2.1, 1.9, 2.6, 3.1, 3.8]
const LISTINGS = [980, 1100, 1320, 1290, 1540, 1780, 1920]

const TOP_CITIES = [
  { city: 'Gurgaon',   visits: 14200, leads: 310, conv: 8.2, color: '#1a56db' },
  { city: 'Noida',     visits: 10800, leads: 248, conv: 7.4, color: '#7c3aed' },
  { city: 'Mumbai',    visits: 9400,  leads: 195, conv: 6.1, color: '#059669' },
  { city: 'Bangalore', visits: 8700,  leads: 212, conv: 9.1, color: '#f59e0b' },
  { city: 'Hyderabad', visits: 5200,  leads: 118, conv: 5.8, color: '#dc2626' },
]

const TOP_PROPS = [
  { title: 'Godrej Horizon 3BHK',        views: 4821, inquiries: 142, city: 'Gurgaon' },
  { title: 'DLF The Arbour Penthouse',   views: 3940, inquiries: 98,  city: 'Gurgaon' },
  { title: 'Prestige Nautilus 2BHK',     views: 3102, inquiries: 87,  city: 'Bangalore' },
  { title: 'Lodha Bellagio 4BHK',        views: 2864, inquiries: 74,  city: 'Mumbai' },
  { title: 'Brigade Utopia 3BHK',        views: 2510, inquiries: 61,  city: 'Bangalore' },
]

const SOURCES = [
  { label: 'Organic Search', pct: 42, color: '#1a56db' },
  { label: 'Direct',         pct: 23, color: '#7c3aed' },
  { label: 'Paid Ads',       pct: 18, color: '#f59e0b' },
  { label: 'Social Media',   pct: 11, color: '#059669' },
  { label: 'Referral',       pct: 6,  color: '#dc2626' },
]

function BarChart({ data, labels, color, unit = '', height = 140 }) {
  const max = Math.max(...data)
  return (
    <svg viewBox={`0 0 ${labels.length * 72} ${height + 28}`} style={{ width: '100%', height: height + 28 }}>
      {data.map((v, i) => {
        const barH = (v / max) * height
        const x    = i * 72 + 36
        return (
          <g key={i}>
            <rect x={x - 24} y={height - barH} width={48} height={barH}
              fill={i === data.length - 1 ? color : `${color}66`} rx={6} />
            <text x={x} y={height + 18} textAnchor="middle" fontSize={11} fill="#94a3b8">{labels[i]}</text>
            <text x={x} y={height - barH - 5} textAnchor="middle" fontSize={10} fill="#374151" fontWeight="700">
              {unit === 'Cr' ? `₹${v}Cr` : unit === 'K' ? `${(v/1000).toFixed(0)}K` : v}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

export default function Analytics() {
  const { isMobile } = useBreakpoint()
  const [period, setPeriod] = useState('7M')

  const kpis = [
    { icon: '👁', label: 'Total Visits',    val: '42,300',  change: '+15.1%', up: true,  color: '#1a56db' },
    { icon: '📋', label: 'Leads Generated', val: '840',     change: '+18.3%', up: true,  color: '#7c3aed' },
    { icon: '💰', label: 'Revenue (Cr)',     val: '₹3.8 Cr', change: '+22.5%', up: true,  color: '#059669' },
    { icon: '🏠', label: 'Active Listings', val: '1,920',   change: '+7.8%',  up: true,  color: '#f59e0b' },
    { icon: '📈', label: 'Conversion Rate', val: '1.99%',   change: '+0.3%',  up: true,  color: '#0284c7' },
    { icon: '⏱', label: 'Avg Session',      val: '4m 32s',  change: '+12s',   up: true,  color: '#dc2626' },
  ]

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>📊 Analytics Dashboard</h1>
            <p style={s.sub}>Real-time insights · Traffic · Leads · Revenue · Conversions</p>
          </div>
          <div style={s.periodRow}>
            {['7M','30D','90D','1Y'].map(p => (
              <button key={p} onClick={() => setPeriod(p)}
                style={{ ...s.periodBtn, ...(period === p ? s.periodActive : {}) }}>{p}</button>
            ))}
          </div>
        </div>
      </div>

      <div style={s.wrap}>
        {/* KPI cards */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2,1fr)' : 'repeat(3,1fr)', gap: 16, marginBottom: 28 }}>
          {kpis.map(k => (
            <div key={k.label} style={{ ...s.kpiCard, borderTop: `4px solid ${k.color}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <span style={{ fontSize: 24 }}>{k.icon}</span>
                <span style={{ ...s.changeBadge, background: k.up ? '#d1fae5' : '#fee2e2', color: k.up ? '#065f46' : '#991b1b' }}>
                  {k.up ? '↑' : '↓'} {k.change}
                </span>
              </div>
              <div style={{ fontSize: 26, fontWeight: 900, color: k.color, letterSpacing: '-0.5px', marginTop: 8 }}>{k.val}</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4, fontWeight: 600 }}>{k.label}</div>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 24, marginBottom: 24 }}>
          <div style={s.card}>
            <h3 style={s.cardTitle}>👁 Monthly Traffic</h3>
            <BarChart data={TRAFFIC} labels={MONTHS} color="#1a56db" unit="K" />
          </div>
          <div style={s.card}>
            <h3 style={s.cardTitle}>📋 Leads Generated</h3>
            <BarChart data={LEADS} labels={MONTHS} color="#7c3aed" />
          </div>
          <div style={s.card}>
            <h3 style={s.cardTitle}>💰 Revenue (₹ Cr)</h3>
            <BarChart data={REVENUE} labels={MONTHS} color="#059669" unit="Cr" />
          </div>
          <div style={s.card}>
            <h3 style={s.cardTitle}>🏠 Active Listings</h3>
            <BarChart data={LISTINGS} labels={MONTHS} color="#f59e0b" />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 24 }}>
          {/* Traffic Sources */}
          <div style={s.card}>
            <h3 style={s.cardTitle}>🌐 Traffic Sources</h3>
            {SOURCES.map(src => (
              <div key={src.label} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{src.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 800, color: src.color }}>{src.pct}%</span>
                </div>
                <div style={s.bar}>
                  <div style={{ ...s.barFill, width: `${src.pct}%`, background: src.color }} />
                </div>
              </div>
            ))}
          </div>

          {/* Top Cities */}
          <div style={s.card}>
            <h3 style={s.cardTitle}>🏙 Top Cities</h3>
            {TOP_CITIES.map((c, i) => (
              <div key={c.city} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: `${c.color}22`, color: c.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 13 }}>{i+1}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{c.city}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>{c.visits.toLocaleString()} visits · {c.leads} leads</div>
                </div>
                <span style={{ ...s.convBadge, color: c.conv >= 8 ? '#059669' : '#f59e0b' }}>{c.conv}%</span>
              </div>
            ))}
          </div>

          {/* Top Properties */}
          <div style={s.card}>
            <h3 style={s.cardTitle}>🏆 Top Properties</h3>
            {TOP_PROPS.map((p, i) => (
              <div key={p.title} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: i < TOP_PROPS.length-1 ? '1px solid #f1f5f9' : 'none' }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', marginBottom: 3, display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.title}</div>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 5 }}>📍 {p.city}</div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <span style={s.metaChip}>👁 {p.views.toLocaleString()}</span>
                  <span style={{ ...s.metaChip, background: '#d1fae5', color: '#065f46' }}>📩 {p.inquiries}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Heatmap placeholder */}
        <div style={{ ...s.card, marginTop: 24 }}>
          <h3 style={s.cardTitle}>🗺 Geographic Heatmap — User Activity by City</h3>
          <div style={s.heatmap}>
            {TOP_CITIES.map(c => (
              <div key={c.city} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{ width: Math.round(40 + c.visits/700), height: Math.round(40 + c.visits/700), borderRadius: '50%', background: `${c.color}44`, border: `3px solid ${c.color}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                  <span style={{ fontSize: 11, fontWeight: 900, color: c.color }}>{(c.visits/1000).toFixed(0)}K</span>
                </div>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>{c.city}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:      { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '2rem 0' },
  bannerInner: { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 },
  h1:          { fontSize: 'clamp(20px,3vw,28px)', fontWeight: 900, margin: 0 },
  sub:         { fontSize: 13, opacity: 0.75, marginTop: 4 },
  periodRow:   { display: 'flex', gap: 4, background: 'rgba(255,255,255,0.1)', borderRadius: 10, padding: 4 },
  periodBtn:   { background: 'none', border: 'none', color: 'rgba(255,255,255,0.7)', borderRadius: 8, padding: '6px 14px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  periodActive:{ background: '#fff', color: '#1a56db' },
  wrap:        { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  kpiCard:     { background: '#fff', borderRadius: 16, padding: '20px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  changeBadge: { borderRadius: 20, padding: '3px 10px', fontSize: 11, fontWeight: 800 },
  card:        { background: '#fff', borderRadius: 18, padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:   { fontSize: 16, fontWeight: 800, color: '#0f172a', margin: '0 0 18px', letterSpacing: '-0.3px' },
  bar:         { height: 8, background: '#f1f5f9', borderRadius: 99, overflow: 'hidden' },
  barFill:     { height: '100%', borderRadius: 99 },
  convBadge:   { fontSize: 13, fontWeight: 900 },
  metaChip:    { background: '#eff6ff', color: '#1d4ed8', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 },
  heatmap:     { display: 'flex', gap: 40, justifyContent: 'center', alignItems: 'flex-end', padding: '20px 0', flexWrap: 'wrap' },
}
