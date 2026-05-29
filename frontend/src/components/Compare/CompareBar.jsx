import React from 'react'
import { Link } from 'react-router-dom'
import { FiBarChart2, FiX } from 'react-icons/fi'
import { useCompareStore } from '../../stores/compareStore'
import './Compare.css'

export function CompareBar() {
  const items = useCompareStore((s) => s.items)
  const remove = useCompareStore((s) => s.remove)
  const clear = useCompareStore((s) => s.clear)

  if (!items.length) return null

  return (
    <div className="compare-bar" role="region" aria-label="Properties to compare">
      <div className="compare-bar-inner">
        <div className="compare-bar-title">
          <FiBarChart2 /> Compare ({items.length})
        </div>
        <div className="compare-chips">
          {items.map((p) => (
            <div key={p.id} className="compare-chip" title={p.title}>
              <span>{p.title?.slice(0, 22) || `#${p.id}`}</span>
              <button onClick={() => remove(p.id)} aria-label="Remove">
                <FiX />
              </button>
            </div>
          ))}
        </div>
        <div className="compare-actions">
          <Link to="/compare" className="compare-btn compare-btn-primary">
            Compare now
          </Link>
          <button className="compare-btn" onClick={clear}>
            Clear
          </button>
        </div>
      </div>
    </div>
  )
}

export default CompareBar
