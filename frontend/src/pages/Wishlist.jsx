import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PropertyCard from '../components/PropertyCard'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { TEST_PROPERTIES } from '../data/testData'

export function getWishlist()          { try { return JSON.parse(localStorage.getItem('py_wishlist') || '[]') } catch { return [] } }
export function toggleWishlist(id)     {
  const list = getWishlist()
  const next = list.includes(id) ? list.filter(x => x !== id) : [...list, id]
  localStorage.setItem('py_wishlist', JSON.stringify(next))
  window.dispatchEvent(new Event('wishlist-change'))
  return next.includes(id)
}
export function isWishlisted(id)       { return getWishlist().includes(id) }

export default function Wishlist() {
  const { isMobile, isTablet } = useBreakpoint()
  const nav = useNavigate()
  const [ids, setIds]     = useState(getWishlist)
  const [sort, setSort]   = useState('saved')

  useEffect(() => {
    const handler = () => setIds(getWishlist())
    window.addEventListener('wishlist-change', handler)
    return () => window.removeEventListener('wishlist-change', handler)
  }, [])

  const properties = TEST_PROPERTIES.filter(p => ids.includes(p.id))

  const sorted = [...properties].sort((a, b) => {
    if (sort === 'price_asc')  return a.price - b.price
    if (sort === 'price_desc') return b.price - a.price
    if (sort === 'area')       return b.area - a.area
    return 0
  })

  const cols = isMobile ? '1fr' : isTablet ? 'repeat(2,1fr)' : 'repeat(auto-fill,minmax(300px,1fr))'

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>❤️ My Wishlist</h1>
            <p style={s.sub}>{ids.length} saved propert{ids.length === 1 ? 'y' : 'ies'}</p>
          </div>
          {ids.length > 0 && (
            <div style={s.bannerRight}>
              <select value={sort} onChange={e => setSort(e.target.value)} style={s.sortSel}>
                <option value="saved">Recently Saved</option>
                <option value="price_asc">Price: Low → High</option>
                <option value="price_desc">Price: High → Low</option>
                <option value="area">Largest Area</option>
              </select>
              <button onClick={() => { localStorage.removeItem('py_wishlist'); setIds([]) }} style={s.clearBtn}>
                🗑 Clear All
              </button>
            </div>
          )}
        </div>
      </div>

      <div style={s.wrap}>
        {ids.length === 0 ? (
          <div style={s.empty}>
            <div style={{ fontSize: 72 }}>💔</div>
            <h2 style={s.emptyTitle}>No Saved Properties</h2>
            <p style={s.emptySub}>Browse properties and tap the ❤️ heart button to save them here for later.</p>
            <Link to="/" style={s.browseBtn}>Browse Properties →</Link>
          </div>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: cols, gap: 24 }}>
              {sorted.map(p => (
                <div key={p.id} style={{ position: 'relative' }}>
                  <PropertyCard property={p} />
                  <button
                    onClick={() => { toggleWishlist(p.id); setIds(getWishlist()) }}
                    style={s.removeBtn}
                    title="Remove from wishlist"
                  >
                    ✕ Remove
                  </button>
                </div>
              ))}
            </div>

            <div style={s.compareHint}>
              💡 <strong>Tip:</strong> Go to{' '}
              <Link to="/compare" style={{ color: '#1a56db', fontWeight: 700 }}>Compare Properties</Link>
              {' '}to see a side-by-side analysis of up to 4 saved properties.
            </div>
          </>
        )}
      </div>
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:      { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '2.5rem 0' },
  bannerInner: { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 },
  h1:          { fontSize: 'clamp(22px,4vw,32px)', fontWeight: 900, margin: 0, letterSpacing: '-0.5px' },
  sub:         { fontSize: 14, opacity: 0.75, marginTop: 4 },
  bannerRight: { display: 'flex', gap: 10, alignItems: 'center' },
  sortSel:     { border: 'none', borderRadius: 10, padding: '9px 14px', fontSize: 13, fontWeight: 600, background: 'rgba(255,255,255,0.15)', color: '#fff', cursor: 'pointer', outline: 'none' },
  clearBtn:    { background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5', borderRadius: 10, padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  wrap:        { maxWidth: 1240, margin: '0 auto', padding: '2rem 1.5rem' },
  empty:       { minHeight: '50vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, textAlign: 'center', background: '#fff', borderRadius: 20, border: '1px solid #e2e8f0', padding: '4rem 2rem' },
  emptyTitle:  { fontSize: 24, fontWeight: 900, color: '#0f172a', margin: 0 },
  emptySub:    { fontSize: 15, color: '#64748b', maxWidth: 400, lineHeight: 1.6 },
  browseBtn:   { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', padding: '13px 28px', borderRadius: 12, fontWeight: 800, textDecoration: 'none', fontSize: 15, boxShadow: '0 4px 14px rgba(26,86,219,0.35)' },
  removeBtn:   { position: 'absolute', top: 10, right: 10, background: 'rgba(239,68,68,0.9)', color: '#fff', border: 'none', borderRadius: 8, padding: '5px 10px', fontSize: 12, fontWeight: 700, cursor: 'pointer', backdropFilter: 'blur(4px)', zIndex: 10 },
  compareHint: { marginTop: 32, background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 14, padding: '14px 20px', fontSize: 14, color: '#78350f' },
}
