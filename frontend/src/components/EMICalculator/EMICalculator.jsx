import React, { useState, useMemo } from 'react'
import { FiDollarSign } from 'react-icons/fi'
import './EMICalculator.css'

/**
 * EMI Calculator — pure client-side. Optionally hits backend if available.
 * Props:
 *  - price: number (loan principal seed)
 *  - currency?: string  (default '₹')
 */
export function EMICalculator({ price = 5000000, currency = '₹' }) {
  const [principal, setPrincipal] = useState(price)
  const [downPct, setDownPct] = useState(20)
  const [rate, setRate] = useState(8.5)
  const [years, setYears] = useState(20)

  const { loan, emi, totalInterest, totalPayable } = useMemo(() => {
    const loan = Math.max(0, principal * (1 - downPct / 100))
    const n = years * 12
    const r = rate / 12 / 100
    const emi = r === 0 ? loan / n : (loan * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1)
    const totalPayable = emi * n
    const totalInterest = totalPayable - loan
    return { loan, emi, totalInterest, totalPayable }
  }, [principal, downPct, rate, years])

  const fmt = (n) =>
    `${currency}${Math.round(n).toLocaleString('en-IN')}`

  return (
    <div className="emi-calc">
      <div className="emi-header">
        <FiDollarSign /> <h3>EMI Calculator</h3>
      </div>

      <div className="emi-row">
        <label>Property Price</label>
        <input
          type="number"
          value={principal}
          onChange={(e) => setPrincipal(Number(e.target.value) || 0)}
          min={0}
        />
      </div>

      <div className="emi-row">
        <label>Down Payment ({downPct}%)</label>
        <input
          type="range"
          min={0}
          max={90}
          value={downPct}
          onChange={(e) => setDownPct(Number(e.target.value))}
        />
      </div>

      <div className="emi-row">
        <label>Interest Rate ({rate}%)</label>
        <input
          type="range"
          min={5}
          max={15}
          step={0.1}
          value={rate}
          onChange={(e) => setRate(Number(e.target.value))}
        />
      </div>

      <div className="emi-row">
        <label>Tenure ({years} yrs)</label>
        <input
          type="range"
          min={1}
          max={30}
          value={years}
          onChange={(e) => setYears(Number(e.target.value))}
        />
      </div>

      <div className="emi-summary">
        <div className="emi-stat">
          <span className="emi-label">Monthly EMI</span>
          <span className="emi-value emi-primary">{fmt(emi)}</span>
        </div>
        <div className="emi-stat">
          <span className="emi-label">Loan Amount</span>
          <span className="emi-value">{fmt(loan)}</span>
        </div>
        <div className="emi-stat">
          <span className="emi-label">Total Interest</span>
          <span className="emi-value">{fmt(totalInterest)}</span>
        </div>
        <div className="emi-stat">
          <span className="emi-label">Total Payable</span>
          <span className="emi-value">{fmt(totalPayable)}</span>
        </div>
      </div>
    </div>
  )
}

export default EMICalculator
