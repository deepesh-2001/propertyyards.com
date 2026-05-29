import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const OFFICES = [
  { city: 'Gurgaon (HQ)', address: 'DLF Cyber City, Phase 2, Gurugram, Haryana 122002', phone: '+91 124 456 7890', email: 'gurgaon@propertyyards.com', hours: 'Mon–Sat 9am–7pm' },
  { city: 'Mumbai',        address: 'Bandra Kurla Complex, Bandra East, Mumbai 400051',  phone: '+91 22 456 7891',  email: 'mumbai@propertyyards.com',   hours: 'Mon–Sat 9am–7pm' },
  { city: 'Bangalore',     address: 'Outer Ring Road, Marathahalli, Bengaluru 560037',   phone: '+91 80 456 7892',  email: 'bangalore@propertyyards.com', hours: 'Mon–Sat 9am–7pm' },
]

const FAQS = [
  { q: 'How do I list a property on PropertyYards?', a: 'Click "Post Property" in the navbar, fill out the details form, and submit. Your listing goes live within minutes after review.' },
  { q: 'Are all brokers RERA verified?', a: 'Yes. Every broker on our platform is RERA-certified. We verify license numbers before any agent can list properties.' },
  { q: 'How does the AI-generated description work?', a: 'When you post a property, our AI analyzes the specs (area, location, bedrooms) and generates a detailed, engaging description. You can edit it before publishing.' },
  { q: 'Is PropertyYards free for buyers and renters?', a: 'Completely free for buyers, renters, and people looking to contact brokers. Only agents pay a small listing fee.' },
  { q: 'Can I get a home loan through PropertyYards?', a: 'Yes! Visit our Finance section to compare home loans from 6+ banks, calculate EMIs, and apply directly through our partner banks.' },
]

export default function Contact() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()

  const [form, setForm]     = useState({ name: '', email: '', phone: '', subject: 'General Enquiry', message: '' })
  const [sending, setSending] = useState(false)
  const [sent, setSent]       = useState(false)
  const [openFaq, setOpenFaq] = useState(null)

  const set = f => e => setForm(p => ({ ...p, [f]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setSending(true)
    await new Promise(r => setTimeout(r, 1200))
    setSending(false)
    setSent(true)
    toast('✅ Message sent! We\'ll get back to you within 24 hours.', 'success')
  }

  return (
    <div style={s.page}>
      {/* Hero */}
      <div style={s.hero}>
        <div style={s.heroInner}>
          <div style={s.heroBadge}>📞 Contact Us</div>
          <h1 style={s.heroH1}>We're Here to Help</h1>
          <p style={s.heroP}>Have a question about a listing, need help with a loan, or want to partner with us? Reach out — we respond within 24 hours.</p>
        </div>
      </div>

      {/* Quick contact cards */}
      <div style={s.quickCards}>
        {[
          { icon: '📞', label: 'Call Us',         val: '+91 124 456 7890',           sub: 'Mon–Sat, 9am–7pm IST' },
          { icon: '✉️', label: 'Email Us',         val: 'support@propertyyards.com',  sub: 'Reply within 24 hours' },
          { icon: '💬', label: 'WhatsApp',         val: '+91 98100 00001',            sub: 'Quick replies, 24×7' },
          { icon: '🏢', label: 'Visit Our Office', val: 'Gurgaon / Mumbai / Bengaluru', sub: 'By appointment' },
        ].map(({ icon, label, val, sub }) => (
          <div key={label} style={s.qCard}>
            <div style={s.qIcon}>{icon}</div>
            <div style={s.qLabel}>{label}</div>
            <div style={s.qVal}>{val}</div>
            <div style={s.qSub}>{sub}</div>
          </div>
        ))}
      </div>

      <div style={s.wrap}>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 420px', gap: 32 }}>

          {/* Contact Form */}
          <div style={s.card}>
            <h2 style={s.cardTitle}>Send Us a Message</h2>
            {sent ? (
              <div style={s.successBox}>
                <div style={{ fontSize: 52 }}>✅</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#065f46' }}>Message Sent!</div>
                <div style={{ fontSize: 14, color: '#4b7a5c', lineHeight: 1.6 }}>
                  Thank you, <strong>{form.name}</strong>. Our team will get back to you at <strong>{form.email}</strong> within 24 hours.
                </div>
                <button onClick={() => { setSent(false); setForm({ name:'', email:'', phone:'', subject:'General Enquiry', message:'' }) }}
                  style={s.resetBtn}>Send Another Message</button>
              </div>
            ) : (
              <form onSubmit={submit} style={s.form}>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 16 }}>
                  <FormField label="Full Name *">
                    <input required placeholder="Your full name" value={form.name} onChange={set('name')} style={s.input} />
                  </FormField>
                  <FormField label="Email Address *">
                    <input required type="email" placeholder="you@email.com" value={form.email} onChange={set('email')} style={s.input} />
                  </FormField>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 16 }}>
                  <FormField label="Phone Number">
                    <input placeholder="+91 98XXXXXXXX" value={form.phone} onChange={set('phone')} style={s.input} />
                  </FormField>
                  <FormField label="Subject *">
                    <select value={form.subject} onChange={set('subject')} style={s.input}>
                      {['General Enquiry','Property Listing Help','Home Loan Query','Broker Partnership','Bug Report','Other'].map(o => (
                        <option key={o}>{o}</option>
                      ))}
                    </select>
                  </FormField>
                </div>
                <FormField label="Message *">
                  <textarea required placeholder="Describe your query in detail..." value={form.message} onChange={set('message')}
                    rows={5} style={{ ...s.input, resize: 'vertical' }} />
                </FormField>
                <button type="submit" disabled={sending} style={s.submitBtn}>
                  {sending ? '⏳ Sending...' : '📩 Send Message'}
                </button>
              </form>
            )}
          </div>

          {/* Offices */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={s.card}>
              <h2 style={s.cardTitle}>Our Offices</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {OFFICES.map(o => (
                  <div key={o.city} style={s.officeRow}>
                    <div style={s.officeCity}>📍 {o.city}</div>
                    <div style={s.officeAddr}>{o.address}</div>
                    <div style={s.officeMeta}>
                      <a href={`tel:${o.phone}`} style={s.officeLink}>📞 {o.phone}</a>
                      <a href={`mailto:${o.email}`} style={s.officeLink}>✉️ {o.email}</a>
                      <span style={s.officeHours}>🕐 {o.hours}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Social links */}
            <div style={s.card}>
              <h2 style={{ ...s.cardTitle, marginBottom: 16 }}>Connect on Social</h2>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { icon: '📘', label: 'Facebook',  color: '#1877f2' },
                  { icon: '📸', label: 'Instagram',  color: '#e1306c' },
                  { icon: '🐦', label: 'Twitter/X',  color: '#000' },
                  { icon: '💼', label: 'LinkedIn',   color: '#0a66c2' },
                  { icon: '📺', label: 'YouTube',    color: '#ff0000' },
                  { icon: '💬', label: 'WhatsApp',   color: '#25d366' },
                ].map(({ icon, label, color }) => (
                  <button key={label} style={{ ...s.socialBtn, borderColor: `${color}33`, color }}>
                    {icon} {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* FAQ */}
        <div style={{ ...s.card, marginTop: 32 }}>
          <h2 style={s.cardTitle}>Frequently Asked Questions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {FAQS.map((faq, i) => (
              <div key={i} style={s.faqItem}>
                <button onClick={() => setOpenFaq(openFaq === i ? null : i)} style={s.faqQ}>
                  <span>{faq.q}</span>
                  <span style={{ fontSize: 18, transition: 'transform 0.2s', transform: openFaq === i ? 'rotate(180deg)' : 'none' }}>▾</span>
                </button>
                {openFaq === i && (
                  <div style={s.faqA} className="fade-in">{faq.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function FormField({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 13, fontWeight: 700, color: '#374151' }}>{label}</label>
      {children}
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  hero:        { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 60%,#0e3a8c 100%)', color: '#fff', padding: '4rem 0 3rem' },
  heroInner:   { maxWidth: 700, margin: '0 auto', padding: '0 1.5rem', textAlign: 'center' },
  heroBadge:   { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600, marginBottom: 16 },
  heroH1:      { fontSize: 'clamp(26px,5vw,44px)', fontWeight: 900, margin: '0 0 12px', letterSpacing: '-1px' },
  heroP:       { fontSize: 16, opacity: 0.8, lineHeight: 1.6, margin: 0 },
  quickCards:  { maxWidth: 1240, margin: '-40px auto 0', padding: '0 1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 16, position: 'relative', zIndex: 10 },
  qCard:       { background: '#fff', borderRadius: 16, padding: '24px 20px', border: '1px solid #e2e8f0', textAlign: 'center', boxShadow: '0 4px 20px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column', gap: 4 },
  qIcon:       { fontSize: 32, marginBottom: 4 },
  qLabel:      { fontSize: 11, fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 },
  qVal:        { fontSize: 14, fontWeight: 700, color: '#0f172a' },
  qSub:        { fontSize: 12, color: '#94a3b8' },
  wrap:        { maxWidth: 1240, margin: '0 auto', padding: '2.5rem 1.5rem', marginTop: 28 },
  card:        { background: '#fff', borderRadius: 18, padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  cardTitle:   { fontSize: 20, fontWeight: 800, color: '#0f172a', margin: '0 0 24px', letterSpacing: '-0.3px' },
  form:        { display: 'flex', flexDirection: 'column', gap: 18 },
  input:       { border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '11px 14px', fontSize: 14, outline: 'none', fontFamily: 'inherit', width: '100%', boxSizing: 'border-box', background: '#fafafa' },
  submitBtn:   { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 15, fontWeight: 800, cursor: 'pointer', boxShadow: '0 4px 16px rgba(26,86,219,0.3)', letterSpacing: '-0.3px' },
  successBox:  { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, padding: '24px 0', textAlign: 'center' },
  resetBtn:    { background: '#eff6ff', color: '#1a56db', border: 'none', borderRadius: 10, padding: '10px 22px', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginTop: 8 },
  officeRow:   { paddingBottom: 16, borderBottom: '1px solid #f1f5f9' },
  officeCity:  { fontSize: 15, fontWeight: 800, color: '#0f172a', marginBottom: 4 },
  officeAddr:  { fontSize: 13, color: '#64748b', marginBottom: 8, lineHeight: 1.5 },
  officeMeta:  { display: 'flex', flexDirection: 'column', gap: 4 },
  officeLink:  { fontSize: 13, color: '#1a56db', textDecoration: 'none', fontWeight: 600 },
  officeHours: { fontSize: 12, color: '#94a3b8' },
  socialBtn:   { display: 'flex', alignItems: 'center', gap: 8, background: '#fafafa', border: '1.5px solid', borderRadius: 10, padding: '10px 14px', fontSize: 14, fontWeight: 700, cursor: 'pointer' },
  faqItem:     { borderBottom: '1px solid #f1f5f9' },
  faqQ:        { width: '100%', background: 'none', border: 'none', padding: '16px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, cursor: 'pointer', fontSize: 15, fontWeight: 700, color: '#0f172a', textAlign: 'left' },
  faqA:        { fontSize: 14, color: '#374151', lineHeight: 1.7, paddingBottom: 16, paddingLeft: 4 },
}
