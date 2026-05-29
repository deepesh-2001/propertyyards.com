import React from 'react'
import { FiCheckCircle, FiShield } from 'react-icons/fi'
import './RERABadge.css'

/**
 * RERA / Verified badge — shows trust signals on a property card.
 * Props:
 *  - rera_id?: string         (shows "RERA ID: ..." tooltip)
 *  - verified?: boolean       (verified by platform)
 *  - size?: 'sm' | 'md'
 */
export function RERABadge({ rera_id, verified, size = 'sm' }) {
  if (!rera_id && !verified) return null
  return (
    <div className={`rera-badge-wrap rera-${size}`}>
      {rera_id && (
        <span className="rera-badge rera-rera" title={`RERA ID: ${rera_id}`}>
          <FiShield /> RERA
        </span>
      )}
      {verified && (
        <span className="rera-badge rera-verified" title="Verified by PropertyYards">
          <FiCheckCircle /> Verified
        </span>
      )}
    </div>
  )
}

export default RERABadge
