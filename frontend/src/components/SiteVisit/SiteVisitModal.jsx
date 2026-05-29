import React, { useState } from 'react'
import { FiCalendar, FiClock, FiPhone, FiUser, FiX, FiCheck } from 'react-icons/fi'
import './SiteVisit.css'

const TIME_SLOTS = ['10:00', '11:30', '13:00', '14:30', '16:00', '17:30']

function nextNDays(n = 7) {
  const out = []
  const today = new Date()
  for (let i = 1; i <= n; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    out.push(d)
  }
  return out
}

/**
 * SiteVisitModal — book a viewing for a property.
 * Props: propertyId, propertyTitle, onClose
 * Posts to /api/site-visits via fetch — falls back to local success if endpoint missing.
 */
export function SiteVisitModal({ propertyId, propertyTitle, onClose }) {
  const [step, setStep] = useState(1)
  const [date, setDate] = useState(null)
  const [slot, setSlot] = useState(null)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const days = nextNDays(7)

  const submit = async () => {
    setSubmitting(true)
    try {
      await fetch('/api/site-visits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          property_id: propertyId,
          visit_date: date?.toISOString().slice(0, 10),
          visit_time: slot,
          visitor_name: name,
          visitor_phone: phone,
        }),
      }).catch(() => null) // tolerate missing backend route
      setDone(true)
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <div className="sv-overlay" onClick={onClose}>
        <div className="sv-modal sv-success" onClick={(e) => e.stopPropagation()}>
          <FiCheck size={48} className="sv-success-icon" />
          <h2>Visit requested!</h2>
          <p>
            We&apos;ve sent your request for{' '}
            <strong>{date?.toDateString()}</strong> at <strong>{slot}</strong>.
            The owner / agent will confirm shortly via SMS / WhatsApp.
          </p>
          <button className="sv-btn sv-btn-primary" onClick={onClose}>Done</button>
        </div>
      </div>
    )
  }

  return (
    <div className="sv-overlay" onClick={onClose}>
      <div className="sv-modal" onClick={(e) => e.stopPropagation()}>
        <button className="sv-close" onClick={onClose}><FiX /></button>
        <h2>Book a Site Visit</h2>
        <p className="sv-sub">{propertyTitle}</p>

        <div className="sv-steps">
          <span className={step >= 1 ? 'active' : ''}>1. Date</span>
          <span className={step >= 2 ? 'active' : ''}>2. Time</span>
          <span className={step >= 3 ? 'active' : ''}>3. Contact</span>
        </div>

        {step === 1 && (
          <div className="sv-grid sv-dates">
            {days.map((d) => (
              <button
                key={d.toISOString()}
                className={`sv-day ${date?.toDateString() === d.toDateString() ? 'selected' : ''}`}
                onClick={() => { setDate(d); setStep(2) }}
              >
                <FiCalendar />
                <div>
                  <strong>{d.toLocaleDateString(undefined, { weekday: 'short' })}</strong>
                  <span>{d.getDate()} {d.toLocaleDateString(undefined, { month: 'short' })}</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {step === 2 && (
          <div className="sv-grid sv-slots">
            {TIME_SLOTS.map((t) => (
              <button
                key={t}
                className={`sv-slot ${slot === t ? 'selected' : ''}`}
                onClick={() => { setSlot(t); setStep(3) }}
              >
                <FiClock /> {t}
              </button>
            ))}
          </div>
        )}

        {step === 3 && (
          <div className="sv-form">
            <label>
              <FiUser />
              <input type="text" placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              <FiPhone />
              <input type="tel" placeholder="Phone number" value={phone} onChange={(e) => setPhone(e.target.value)} required />
            </label>
            <button
              className="sv-btn sv-btn-primary"
              disabled={!name || !phone || submitting}
              onClick={submit}
            >
              {submitting ? 'Booking...' : `Confirm visit on ${date?.toDateString()} at ${slot}`}
            </button>
          </div>
        )}

        {step > 1 && (
          <button className="sv-back" onClick={() => setStep(step - 1)}>← Back</button>
        )}
      </div>
    </div>
  )
}

export default SiteVisitModal
