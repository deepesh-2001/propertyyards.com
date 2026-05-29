import React from 'react'
import { Link } from 'react-router-dom'
import { FiArrowLeft, FiTrash2, FiCheck, FiX as FiCross } from 'react-icons/fi'
import { useCompareStore } from '../../stores/compareStore'
import './Compare.css'

const ROWS = [
  { label: 'Price', key: 'price', fmt: (v) => (typeof v === 'number' ? `₹${v.toLocaleString('en-IN')}` : '—') },
  { label: 'City', key: 'city' },
  { label: 'State', key: 'state' },
  { label: 'Bedrooms', key: 'bedrooms' },
  { label: 'Bathrooms', key: 'bathrooms' },
  { label: 'Area (sqft)', key: 'area', fmt: (v) => (typeof v === 'number' ? v.toLocaleString() : '—') },
  { label: 'Type', key: 'property_type' },
  { label: 'RERA ID', key: 'rera_id' },
  { label: 'Verified', key: 'verified', fmt: (v) => (v ? '✓' : '—') },
  { label: 'Listed by Owner', key: 'is_owner', fmt: (v) => (v ? '✓' : '—') },
  { label: 'Furnished', key: 'furnishing' },
]

export function ComparePage() {
  const items = useCompareStore((s) => s.items)
  const remove = useCompareStore((s) => s.remove)
  const clear = useCompareStore((s) => s.clear)

  if (!items.length) {
    return (
      <div className="compare-page-empty">
        <h2>Nothing to compare</h2>
        <p>Add properties from the listings page to start comparing.</p>
        <Link to="/properties" className="compare-btn compare-btn-primary">
          <FiArrowLeft /> Browse properties
        </Link>
      </div>
    )
  }

  return (
    <div className="compare-page">
      <div className="compare-page-header">
        <h1>Compare Properties</h1>
        <button className="compare-btn" onClick={clear}>
          <FiTrash2 /> Clear all
        </button>
      </div>

      <div className="compare-grid" style={{ gridTemplateColumns: `200px repeat(${items.length}, 1fr)` }}>
        <div className="compare-cell compare-head">Property</div>
        {items.map((p) => (
          <div key={p.id} className="compare-cell compare-head compare-card">
            {p.images?.[0] && <img src={p.images[0]} alt={p.title} />}
            <div className="compare-card-title">{p.title}</div>
            <button className="compare-remove" onClick={() => remove(p.id)} aria-label="Remove">
              <FiCross />
            </button>
          </div>
        ))}

        {ROWS.map((row) => (
          <React.Fragment key={row.key}>
            <div className="compare-cell compare-row-label">{row.label}</div>
            {items.map((p) => {
              const v = p[row.key]
              return (
                <div key={p.id + row.key} className="compare-cell">
                  {row.fmt ? row.fmt(v) : v ?? '—'}
                </div>
              )
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}

export default ComparePage
