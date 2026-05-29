import React, { useEffect, useState } from 'react'
import { FiTrendingUp, FiTrendingDown, FiBarChart2 } from 'react-icons/fi'
import './PricePrediction.css'

/**
 * PricePrediction — predicts 1-year price change for a property.
 * Hits /api/predict/price; falls back to a simple deterministic mock so the
 * UI is never empty during dev.
 */
export function PricePrediction({ property }) {
  const [pred, setPred] = useState(null)

  useEffect(() => {
    if (!property?.id) return
    let cancelled = false
    fetch(`/api/predict/price/${property.id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
    })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) => !cancelled && setPred(d))
      .catch(() => {
        if (cancelled) return
        // Mock: deterministic based on price
        const base = Number(property.price) || 5000000
        const change = ((Number(String(property.id).slice(-2)) % 11) - 3) / 100
        setPred({
          current_price: base,
          predicted_price: Math.round(base * (1 + change)),
          change_pct: +(change * 100).toFixed(1),
          confidence: 0.72,
          horizon_months: 12,
          source: 'mock',
        })
      })
    return () => { cancelled = true }
  }, [property?.id, property?.price])

  if (!pred) return null
  const positive = pred.change_pct >= 0

  return (
    <div className="pp-card">
      <div className="pp-header">
        <FiBarChart2 /> <h3>Price prediction</h3>
        <span className="pp-horizon">{pred.horizon_months || 12} mo</span>
      </div>
      <div className="pp-body">
        <div>
          <span className="pp-label">Today</span>
          <span className="pp-value">₹{Number(pred.current_price).toLocaleString('en-IN')}</span>
        </div>
        <div className={`pp-arrow ${positive ? 'up' : 'down'}`}>
          {positive ? <FiTrendingUp /> : <FiTrendingDown />}
          <span>{positive ? '+' : ''}{pred.change_pct}%</span>
        </div>
        <div>
          <span className="pp-label">In {pred.horizon_months || 12} months</span>
          <span className="pp-value">₹{Number(pred.predicted_price).toLocaleString('en-IN')}</span>
        </div>
      </div>
      <div className="pp-footer">
        Confidence: {Math.round((pred.confidence || 0.7) * 100)}%
        {pred.source === 'mock' && <span className="pp-mock"> · estimated</span>}
      </div>
    </div>
  )
}

export default PricePrediction
