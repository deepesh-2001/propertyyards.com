import React, { useState, useMemo } from 'react'
import { FiFileText, FiDownload, FiSend } from 'react-icons/fi'
import { apiUrl, authHeaders } from '../../services/api'
import './RentalAgreement.css'

const DEFAULTS = {
  landlord: '',
  tenant: '',
  property: '',
  rent: 25000,
  deposit: 100000,
  start: new Date().toISOString().slice(0, 10),
  duration: 11,
  city: 'Bengaluru',
}

export function RentalAgreement() {
  const [form, setForm] = useState(DEFAULTS)
  const update = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }))

  const text = useMemo(() => buildAgreement(form), [form])

  const handleDownload = () => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rental-agreement-${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSendForESign = async () => {
    try {
      const res = await fetch(apiUrl('/api/rental-agreements/esign'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ ...form, agreement_text: text }),
      })
      if (res.ok) alert('Sent for e-sign! Both parties will receive an email.')
      else throw new Error()
    } catch {
      alert('E-sign backend not configured yet. Downloaded a copy instead.')
      handleDownload()
    }
  }

  return (
    <div className="ra-page">
      <div className="ra-header">
        <h1><FiFileText /> Rental Agreement</h1>
        <p>Fill in details, preview the agreement, then send it for e-signature.</p>
      </div>

      <div className="ra-grid">
        <form className="ra-form" onSubmit={(e) => e.preventDefault()}>
          <Field label="Landlord name" value={form.landlord} onChange={update('landlord')} />
          <Field label="Tenant name" value={form.tenant} onChange={update('tenant')} />
          <Field label="Property address" value={form.property} onChange={update('property')} />
          <div className="ra-row">
            <Field label="Monthly rent (₹)" type="number" value={form.rent} onChange={update('rent')} />
            <Field label="Security deposit (₹)" type="number" value={form.deposit} onChange={update('deposit')} />
          </div>
          <div className="ra-row">
            <Field label="Start date" type="date" value={form.start} onChange={update('start')} />
            <Field label="Duration (months)" type="number" value={form.duration} onChange={update('duration')} />
          </div>
          <Field label="City of jurisdiction" value={form.city} onChange={update('city')} />

          <div className="ra-actions">
            <button type="button" className="ra-btn" onClick={handleDownload}>
              <FiDownload /> Download draft
            </button>
            <button type="button" className="ra-btn ra-btn-primary" onClick={handleSendForESign}>
              <FiSend /> Send for e-sign
            </button>
          </div>
        </form>

        <div className="ra-preview">
          <h3>Preview</h3>
          <pre>{text}</pre>
        </div>
      </div>
    </div>
  )
}

function Field({ label, ...rest }) {
  return (
    <label className="ra-field">
      <span>{label}</span>
      <input {...rest} />
    </label>
  )
}

function buildAgreement(f) {
  return `RENTAL AGREEMENT

This Rental Agreement is made on ${new Date().toDateString()} between:

LANDLORD: ${f.landlord || '[Landlord Name]'}
TENANT:   ${f.tenant || '[Tenant Name]'}

PROPERTY: ${f.property || '[Property Address]'}

TERMS:
- Monthly Rent: ₹${Number(f.rent).toLocaleString('en-IN')}
- Security Deposit: ₹${Number(f.deposit).toLocaleString('en-IN')} (refundable)
- Start Date: ${f.start}
- Duration: ${f.duration} months
- Jurisdiction: ${f.city}

CONDITIONS:
1. Rent is payable on or before the 5th of each month.
2. The deposit is refundable on vacating the premises, subject to deductions for damages.
3. The tenant shall use the property only for residential purposes.
4. Either party may terminate this agreement with 30 days' written notice.
5. Any disputes shall be subject to the jurisdiction of courts in ${f.city}.

SIGNED:

____________________            ____________________
Landlord                        Tenant
`
}

export default RentalAgreement
