import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { TEST_PROPERTIES } from '../data/testData'
import { formatPrice } from '../components/PropertyCard'
import { getWishlist } from './Wishlist'
import { useBreakpoint } from '../hooks/useBreakpoint'

const MAX = 4

const ROWS = [
  { key: 'price',          label: 'Price',           fmt: (v,p) => formatPrice(v, p.listing_type) },
  { key: 'area',           label: 'Area (sq ft)',     fmt: v => `${v} sq ft` },
  { key: 'bedrooms',       label: 'Bedrooms',         fmt: v => v || '—' },
  { key: 'bathrooms',      label: 'Bathrooms',        fmt: v => v || '—' },
  { key: 'property_type',  label: 'Property Type',    fmt: v => v || '—' },
  { key: 'listing_type',   label: 'Listing',          fmt: v => v === 'rent' ? 'For Rent' : 'For Sale' },
  { key: 'furnished',      label: 'Furnished',        fmt: v => v == null ? '—' : v ? 'Yes' : 'No' },
  { key: 'pets_allowed',   label: 'Pets Allowed',     fmt: v => v == null ? '—' : v ? 'Yes' : 'No' },
  { key: 'city',           label: 'City',             fmt: v => v || '—' },
  { key: 'state',          label: 'State',            fmt: v => v || '—' },
  { key: 'deposit_amount', label: 'Security Deposit', fmt: v => v ? `₹${Number(v).toLocaleString('en-IN')}` : '—' },
  { key: 'amenities',      label: 'Amenities',        fmt: v => Array.isArray(v) && v.length ? `${v.length} amenities` : '—' },
]

function bestIdx(props, key) {
  if (!props.length) return -1
  if (key === 'price') {
    const min = Math.min(...props.map(p => p.price))
    return props.findIndex(p => p.price === min)
  }
  if (key === 'area') {
    const max = Math.max(...props.map(p => p.area || 0))
    return props.findIndex(p => (p.area || 0) === max)
  }
  if (key === 'amenities') {
    const max = Math.max(...props.map(p => p.amenities?.length || 0))
    return props.findIndex(p => (p.amenities?.length || 0) === max)
  }
  return -1
}

export default function Compare() {
  const { isMobile } = useBreakpoint()
  const [selected, setSelected] = useState([])
  const [picker,   setPicker]   = useState(false)

  const wishlistIds = getWishlist()
  const wishlistProps = TEST_PROPERTIES.filter(p => wishlistIds.includes(p.id))
  const allProps      = TEST_PROPERTIES

  const addProperty = (p) => {
    if (selected.length >= MAX) return
    if (selected.find(s => s.id === p.id)) return
    setSelected(prev => [...prev, p])
    setPicker(false)
  }
  const remove = (id) => setSelected(prev => prev.filter(p => p.id !== id))

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>⚖️ Compare Properties</h1>
            <p style={s.sub}>Side-by-side comparison of up to {MAX} properties</p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {selected.length < MAX && (
              <button onClick={() => setPicker(true)} style={s.addBtn}>+ Add Property</button>
            )}
            {selected.length > 0 && (
              <button onClick={() => setSelected([])} style={s.clearBtn}>🗑 Clear All</button>
            )}
          </div>
        </div>
      </div>

      {/* Property picker modal */}
      {picker && (
        <div style={s.overlay} onClick={() => setPicker(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()} className="fade-in">
            <div style={s.modalHeader}>
              <h3 style={s.modalTitle}>Select a Property to Compare</h3>
              <button onClick={() => setPicker(false)} style={s.modalClose}>✕</button>
            </div>
            {wishlistProps.length > 0 && (
              <div style={s.modalSection}>⭐ From Your Wishlist</div>
            )}
            <div style={s.pickerGrid}>
              {(wishlistProps.length > 0 ? wishlistProps : allProps).map(p => (
                <button
                  key={p.id}
                  onClick={() => addProperty(p)}
                  disabled={!!selected.find(s => s.id === p.id)}
                  style={{ ...s.pickerCard, ...(selected.find(s => s.id === p.id) ? s.pickerDisabled : {}) }}
                >
                  <img src={p.images?.[0] || `https://picsum.photos/seed/${p.id}/120/80`} alt="" style={s.pickerImg} />
                  <div style={s.pickerInfo}>
                    <div style={s.pickerTitle}>{p.title}</div>
                    <div style={s.pickerPrice}>{formatPrice(p.price, p.listing_type)}</div>
                    <div style={s.pickerCity}>📍 {p.city}</div>
                  </div>
                  {selected.find(s => s.id === p.id) && <span style={s.pickerAdded}>✓ Added</span>}
                </button>
              ))}
            </div>
            {wishlistProps.length === 0 && (
              <div style={s.modalHint}>
                💡 <Link to="/wishlist" style={{ color: '#1a56db' }}>Save properties to your wishlist</Link> for quick access here.
              </div>
            )}
          </div>
        </div>
      )}

      <div style={s.wrap}>
        {selected.length === 0 ? (
          <div style={s.empty}>
            <div style={{ fontSize: 64 }}>⚖️</div>
            <h2 style={s.emptyTitle}>Compare Properties Side by Side</h2>
            <p style={s.emptySub}>Add up to 4 properties to see a detailed comparison of price, area, amenities, and more.</p>
            <button onClick={() => setPicker(true)} style={s.browseBtn}>+ Add Your First Property</button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={s.table}>
              <thead>
                <tr>
                  <th style={s.th}>Feature</th>
                  {selected.map(p => (
                    <th key={p.id} style={s.th}>
                      <div style={s.colHeader}>
                        <img src={p.images?.[0] || `https://picsum.photos/seed/${p.id}/240/160`} alt="" style={s.colImg} />
                        <div style={s.colTitle}>{p.title}</div>
                        <div style={s.colCity}>📍 {p.city}</div>
                        <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginTop: 8 }}>
                          <Link to={`/property/${p.id}`} style={s.viewBtn}>View →</Link>
                          <button onClick={() => remove(p.id)} style={s.removeColBtn}>✕</button>
                        </div>
                      </div>
                    </th>
                  ))}
                  {selected.length < MAX && (
                    <th style={{ ...s.th, minWidth: 180 }}>
                      <button onClick={() => setPicker(true)} style={s.addColBtn}>
                        <span style={{ fontSize: 28 }}>＋</span>
                        <span style={{ fontSize: 13 }}>Add Property</span>
                      </button>
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row, ri) => {
                  const best = bestIdx(selected, row.key)
                  return (
                    <tr key={row.key} style={ri % 2 === 0 ? s.rowEven : {}}>
                      <td style={s.rowLabel}>{row.label}</td>
                      {selected.map((p, ci) => (
                        <td key={p.id} style={{ ...s.cell, ...(ci === best ? s.bestCell : {}) }}>
                          {row.fmt(p[row.key], p)}
                          {ci === best && <span style={s.bestBadge}>✓ Best</span>}
                        </td>
                      ))}
                      {selected.length < MAX && <td style={s.cell} />}
                    </tr>
                  )
                })}
                {/* Amenities detail row */}
                <tr>
                  <td style={s.rowLabel}>All Amenities</td>
                  {selected.map(p => (
                    <td key={p.id} style={s.cell}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, justifyContent: 'center' }}>
                        {p.amenities?.map(a => (
                          <span key={a} style={s.amenChip}>{a}</span>
                        )) || '—'}
                      </div>
                    </td>
                  ))}
                  {selected.length < MAX && <td style={s.cell} />}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

const s = {
  page:          { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:        { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '2.5rem 0' },
  bannerInner:   { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 },
  h1:            { fontSize: 'clamp(22px,4vw,32px)', fontWeight: 900, margin: 0 },
  sub:           { fontSize: 14, opacity: 0.75, marginTop: 4 },
  addBtn:        { background: '#fff', color: '#1a56db', border: 'none', borderRadius: 10, padding: '10px 20px', fontWeight: 800, fontSize: 14, cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' },
  clearBtn:      { background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5', borderRadius: 10, padding: '10px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  overlay:       { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' },
  modal:         { background: '#fff', borderRadius: 20, width: '100%', maxWidth: 700, maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 24px 80px rgba(0,0,0,0.3)' },
  modalHeader:   { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid #e2e8f0' },
  modalTitle:    { fontSize: 18, fontWeight: 800, color: '#0f172a', margin: 0 },
  modalClose:    { background: '#f1f5f9', border: 'none', borderRadius: 8, padding: '6px 12px', cursor: 'pointer', fontSize: 16, fontWeight: 700 },
  modalSection:  { padding: '10px 24px 4px', fontSize: 12, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 },
  pickerGrid:    { overflowY: 'auto', padding: '12px 24px 20px', display: 'flex', flexDirection: 'column', gap: 10 },
  pickerCard:    { display: 'flex', gap: 14, alignItems: 'center', background: '#f8fafc', border: '1.5px solid #e2e8f0', borderRadius: 14, padding: '12px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s', position: 'relative' },
  pickerDisabled:{ opacity: 0.45, cursor: 'not-allowed' },
  pickerImg:     { width: 80, height: 56, objectFit: 'cover', borderRadius: 8, flexShrink: 0 },
  pickerInfo:    { flex: 1 },
  pickerTitle:   { fontSize: 14, fontWeight: 700, color: '#0f172a', marginBottom: 2 },
  pickerPrice:   { fontSize: 15, fontWeight: 900, color: '#1a56db' },
  pickerCity:    { fontSize: 12, color: '#64748b' },
  pickerAdded:   { position: 'absolute', top: 8, right: 12, background: '#d1fae5', color: '#065f46', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 },
  modalHint:     { padding: '12px 24px 20px', fontSize: 13, color: '#64748b', borderTop: '1px solid #f1f5f9', marginTop: 4 },
  wrap:          { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  empty:         { minHeight: '50vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, textAlign: 'center', background: '#fff', borderRadius: 20, border: '1px solid #e2e8f0', padding: '4rem 2rem' },
  emptyTitle:    { fontSize: 24, fontWeight: 900, color: '#0f172a', margin: 0 },
  emptySub:      { fontSize: 15, color: '#64748b', maxWidth: 420, lineHeight: 1.6 },
  browseBtn:     { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', padding: '13px 28px', borderRadius: 12, fontWeight: 800, fontSize: 15, cursor: 'pointer', border: 'none', boxShadow: '0 4px 14px rgba(26,86,219,0.35)' },
  table:         { width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 18, overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', minWidth: 600 },
  th:            { padding: '0 8px 16px', textAlign: 'center', fontWeight: 700, fontSize: 13, color: '#64748b', borderBottom: '2px solid #e2e8f0', verticalAlign: 'top', minWidth: 180 },
  colHeader:     { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, paddingTop: 16 },
  colImg:        { width: '100%', maxWidth: 200, height: 130, objectFit: 'cover', borderRadius: 12 },
  colTitle:      { fontSize: 14, fontWeight: 800, color: '#0f172a', textAlign: 'center', lineHeight: 1.3 },
  colCity:       { fontSize: 12, color: '#64748b' },
  viewBtn:       { background: '#eff6ff', color: '#1a56db', border: 'none', borderRadius: 8, padding: '5px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer', textDecoration: 'none' },
  removeColBtn:  { background: '#fef2f2', color: '#dc2626', border: 'none', borderRadius: 8, padding: '5px 10px', fontSize: 12, fontWeight: 700, cursor: 'pointer' },
  addColBtn:     { background: '#f8fafc', border: '2px dashed #e2e8f0', borderRadius: 14, padding: '20px', cursor: 'pointer', color: '#94a3b8', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, width: '100%', transition: 'all 0.15s' },
  rowEven:       { background: '#f8fafc' },
  rowLabel:      { padding: '13px 18px', fontSize: 13, fontWeight: 700, color: '#374151', textAlign: 'left', borderRight: '1px solid #e2e8f0', whiteSpace: 'nowrap' },
  cell:          { padding: '13px 12px', fontSize: 14, fontWeight: 600, color: '#0f172a', textAlign: 'center', borderRight: '1px solid #f1f5f9', position: 'relative', textTransform: 'capitalize' },
  bestCell:      { background: '#f0fdf4', color: '#065f46' },
  bestBadge:     { display: 'block', fontSize: 10, fontWeight: 800, color: '#059669', marginTop: 2 },
  amenChip:      { background: '#eff6ff', color: '#1d4ed8', borderRadius: 20, padding: '2px 8px', fontSize: 11, fontWeight: 600 },
}
