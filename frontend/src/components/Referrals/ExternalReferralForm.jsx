import React, { useState } from 'react'
import { useReferralStore } from '../../stores/referralStore'
import { FiSend, FiCheckCircle, FiGift, FiTrendingUp, FiShield } from 'react-icons/fi'
import './ExternalReferralForm.css'

// Test properties for dropdown
const TEST_PROPERTIES = [
  { id: 1, title: 'Modern 3BHK Apartment', value: 750000 },
  { id: 2, title: 'Luxury Villa with Garden', value: 2500000 },
  { id: 3, title: 'Cozy Studio Apartment', value: 350000 },
  { id: 4, title: 'Premium Penthouse', value: 5000000 },
  { id: 5, title: 'Family Home with Pool', value: 1800000 }
]

export function ExternalReferralForm() {
  const { createReferral } = useReferralStore()
  const [submitted, setSubmitted] = useState(false)
  const [referralCode, setReferralCode] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [formData, setFormData] = useState({
    referrerName: '',
    referrerEmail: '',
    referrerPhone: '',
    propertyId: '',
    propertyTitle: '',
    propertyValue: '',
    buyerName: '',
    buyerEmail: '',
    buyerPhone: '',
    notes: ''
  })

  const handlePropertyChange = (e) => {
    const propertyId = e.target.value
    const property = TEST_PROPERTIES.find(p => p.id.toString() === propertyId)

    if (property) {
      setFormData({
        ...formData,
        propertyId: property.id,
        propertyTitle: property.title,
        propertyValue: property.value
      })
    } else {
      setFormData({
        ...formData,
        propertyId: '',
        propertyTitle: '',
        propertyValue: ''
      })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500))

      const referral = createReferral({
        ...formData,
        propertyValue: Number(formData.propertyValue) || 0,
        source: 'external',
        userAgent: navigator.userAgent,
        referrer: document.referrer,
        landingPage: window.location.href,
        ipAddress: '127.0.0.1' // In real app, this would be captured server-side
      })

      setReferralCode(referral.code)
      setSubmitted(true)
    } catch (error) {
      alert('Error creating referral: ' + error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const calculateEarnings = () => {
    const value = Number(formData.propertyValue) || 0
    return Math.round(value * 0.02) // 2% commission
  }

  if (submitted) {
    return (
      <div className="external-referral-form">
        <div className="success-container">
          <div className="success-icon">
            <FiCheckCircle size={64} />
          </div>
          <h2>Referral Submitted Successfully!</h2>
          <p className="success-message">
            Thank you for your referral. Our team will review it and contact you soon.
          </p>

          <div className="referral-code-box">
            <span className="code-label">Your Referral Code</span>
            <span className="code-value">{referralCode}</span>
            <p className="code-hint">Save this code to track your referral status</p>
          </div>

          <div className="earnings-preview">
            <h3>Potential Earnings</h3>
            <div className="earnings-amount">${calculateEarnings().toLocaleString()}</div>
            <p>2% commission on property value</p>
          </div>

          <div className="next-steps">
            <h3>What happens next?</h3>
            <ul>
              <li>Our team will contact the buyer within 24 hours</li>
              <li>If the sale is successful, you'll receive your commission</li>
              <li>Payment will be processed within 30 days of closing</li>
            </ul>
          </div>

          <button
            className="btn-submit-another"
            onClick={() => {
              setSubmitted(false)
              setReferralCode('')
              setFormData({
                referrerName: '',
                referrerEmail: '',
                referrerPhone: '',
                propertyId: '',
                propertyTitle: '',
                propertyValue: '',
                buyerName: '',
                buyerEmail: '',
                buyerPhone: '',
                notes: ''
              })
            }}
          >
            Submit Another Referral
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="external-referral-form">
      <div className="referral-header-section">
        <h1>🏠 Submit a Referral</h1>
        <p>Refer a buyer and earn up to 2% commission on successful sales</p>
      </div>

      <div className="benefits-banner">
        <div className="benefit-item">
          <FiGift className="benefit-icon" />
          <span>Up to 2% Commission</span>
        </div>
        <div className="benefit-item">
          <FiTrendingUp className="benefit-icon" />
          <span>Unlimited Earnings</span>
        </div>
        <div className="benefit-item">
          <FiShield className="benefit-icon" />
          <span>Secure & Trusted</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="referral-form-container">
        <div className="form-section">
          <h3>Your Information</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Your Name *</label>
              <input
                type="text"
                required
                placeholder="John Doe"
                value={formData.referrerName}
                onChange={(e) => setFormData({ ...formData, referrerName: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Your Email *</label>
              <input
                type="email"
                required
                placeholder="john@example.com"
                value={formData.referrerEmail}
                onChange={(e) => setFormData({ ...formData, referrerEmail: e.target.value })}
              />
            </div>
          </div>
          <div className="form-group">
            <label>Your Phone Number</label>
            <input
              type="tel"
              placeholder="+91-9876543210"
              value={formData.referrerPhone}
              onChange={(e) => setFormData({ ...formData, referrerPhone: e.target.value })}
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Property Information</h3>
          <div className="form-group">
            <label>Select Property *</label>
            <select
              required
              value={formData.propertyId}
              onChange={handlePropertyChange}
            >
              <option value="">Choose a property...</option>
              {TEST_PROPERTIES.map(prop => (
                <option key={prop.id} value={prop.id}>
                  {prop.title} - ${prop.value.toLocaleString()}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Property Title</label>
              <input
                type="text"
                placeholder="Or enter custom property"
                value={formData.propertyTitle}
                onChange={(e) => setFormData({ ...formData, propertyTitle: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Property Value ($)</label>
              <input
                type="number"
                placeholder="750000"
                value={formData.propertyValue}
                onChange={(e) => setFormData({ ...formData, propertyValue: e.target.value })}
              />
            </div>
          </div>

          {formData.propertyValue && (
            <div className="earnings-calc">
              <span className="calc-label">Your Potential Earnings:</span>
              <span className="calc-value">${calculateEarnings().toLocaleString()}</span>
            </div>
          )}
        </div>

        <div className="form-section">
          <h3>Buyer Information</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Buyer Name *</label>
              <input
                type="text"
                required
                placeholder="Jane Smith"
                value={formData.buyerName}
                onChange={(e) => setFormData({ ...formData, buyerName: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Buyer Email</label>
              <input
                type="email"
                placeholder="jane@example.com"
                value={formData.buyerEmail}
                onChange={(e) => setFormData({ ...formData, buyerEmail: e.target.value })}
              />
            </div>
          </div>
          <div className="form-group">
            <label>Buyer Phone</label>
            <input
              type="tel"
              placeholder="+91-9876543210"
              value={formData.buyerPhone}
              onChange={(e) => setFormData({ ...formData, buyerPhone: e.target.value })}
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Additional Notes</h3>
          <div className="form-group">
            <textarea
              placeholder="Any additional information about the buyer or property..."
              rows={4}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>
        </div>

        <div className="form-footer">
          <p className="terms-text">
            By submitting, you agree to our referral program terms. 
            Commission is paid only on successful property sales.
          </p>
          <button
            type="submit"
            className="btn-submit-referral"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <span className="spinner"></span>
                Submitting...
              </>
            ) : (
              <>
                <FiSend />
                Submit Referral
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default ExternalReferralForm
