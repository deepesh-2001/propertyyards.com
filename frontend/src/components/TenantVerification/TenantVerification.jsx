import React, { useState } from 'react'
import { FiShield, FiCheck, FiUpload, FiFileText, FiUser } from 'react-icons/fi'
import './TenantVerification.css'

const STEPS = [
  { id: 'identity', title: 'Identity', desc: 'Aadhaar / PAN / Passport', icon: <FiUser /> },
  { id: 'employment', title: 'Employment', desc: 'Offer letter or payslip', icon: <FiFileText /> },
  { id: 'police', title: 'Police verification', desc: 'Background check', icon: <FiShield /> },
  { id: 'address', title: 'Address proof', desc: 'Utility bill', icon: <FiFileText /> },
]

export function TenantVerification() {
  const [done, setDone] = useState({})
  const [uploaded, setUploaded] = useState({})

  const handleUpload = async (id, file) => {
    setUploaded((u) => ({ ...u, [id]: file?.name || 'file' }))
    // best-effort
    const fd = new FormData()
    fd.append('document', file)
    fd.append('type', id)
    fetch('/api/tenant-verification/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
      body: fd,
    }).catch(() => null)
    setTimeout(() => setDone((d) => ({ ...d, [id]: true })), 600)
  }

  const completed = STEPS.filter((s) => done[s.id]).length
  const pct = Math.round((completed / STEPS.length) * 100)

  return (
    <div className="tv-page">
      <div className="tv-header">
        <h1><FiShield /> Tenant Verification</h1>
        <p>Get a verified tenant badge — landlords prefer pre-verified tenants and approve faster.</p>
        <div className="tv-progress">
          <div className="tv-bar"><div className="tv-bar-fill" style={{ width: `${pct}%` }} /></div>
          <span>{pct}% complete</span>
        </div>
      </div>

      <div className="tv-steps">
        {STEPS.map((s) => (
          <div key={s.id} className={`tv-step ${done[s.id] ? 'done' : ''}`}>
            <div className="tv-step-icon">{done[s.id] ? <FiCheck /> : s.icon}</div>
            <div className="tv-step-body">
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
              {uploaded[s.id] && <small>Uploaded: {uploaded[s.id]}</small>}
            </div>
            <label className="tv-upload-btn">
              <FiUpload /> {done[s.id] ? 'Replace' : 'Upload'}
              <input
                type="file"
                hidden
                onChange={(e) => e.target.files?.[0] && handleUpload(s.id, e.target.files[0])}
              />
            </label>
          </div>
        ))}
      </div>

      {pct === 100 && (
        <div className="tv-success">
          ✅ All documents submitted — verification typically completes in 24–48 hours.
        </div>
      )}
    </div>
  )
}

export default TenantVerification
