import { useState } from 'react'
import { useLang } from '../context/LangContext'
import { useBreakpoint } from '../hooks/useBreakpoint'

/* ── Product catalogue ──────────────────────────────────── */
const BANKS = [
  { name: 'SBI Home Loans',    rate: 8.50, maxTenure: 30, logo: '🏛️', tag: 'Govt. Backed',  color: '#1a56db' },
  { name: 'HDFC Ltd.',         rate: 8.65, maxTenure: 30, logo: '🏦', tag: 'Most Popular',  color: '#e11d48' },
  { name: 'ICICI Bank',        rate: 8.75, maxTenure: 30, logo: '💳', tag: 'Quick Approval', color: '#f59e0b' },
  { name: 'Kotak Mahindra',    rate: 8.70, maxTenure: 20, logo: '🔴', tag: 'Low Processing',color: '#7c3aed' },
  { name: 'Axis Bank',         rate: 8.80, maxTenure: 30, logo: '🟦', tag: 'Flexible EMI',  color: '#059669' },
  { name: 'LIC Housing Fin.',  rate: 8.45, maxTenure: 30, logo: '🛡️', tag: 'Lowest Rate',   color: '#0369a1' },
]

const INSURANCE = [
  { name: 'Home Shield Pro',    provider: 'HDFC Ergo',       premium: '₹4,200/yr',  cover: '₹1 Cr',  tag: 'Bestseller',  icon: '🏠', color: '#1a56db' },
  { name: 'Property Guard',     provider: 'Bajaj Allianz',   premium: '₹3,800/yr',  cover: '₹75 L',  tag: 'Budget Pick', icon: '🛡️', color: '#059669' },
  { name: 'Fire & Theft Cover', provider: 'New India Assur.', premium: '₹2,100/yr', cover: '₹50 L',  tag: 'Basic',       icon: '🔥', color: '#f59e0b' },
  { name: 'Comprehensive Plus', provider: 'ICICI Lombard',   premium: '₹6,500/yr',  cover: '₹2 Cr',  tag: 'Premium',     icon: '⭐', color: '#7c3aed' },
]

const TABS = ['emi', 'loans', 'insurance', 'balance']

/* ── Component ──────────────────────────────────────────── */
export default function Finance() {
  const { tr }       = useLang()
  const { isMobile } = useBreakpoint()
  const [tab, setTab] = useState('emi')

  return (
    <div style={s.page}>
      {/* Hero */}
      <div style={s.hero}>
        <div style={s.heroInner}>
          <div style={s.heroLeft}>
            <div style={s.heroBadge}>💰 Financial Products</div>
            <h1 style={s.heroH1}>Smart Finance for <br />Your Dream Home</h1>
            <p style={s.heroP}>Compare home loans, calculate EMIs, get property insurance — all in one place.</p>
            <div style={s.heroStats}>
              {[['8.45%','Lowest Rate'],['₹500Cr+','Loans Disbursed'],['50+','Partner Banks'],['24hr','Approval Time']].map(([v,l]) => (
                <div key={l} style={s.hStat}>
                  <span style={s.hStatVal}>{v}</span>
                  <span style={s.hStatLbl}>{l}</span>
                </div>
              ))}
            </div>
          </div>
          {!isMobile && (
            <div style={s.heroRight}>
              <QuickEMI />
            </div>
          )}
        </div>
      </div>

      {/* Tab navigation */}
      <div style={s.tabBar}>
        <div style={s.tabInner}>
          {[['emi','🧮 EMI Calculator'],['loans','🏦 Compare Loans'],['insurance','🛡️ Insurance'],['balance','🔄 Balance Transfer']].map(([k,l]) => (
            <button key={k} onClick={() => setTab(k)}
              style={{ ...s.tabBtn, ...(tab === k ? s.tabActive : {}) }}>
              {l}
            </button>
          ))}
        </div>
      </div>

      <div style={s.wrap}>
        {tab === 'emi'      && <EMICalculator isMobile={isMobile} />}
        {tab === 'loans'    && <LoanComparison isMobile={isMobile} />}
        {tab === 'insurance'&& <InsuranceSection isMobile={isMobile} />}
        {tab === 'balance'  && <BalanceTransfer isMobile={isMobile} />}
      </div>
    </div>
  )
}

/* ── Quick EMI widget (hero) ────────────────────────────── */
function QuickEMI() {
  const [amt, setAmt]   = useState(5000000)
  const [rate, setRate] = useState(8.5)
  const [yr, setYr]     = useState(20)
  const emi = calcEMI(amt, rate, yr)
  return (
    <div style={s.quickBox}>
      <div style={s.qTitle}>Quick EMI Check</div>
      <div style={s.qRow}>
        <label style={s.qLabel}>Loan Amount</label>
        <div style={s.qVal}>₹{formatLakh(amt)}</div>
      </div>
      <input type="range" min={500000} max={50000000} step={100000} value={amt} onChange={e => setAmt(+e.target.value)} style={s.range} />
      <div style={s.qRow}>
        <label style={s.qLabel}>Interest Rate</label>
        <div style={s.qVal}>{rate}%</div>
      </div>
      <input type="range" min={6} max={15} step={0.05} value={rate} onChange={e => setRate(+e.target.value)} style={s.range} />
      <div style={s.qRow}>
        <label style={s.qLabel}>Tenure</label>
        <div style={s.qVal}>{yr} yrs</div>
      </div>
      <input type="range" min={1} max={30} step={1} value={yr} onChange={e => setYr(+e.target.value)} style={s.range} />
      <div style={s.qResult}>
        <span style={s.qResultLabel}>Monthly EMI</span>
        <span style={s.qResultVal}>₹{emi.toLocaleString('en-IN')}</span>
      </div>
      <div style={s.qMeta}>Total Interest: ₹{((emi * yr * 12) - amt).toLocaleString('en-IN')}</div>
    </div>
  )
}

/* ── Full EMI Calculator tab ─────────────────────────────── */
function EMICalculator({ isMobile }) {
  const [loan, setLoan]   = useState(5000000)
  const [rate, setRate]   = useState(8.5)
  const [years, setYears] = useState(20)

  const emi          = calcEMI(loan, rate, years)
  const totalPay     = emi * years * 12
  const totalInt     = totalPay - loan
  const intPct       = Math.round((totalInt / totalPay) * 100)
  const prinPct      = 100 - intPct

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 28 }}>
      {/* Inputs */}
      <div style={s.card}>
        <h2 style={s.cardTitle}>🧮 EMI Calculator</h2>
        <SliderField label="Loan Amount" value={loan} min={100000} max={50000000} step={100000}
          onChange={setLoan} display={`₹${formatLakh(loan)}`} />
        <SliderField label="Interest Rate (% p.a.)" value={rate} min={5} max={20} step={0.05}
          onChange={setRate} display={`${rate.toFixed(2)}%`} />
        <SliderField label="Loan Tenure" value={years} min={1} max={30} step={1}
          onChange={setYears} display={`${years} Years`} />

        <div style={s.emiResult}>
          <div>
            <div style={s.emiLabel}>Monthly EMI</div>
            <div style={s.emiVal}>₹{emi.toLocaleString('en-IN')}</div>
          </div>
          <button style={s.applyBtn}>Apply Now →</button>
        </div>
      </div>

      {/* Breakdown */}
      <div style={s.card}>
        <h2 style={s.cardTitle}>📊 Payment Breakdown</h2>
        <div style={s.breakdownGrid}>
          <StatBox label="Principal Amount"  val={`₹${formatLakh(loan)}`}      color="#1a56db" bg="#eff6ff" />
          <StatBox label="Total Interest"    val={`₹${formatLakh(totalInt)}`}  color="#dc2626" bg="#fef2f2" />
          <StatBox label="Total Amount Paid" val={`₹${formatLakh(totalPay)}`}  color="#059669" bg="#f0fdf4" />
          <StatBox label="Monthly EMI"       val={`₹${emi.toLocaleString('en-IN')}`} color="#7c3aed" bg="#f5f3ff" />
        </div>

        {/* Visual bar */}
        <div style={{ marginTop: 24 }}>
          <div style={s.barLabel}>
            <span style={{ color: '#1a56db' }}>■ Principal {prinPct}%</span>
            <span style={{ color: '#dc2626' }}>■ Interest {intPct}%</span>
          </div>
          <div style={s.barTrack}>
            <div style={{ ...s.barFill, width: `${prinPct}%`, background: '#1a56db', borderRadius: '8px 0 0 8px' }} />
            <div style={{ ...s.barFill, width: `${intPct}%`, background: '#dc2626', borderRadius: '0 8px 8px 0' }} />
          </div>
        </div>

        {/* Amortisation preview */}
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', marginBottom: 10 }}>Year-by-Year Preview</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[1, 3, 5, 10, years].filter((y, i, a) => a.indexOf(y) === i && y <= years).map(y => {
              const paid = emi * y * 12
              const prinPaid = loan - calcRemainingPrincipal(loan, rate, years, y)
              return (
                <div key={y} style={s.amorRow}>
                  <span style={s.amorYr}>Year {y}</span>
                  <span style={s.amorPrin}>Principal: ₹{formatLakh(Math.max(0, prinPaid))}</span>
                  <span style={s.amorInt}>Interest: ₹{formatLakh(Math.max(0, paid - prinPaid))}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Loan Comparison tab ────────────────────────────────── */
function LoanComparison({ isMobile }) {
  const [amount, setAmount] = useState(5000000)
  const [tenure, setTenure] = useState(20)
  const [sortBy, setSortBy] = useState('rate')

  const sorted = [...BANKS].sort((a, b) => sortBy === 'rate' ? a.rate - b.rate : a.name.localeCompare(b.name))

  return (
    <div>
      <div style={s.card}>
        <h2 style={s.cardTitle}>🏦 Compare Home Loan Rates</h2>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
          <SliderField label="Loan Amount" value={amount} min={500000} max={50000000} step={100000}
            onChange={setAmount} display={`₹${formatLakh(amount)}`} />
          <SliderField label="Tenure (Years)" value={tenure} min={5} max={30} step={1}
            onChange={setTenure} display={`${tenure} Yrs`} />
          <div>
            <div style={s.fieldLabel}>Sort By</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              {['rate','name'].map(k => (
                <button key={k} onClick={() => setSortBy(k)}
                  style={{ ...s.sortBtn, ...(sortBy === k ? s.sortActive : {}) }}>
                  {k === 'rate' ? '⬆ Rate' : 'A–Z Name'}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill,minmax(320px,1fr))', gap: 16 }}>
          {sorted.map((b, i) => {
            const emi = calcEMI(amount, b.rate, tenure)
            const totalInt = (emi * tenure * 12) - amount
            return (
              <div key={b.name} style={{ ...s.bankCard, borderTop: `4px solid ${b.color}` }}>
                <div style={s.bankTop}>
                  <span style={s.bankLogo}>{b.logo}</span>
                  <div style={{ flex: 1 }}>
                    <div style={s.bankName}>{b.name}</div>
                    <span style={{ ...s.bankTag, background: `${b.color}18`, color: b.color }}>{b.tag}</span>
                  </div>
                  {i === 0 && <span style={s.bestTag}>Best</span>}
                </div>
                <div style={s.bankStats}>
                  <div style={s.bankStat}><span style={s.bsV}>{b.rate}%</span><span style={s.bsL}>Rate p.a.</span></div>
                  <div style={s.bsDivider} />
                  <div style={s.bankStat}><span style={s.bsV}>₹{emi.toLocaleString('en-IN')}</span><span style={s.bsL}>Monthly EMI</span></div>
                  <div style={s.bsDivider} />
                  <div style={s.bankStat}><span style={s.bsV}>₹{formatLakh(totalInt)}</span><span style={s.bsL}>Total Interest</span></div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button style={{ ...s.applyBtn, flex: 1, justifyContent: 'center' }}>Apply Now</button>
                  <button style={s.emiBtn}>EMI Details</button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

/* ── Insurance tab ──────────────────────────────────────── */
function InsuranceSection({ isMobile }) {
  const [selected, setSelected] = useState(null)
  return (
    <div>
      <div style={s.card}>
        <h2 style={s.cardTitle}>🛡️ Property Insurance Plans</h2>
        <p style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>
          Protect your biggest investment. Choose from fire, theft, natural disaster, and comprehensive cover options from India's top insurers.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill,minmax(280px,1fr))', gap: 20 }}>
          {INSURANCE.map(plan => (
            <div key={plan.name} onClick={() => setSelected(plan.name === selected ? null : plan.name)}
              style={{ ...s.insCard, ...(plan.name === selected ? { border: `2px solid ${plan.color}`, background: `${plan.color}06` } : {}) }}>
              <div style={s.insTop}>
                <span style={{ fontSize: 32 }}>{plan.icon}</span>
                <div>
                  <div style={s.insName}>{plan.name}</div>
                  <div style={s.insProv}>{plan.provider}</div>
                </div>
                <span style={{ ...s.insTag, background: `${plan.color}18`, color: plan.color }}>{plan.tag}</span>
              </div>
              <div style={s.insStats}>
                <div><div style={s.insStatV}>{plan.premium}</div><div style={s.insStatL}>Annual Premium</div></div>
                <div><div style={s.insStatV}>{plan.cover}</div><div style={s.insStatL}>Coverage</div></div>
              </div>
              {plan.name === selected && (
                <div style={s.insFeatures}>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>What's Covered</div>
                  {['Fire & Lightning','Natural Disasters','Theft & Burglary','Water Damage','Earthquake','Third-party Liability'].map(f => (
                    <div key={f} style={s.insFeature}>✓ {f}</div>
                  ))}
                </div>
              )}
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button style={{ ...s.applyBtn, flex: 1, justifyContent: 'center' }}>Get Quote</button>
                <button onClick={e => { e.stopPropagation(); setSelected(p => p === plan.name ? null : plan.name) }}
                  style={s.emiBtn}>{plan.name === selected ? 'Less ▲' : 'More ▼'}</button>
              </div>
            </div>
          ))}
        </div>

        {/* Info boxes */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3,1fr)', gap: 16, marginTop: 28, borderTop: '1px solid #e2e8f0', paddingTop: 24 }}>
          {[
            ['🏠', 'Structure Cover', 'Covers the physical structure of your home against damage from fire, storm, floods, and earthquakes.'],
            ['🛋️', 'Contents Cover', 'Covers furniture, appliances, electronics and personal belongings inside the property.'],
            ['🤝', 'Liability Cover', 'Covers legal liability if a visitor gets injured on your property.'],
          ].map(([icon, title, desc]) => (
            <div key={title} style={s.infoBadge}>
              <span style={{ fontSize: 24 }}>{icon}</span>
              <div style={{ fontWeight: 700, fontSize: 14, color: '#0f172a', marginBottom: 4 }}>{title}</div>
              <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.5 }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── Balance Transfer tab ───────────────────────────────── */
function BalanceTransfer({ isMobile }) {
  const [curLoan, setCurLoan]   = useState(3000000)
  const [curRate, setCurRate]   = useState(10.5)
  const [newRate, setNewRate]   = useState(8.5)
  const [remYrs, setRemYrs]     = useState(15)

  const curEMI      = calcEMI(curLoan, curRate, remYrs)
  const newEMI      = calcEMI(curLoan, newRate, remYrs)
  const savings     = (curEMI - newEMI) * remYrs * 12
  const monthlySave = curEMI - newEMI

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 28 }}>
      <div style={s.card}>
        <h2 style={s.cardTitle}>🔄 Balance Transfer Calculator</h2>
        <p style={{ color: '#64748b', fontSize: 14, marginBottom: 20 }}>
          Switch your existing home loan to a lender with a lower rate and save lakhs over the tenure.
        </p>
        <SliderField label="Outstanding Loan Balance" value={curLoan} min={100000} max={30000000} step={100000}
          onChange={setCurLoan} display={`₹${formatLakh(curLoan)}`} />
        <SliderField label="Current Interest Rate (%)" value={curRate} min={7} max={18} step={0.05}
          onChange={setCurRate} display={`${curRate.toFixed(2)}%`} />
        <SliderField label="New Rate Offered (%)" value={newRate} min={6} max={14} step={0.05}
          onChange={setNewRate} display={`${newRate.toFixed(2)}%`} />
        <SliderField label="Remaining Tenure" value={remYrs} min={1} max={30} step={1}
          onChange={setRemYrs} display={`${remYrs} Years`} />
      </div>

      <div style={s.card}>
        <h2 style={s.cardTitle}>💡 Savings Summary</h2>
        <div style={s.btSummary}>
          <div style={s.btRow}>
            <span style={s.btLabel}>Current EMI</span>
            <span style={{ ...s.btVal, color: '#dc2626' }}>₹{curEMI.toLocaleString('en-IN')}/mo</span>
          </div>
          <div style={s.btRow}>
            <span style={s.btLabel}>New EMI</span>
            <span style={{ ...s.btVal, color: '#059669' }}>₹{newEMI.toLocaleString('en-IN')}/mo</span>
          </div>
          <div style={{ ...s.btRow, background: '#f0fdf4', borderRadius: 10, padding: '12px 16px', border: '1px solid #bbf7d0' }}>
            <span style={{ ...s.btLabel, color: '#166534', fontWeight: 700 }}>Monthly Savings</span>
            <span style={{ ...s.btVal, color: '#059669', fontSize: 22 }}>₹{Math.max(0, monthlySave).toLocaleString('en-IN')}/mo</span>
          </div>
          <div style={{ ...s.btRow, background: '#eff6ff', borderRadius: 10, padding: '12px 16px', border: '1px solid #bfdbfe' }}>
            <span style={{ ...s.btLabel, color: '#1e3a8a', fontWeight: 700 }}>Total Savings</span>
            <span style={{ ...s.btVal, color: '#1a56db', fontSize: 22 }}>₹{formatLakh(Math.max(0, savings))}</span>
          </div>
        </div>

        {monthlySave > 0 ? (
          <>
            <div style={s.savingsBadge}>
              🎉 You can save <strong>₹{formatLakh(savings)}</strong> over {remYrs} years by switching!
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 16 }}>
              {BANKS.slice(0,4).map(b => (
                <div key={b.name} style={s.btBank} onClick={() => {}}>
                  <span style={{ fontSize: 20 }}>{b.logo}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0f172a' }}>{b.name}</div>
                    <div style={{ fontSize: 11, color: '#059669', fontWeight: 700 }}>{b.rate}% p.a.</div>
                  </div>
                  <span style={{ fontSize: 11, color: '#1a56db', fontWeight: 700 }}>Apply →</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ ...s.savingsBadge, background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }}>
            ⚠️ New rate must be lower than current rate to save money.
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Shared sub-components ───────────────────────────────── */
function SliderField({ label, value, min, max, step, onChange, display }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <label style={s.fieldLabel}>{label}</label>
        <span style={s.fieldVal}>{display}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(+e.target.value)} style={s.range} />
      <div style={s.rangeLabels}>
        <span>{typeof min === 'number' && min >= 100000 ? `₹${formatLakh(min)}` : min}</span>
        <span>{typeof max === 'number' && max >= 100000 ? `₹${formatLakh(max)}` : max}</span>
      </div>
    </div>
  )
}

function StatBox({ label, val, color, bg }) {
  return (
    <div style={{ background: bg, borderRadius: 12, padding: '16px', border: `1px solid ${color}22` }}>
      <div style={{ fontSize: 18, fontWeight: 800, color, letterSpacing: '-0.5px' }}>{val}</div>
      <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{label}</div>
    </div>
  )
}

/* ── Helpers ─────────────────────────────────────────────── */
function calcEMI(p, r, y) {
  const n = y * 12
  const mRate = r / 12 / 100
  if (mRate === 0) return Math.round(p / n)
  return Math.round(p * mRate * Math.pow(1 + mRate, n) / (Math.pow(1 + mRate, n) - 1))
}

function calcRemainingPrincipal(p, r, totalYears, yearsGone) {
  const n = totalYears * 12
  const m = yearsGone * 12
  const mRate = r / 12 / 100
  if (mRate === 0) return p - (p / n) * m
  const emi = calcEMI(p, r, totalYears)
  return emi * (1 - Math.pow(1 + mRate, -(n - m))) / mRate
}

function formatLakh(n) {
  if (n >= 10000000) return `${(n / 10000000).toFixed(2)} Cr`
  if (n >= 100000)   return `${(n / 100000).toFixed(1)} L`
  return n.toLocaleString('en-IN')
}

/* ── Styles ──────────────────────────────────────────────── */
const s = {
  page:         { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  hero:         { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 60%,#0e3a8c 100%)', color: '#fff', padding: '3rem 0' },
  heroInner:    { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', gap: 40, alignItems: 'center', flexWrap: 'wrap' },
  heroLeft:     { flex: 1, minWidth: 280 },
  heroBadge:    { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600, marginBottom: 16 },
  heroH1:       { fontSize: 'clamp(26px,4vw,42px)', fontWeight: 900, margin: '0 0 12px', letterSpacing: '-1px', lineHeight: 1.15 },
  heroP:        { fontSize: 16, opacity: 0.8, marginBottom: 28, lineHeight: 1.6 },
  heroStats:    { display: 'flex', gap: 24, flexWrap: 'wrap' },
  hStat:        { display: 'flex', flexDirection: 'column', gap: 2 },
  hStatVal:     { fontSize: 22, fontWeight: 800, letterSpacing: '-0.5px' },
  hStatLbl:     { fontSize: 12, opacity: 0.65 },
  heroRight:    { width: 340, flexShrink: 0 },
  quickBox:     { background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '24px' },
  qTitle:       { fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 20 },
  qRow:         { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  qLabel:       { fontSize: 12, color: 'rgba(255,255,255,0.7)' },
  qVal:         { fontSize: 14, fontWeight: 700, color: '#fff' },
  range:        { width: '100%', accentColor: '#60a5fa', marginBottom: 16, cursor: 'pointer' },
  qResult:      { background: 'rgba(255,255,255,0.15)', borderRadius: 12, padding: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  qResultLabel: { fontSize: 12, color: 'rgba(255,255,255,0.7)' },
  qResultVal:   { fontSize: 24, fontWeight: 900, color: '#fff', letterSpacing: '-1px' },
  qMeta:        { fontSize: 11, color: 'rgba(255,255,255,0.55)', marginTop: 8, textAlign: 'right' },
  tabBar:       { background: '#fff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 60, zIndex: 100, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' },
  tabInner:     { maxWidth: 1240, margin: '0 auto', padding: '0 1.5rem', display: 'flex', overflowX: 'auto' },
  tabBtn:       { background: 'none', border: 'none', padding: '14px 20px', fontSize: 14, fontWeight: 600, color: '#64748b', cursor: 'pointer', whiteSpace: 'nowrap', borderBottom: '3px solid transparent', transition: 'all 0.15s' },
  tabActive:    { color: '#1a56db', borderBottom: '3px solid #1a56db' },
  wrap:         { maxWidth: 1240, margin: '0 auto', padding: '2.5rem 1.5rem' },
  card:         { background: '#fff', borderRadius: 18, padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' },
  cardTitle:    { fontSize: 20, fontWeight: 800, color: '#0f172a', margin: '0 0 24px', letterSpacing: '-0.3px' },
  fieldLabel:   { fontSize: 13, fontWeight: 700, color: '#374151' },
  fieldVal:     { fontSize: 15, fontWeight: 800, color: '#1a56db' },
  rangeLabels:  { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#94a3b8', marginTop: -10 },
  emiResult:    { display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#eff6ff', borderRadius: 14, padding: '18px 20px', border: '1px solid #bfdbfe', marginTop: 8 },
  emiLabel:     { fontSize: 13, color: '#1e40af', fontWeight: 600 },
  emiVal:       { fontSize: 30, fontWeight: 900, color: '#1a56db', letterSpacing: '-1px' },
  applyBtn:     { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 10, padding: '10px 18px', fontWeight: 700, fontSize: 13, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6, boxShadow: '0 2px 8px rgba(26,86,219,0.3)' },
  breakdownGrid:{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 },
  barLabel:     { display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, marginBottom: 8 },
  barTrack:     { display: 'flex', height: 12, borderRadius: 8, overflow: 'hidden' },
  barFill:      { height: '100%', transition: 'width 0.4s ease' },
  amorRow:      { display: 'flex', gap: 12, fontSize: 12, color: '#374151', padding: '6px 10px', background: '#f8fafc', borderRadius: 8, flexWrap: 'wrap' },
  amorYr:       { fontWeight: 700, color: '#0f172a', minWidth: 50 },
  amorPrin:     { color: '#1a56db' },
  amorInt:      { color: '#dc2626' },
  sortBtn:      { border: '1.5px solid #e2e8f0', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer', background: '#f8fafc', color: '#374151' },
  sortActive:   { border: '1.5px solid #1a56db', background: '#eff6ff', color: '#1a56db' },
  bankCard:     { background: '#fff', borderRadius: 14, padding: '20px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: 14 },
  bankTop:      { display: 'flex', alignItems: 'center', gap: 12 },
  bankLogo:     { fontSize: 28, flexShrink: 0 },
  bankName:     { fontSize: 15, fontWeight: 800, color: '#0f172a' },
  bankTag:      { fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 20, display: 'inline-block', marginTop: 4 },
  bestTag:      { background: '#fef3c7', color: '#92400e', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 20, height: 'fit-content' },
  bankStats:    { display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#f8fafc', borderRadius: 10, padding: '12px' },
  bankStat:     { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 },
  bsV:          { fontSize: 15, fontWeight: 800, color: '#0f172a' },
  bsL:          { fontSize: 11, color: '#94a3b8' },
  bsDivider:    { width: 1, height: 28, background: '#e2e8f0' },
  emiBtn:       { border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '10px 14px', fontSize: 12, fontWeight: 700, cursor: 'pointer', background: '#f8fafc', color: '#374151' },
  insCard:      { background: '#fff', borderRadius: 16, padding: '20px', border: '1px solid #e2e8f0', cursor: 'pointer', transition: 'all 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  insTop:       { display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 16 },
  insName:      { fontSize: 15, fontWeight: 800, color: '#0f172a' },
  insProv:      { fontSize: 12, color: '#64748b', marginTop: 2 },
  insTag:       { fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 20, whiteSpace: 'nowrap', flexShrink: 0 },
  insStats:     { display: 'flex', gap: 24, marginBottom: 8 },
  insStatV:     { fontSize: 18, fontWeight: 800, color: '#0f172a' },
  insStatL:     { fontSize: 11, color: '#64748b' },
  insFeatures:  { background: '#f8fafc', borderRadius: 10, padding: '14px', marginTop: 12 },
  insFeature:   { fontSize: 13, color: '#374151', padding: '3px 0' },
  infoBadge:    { background: '#f8fafc', borderRadius: 14, padding: '20px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: 8 },
  btSummary:    { display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 },
  btRow:        { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  btLabel:      { fontSize: 14, color: '#64748b' },
  btVal:        { fontSize: 18, fontWeight: 800 },
  savingsBadge: { background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 12, padding: '14px 16px', fontSize: 14, color: '#166534', lineHeight: 1.5, textAlign: 'center' },
  btBank:       { display: 'flex', alignItems: 'center', gap: 10, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: '12px', cursor: 'pointer', transition: 'all 0.15s' },
}
