import React, { useState } from 'react'
import { FiVideo, FiX, FiExternalLink } from 'react-icons/fi'
import './VirtualTour.css'

/**
 * VirtualTour — opens a fullscreen modal with an embedded 360/video tour.
 * Props:
 *  - url?: string  (YouTube/Matterport/Kuula iframe URL)
 *  - title?: string
 */
export function VirtualTour({ url, title = 'Virtual Tour' }) {
  const [open, setOpen] = useState(false)
  if (!url) return null

  return (
    <>
      <button className="vt-trigger" onClick={() => setOpen(true)}>
        <FiVideo /> 360° Virtual Tour
      </button>
      {open && (
        <div className="vt-overlay" onClick={() => setOpen(false)}>
          <div className="vt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="vt-header">
              <strong>{title}</strong>
              <div className="vt-actions">
                <a href={url} target="_blank" rel="noreferrer" className="vt-link" title="Open in new tab">
                  <FiExternalLink />
                </a>
                <button onClick={() => setOpen(false)} aria-label="Close"><FiX /></button>
              </div>
            </div>
            <iframe
              src={url}
              title={title}
              allow="accelerometer; gyroscope; fullscreen; xr-spatial-tracking"
              allowFullScreen
            />
          </div>
        </div>
      )}
    </>
  )
}

export default VirtualTour
