import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const PIPELINE = ['New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost']
const PIPELINE_COLORS = { New:'#6366f1', Contacted:'#0284c7', Qualified:'#f59e0b', Proposal:'#7c3aed', Negotiation:'#f97316', Won:'#059669', Lost:'#dc2626' }

const INITIAL_LEADS = [
  { id: 1, name: 'Rajesh Kumar',   email: 'rajesh@email.com', phone: '+91 98100 11234', status: 'New',         source: 'Website',      interest: '3BHK in Gurgaon',   budget: '1.2 Cr', lastContact: '2025-05-28', score: 82 },
  { id: 2, name: 'Priya Singh',    email: 'priya@email.com',  phone: '+91 98200 22345', status: 'Contacted',   source: 'Referral',     interest: '2BHK in Noida',     budget: '65 L',   lastContact: '2025-05-27', score: 67 },
  { id: 3, name: 'Amit Verma',     email: 'amit@email.com',   phone: '+91 98300 33456', status: 'Qualified',   source: 'Paid Ad',      interest: 'Villa in Gurgaon',  budget: '3.5 Cr', lastContact: '2025-05-26', score: 91 },
  { id: 4, name: 'Sunita Patel',   email: 'sunita@email.com', phone: '+91 98400 44567', status: 'Proposal',    source: 'Social Media', interest: '4BHK in Mumbai',    budget: '4.2 Cr', lastContact: '2025-05-25', score: 88 },
  { id: 5, name: 'Deepak Sharma',  email: 'deepak@email.com', phone: '+91 98500 55678', status: 'Negotiation', source: 'Website',      interest: 'Commercial Space',  budget: '8 Cr',   lastContact: '2025-05-24', score: 94 },
  { id: 6, name: 'Anita Joshi',    email: 'anita@email.com',  phone: '+91 98600 66789', status: 'Won',         source: 'Referral',     interest: '3BHK in Bangalore', budget: '1.8 Cr', lastContact: '2025-05-23', score: 100 },
  { id: 7, name: 'Vikram Nair',    email: 'vikram@email.com', phone: '+91 98700 77890', status: 'Lost',        source: 'Email',        interest: '2BHK in Pune',      budget: '55 L',   lastContact: '2025-05-20', score: 30 },
  { id: 8, name: 'Meera Reddy',    email: 'meera@email.com',  phone: '+91 98800 88901', status: 'New',         source: 'Website',      interest: 'Plot in Hyderabad', budget: '90 L',   lastContact: '2025-05-29', score: 73 },
  { id: 9, name: 'Karthik Raja',   email: 'karthik@email.com',phone: '+91 98900 99012', status: 'Contacted',   source: 'Paid Ad',      interest: '3BHK in Chennai',   budget: '1.1 Cr', lastContact: '2025-05-28', score: 61 },
]

const INTERACTIONS = [
  { id: 1, leadId: 1, type: 'Call',    note: 'Discussed 3BHK options in Sector 45. Interested in Godrej Horizon.', date: '2025-05-28 14:30', by: 'Rahul Sharma' },
  { id: 2, leadId: 2, type: 'Email',   note: 'Sent property brochures. Awaiting response.', date: '2025-05-27 10:00', by: 'Priya Verma' },
  { id: 3, leadId: 3, type: 'Meeting', note: 'Site visit to DLF The Arbour completed. Client loved the project.', date: '2025-05-26 11:00', by: 'Rahul Sharma' },
  { id: 4, leadId: 5, type: 'Follow Up', note: 'Price negotiation in progress. Client requesting 5% discount.', date: '2025-05-24 16:00', by: 'Vikram Singh' },
]

export default function CRM() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()
  const [leads, setLeads]       = useState(INITIAL_LEADS)
  const [view,  setView]        = useState('kanban')
  const [search, setSearch]     = useState('')
  const [selectedLead, setSelectedLead] = useState(null)
  const [showAdd,  setShowAdd]  = useState(false)
  const [newLead, setNewLead]   = useState({ name:'', email:'', phone:'', interest:'', budget:'', source:'Website', status:'New' })

  const filtered = leads.filter(l =>
    !search || l.name.toLowerCase().includes(search.toLowerCase()) ||
    l.email.toLowerCase().includes(search.toLowerCase()) ||
    l.interest.toLowerCase().includes(search.toLowerCase())
  )

  const byStatus = (status) => filtered.filter(l => l.status === status)

  const moveLead = (id, newStatus) => {
    setLeads(prev => prev.map(l => l.id === id ? { ...l, status: newStatus } : l))
    toast(`Lead moved to ${newStatus}`, 'success')
  }

  const addLead = () => {
    if (!newLead.name || !newLead.phone) { toast('Name and phone are required', 'error'); return }
    setLeads(prev => [...prev, { ...newLead, id: Date.now(), lastContact: new Date().toISOString().slice(0,10), score: Math.floor(Math.random()*40)+50 }])
    toast('Lead added!', 'success')
    setShowAdd(false)
    setNewLead({ name:'', email:'', phone:'', interest:'', budget:'', source:'Website', status:'New' })
  }

  const wonCount  = leads.filter(l => l.status === 'Won').length
  const lostCount = leads.filter(l => l.status === 'Lost').length
  const convRate  = leads.length ? Math.round((wonCount / leads.length) * 100) : 0

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div>
            <h1 style={s.h1}>📋 CRM Dashboard</h1>
            <p style={s.sub}>Manage leads, track interactions, close more deals</p>
          </div>
          <div style={s.bannerActions}>
            <button onClick={() => setView(v => v === 'kanban' ? 'table' : 'kanban')} style={s.viewToggle}>
              {view === 'kanban' ? '📋 Table View' : '🗂 Kanban View'}
            </button>
            <button onClick={() => setShowAdd(true)} style={s.addBtn}>+ Add Lead</button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div style={s.statsBar}>
        <div style={s.statsInner}>
          {[
            { icon:'👥', label:'Total Leads',     val: leads.length,      color:'#1a56db' },
            { icon:'🔥', label:'Hot Leads (80+)', val: leads.filter(l=>l.score>=80).length, color:'#f59e0b' },
            { icon:'🏆', label:'Won',             val: wonCount,          color:'#059669' },
            { icon:'📉', label:'Lost',            val: lostCount,         color:'#dc2626' },
            { icon:'📈', label:'Conversion Rate', val: `${convRate}%`,    color:'#7c3aed' },
          ].map(stat => (
            <div key={stat.label} style={s.statCard}>
              <span style={{ fontSize: 22 }}>{stat.icon}</span>
              <div style={{ fontSize: 26, fontWeight: 900, color: stat.color, letterSpacing: '-1px' }}>{stat.val}</div>
              <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={s.wrap}>
        {/* Search */}
        <div style={s.searchRow}>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="🔍 Search leads by name, email, interest..."
            style={s.searchInput} />
        </div>

        {/* Kanban View */}
        {view === 'kanban' && (
          <div style={{ overflowX: 'auto' }}>
            <div style={s.kanban}>
              {PIPELINE.map(status => {
                const cols = byStatus(status)
                return (
                  <div key={status} style={s.kanbanCol}>
                    <div style={{ ...s.kanbanHeader, borderTop: `4px solid ${PIPELINE_COLORS[status]}` }}>
                      <span style={{ fontWeight: 800, fontSize: 14, color: '#0f172a' }}>{status}</span>
                      <span style={{ ...s.kanbanCount, background: `${PIPELINE_COLORS[status]}22`, color: PIPELINE_COLORS[status] }}>{cols.length}</span>
                    </div>
                    <div style={s.kanbanCards}>
                      {cols.map(lead => (
                        <LeadCard key={lead.id} lead={lead} onMove={moveLead} onSelect={setSelectedLead} />
                      ))}
                      {cols.length === 0 && <div style={s.emptyCol}>Drop leads here</div>}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Table View */}
        {view === 'table' && (
          <div style={{ overflowX: 'auto' }}>
            <table style={s.table}>
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  {['Name','Phone','Interest','Budget','Source','Status','Score','Last Contact','Actions'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((lead, i) => (
                  <tr key={lead.id} style={i%2===0?{}:{background:'#fafafa'}}>
                    <td style={s.td}>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{lead.name}</div>
                      <div style={{ fontSize: 12, color: '#64748b' }}>{lead.email}</div>
                    </td>
                    <td style={s.td}>{lead.phone}</td>
                    <td style={s.td}>{lead.interest}</td>
                    <td style={s.td}><span style={{ fontWeight: 700, color: '#1a56db' }}>{lead.budget}</span></td>
                    <td style={s.td}>{lead.source}</td>
                    <td style={s.td}>
                      <span style={{ ...s.statusChip, background: `${PIPELINE_COLORS[lead.status]}18`, color: PIPELINE_COLORS[lead.status] }}>
                        {lead.status}
                      </span>
                    </td>
                    <td style={s.td}>
                      <div style={s.scoreWrap}>
                        <div style={{ ...s.scoreFill, width: `${lead.score}%`, background: lead.score>=80?'#059669':lead.score>=50?'#f59e0b':'#dc2626' }} />
                        <span style={{ fontSize: 12, fontWeight: 700, marginLeft: 6 }}>{lead.score}</span>
                      </div>
                    </td>
                    <td style={s.td}>{lead.lastContact}</td>
                    <td style={s.td}>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={() => setSelectedLead(lead)} style={s.actionBtn}>👁 View</button>
                        <select value={lead.status} onChange={e => moveLead(lead.id, e.target.value)} style={s.moveSelect}>
                          {PIPELINE.map(p => <option key={p}>{p}</option>)}
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <div style={s.overlay} onClick={() => setSelectedLead(null)}>
          <div style={s.modal} onClick={e => e.stopPropagation()} className="fade-in">
            <div style={s.modalHeader}>
              <div>
                <h3 style={s.modalTitle}>{selectedLead.name}</h3>
                <span style={{ ...s.statusChip, background: `${PIPELINE_COLORS[selectedLead.status]}18`, color: PIPELINE_COLORS[selectedLead.status] }}>
                  {selectedLead.status}
                </span>
              </div>
              <button onClick={() => setSelectedLead(null)} style={s.closeBtn}>✕</button>
            </div>
            <div style={s.modalBody}>
              <div style={s.detailGrid}>
                {[['📧 Email', selectedLead.email],['📞 Phone', selectedLead.phone],['🏠 Interest', selectedLead.interest],['💰 Budget', selectedLead.budget],['📢 Source', selectedLead.source],['📅 Last Contact', selectedLead.lastContact]].map(([k,v]) => (
                  <div key={k} style={s.detailItem}>
                    <div style={s.detailLabel}>{k}</div>
                    <div style={s.detailVal}>{v}</div>
                  </div>
                ))}
              </div>
              <div style={s.modalSection}>Interaction History</div>
              {INTERACTIONS.filter(i => i.leadId === selectedLead.id).map(intr => (
                <div key={intr.id} style={s.intrCard}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={s.intrType}>{intr.type}</span>
                    <span style={{ fontSize: 12, color: '#94a3b8' }}>{intr.date}</span>
                  </div>
                  <div style={{ fontSize: 14, color: '#374151' }}>{intr.note}</div>
                  <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>by {intr.by}</div>
                </div>
              ))}
              <div style={s.moveRow}>
                <span style={{ fontSize: 14, fontWeight: 700 }}>Move to:</span>
                {PIPELINE.filter(p => p !== selectedLead.status).map(p => (
                  <button key={p} onClick={() => { moveLead(selectedLead.id, p); setSelectedLead(null) }}
                    style={{ ...s.moveBtn, background: `${PIPELINE_COLORS[p]}18`, color: PIPELINE_COLORS[p], border: `1px solid ${PIPELINE_COLORS[p]}44` }}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Lead Modal */}
      {showAdd && (
        <div style={s.overlay} onClick={() => setShowAdd(false)}>
          <div style={{ ...s.modal, maxWidth: 520 }} onClick={e => e.stopPropagation()} className="fade-in">
            <div style={s.modalHeader}>
              <h3 style={s.modalTitle}>Add New Lead</h3>
              <button onClick={() => setShowAdd(false)} style={s.closeBtn}>✕</button>
            </div>
            <div style={s.modalBody}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[['Name *','name','text'],['Email','email','email'],['Phone *','phone','tel'],['Property Interest','interest','text'],['Budget','budget','text']].map(([label,field,type]) => (
                  <div key={field}>
                    <label style={s.fieldLabel}>{label}</label>
                    <input type={type} value={newLead[field]} onChange={e => setNewLead(p=>({...p,[field]:e.target.value}))}
                      placeholder={label.replace(' *','')} style={s.fieldInput} />
                  </div>
                ))}
                <div>
                  <label style={s.fieldLabel}>Source</label>
                  <select value={newLead.source} onChange={e => setNewLead(p=>({...p,source:e.target.value}))} style={s.fieldInput}>
                    {['Website','Referral','Paid Ad','Social Media','Email','Direct','Other'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <button onClick={addLead} style={s.submitBtn}>Add Lead →</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function LeadCard({ lead, onMove, onSelect }) {
  return (
    <div style={s.leadCard} onClick={() => onSelect(lead)} className="fade-in">
      <div style={s.leadTop}>
        <div style={s.leadAvatar}>{lead.name[0]}</div>
        <div style={{ flex: 1 }}>
          <div style={s.leadName}>{lead.name}</div>
          <div style={s.leadPhone}>{lead.phone}</div>
        </div>
        <div style={{ ...s.scoreCircle, background: lead.score>=80?'#d1fae5':lead.score>=50?'#fef3c7':'#fee2e2', color: lead.score>=80?'#065f46':lead.score>=50?'#92400e':'#991b1b' }}>
          {lead.score}
        </div>
      </div>
      <div style={s.leadInterest}>{lead.interest}</div>
      <div style={s.leadBudget}>💰 {lead.budget}</div>
      <div style={s.leadMeta}>
        <span style={s.leadSource}>{lead.source}</span>
        <span style={{ fontSize: 11, color: '#94a3b8' }}>{lead.lastContact}</span>
      </div>
      <select value={lead.status} onChange={e => { e.stopPropagation(); onMove(lead.id, e.target.value) }}
        onClick={e => e.stopPropagation()} style={s.moveSelect}>
        {PIPELINE.map(p => <option key={p}>{p}</option>)}
      </select>
    </div>
  )
}

const s = {
  page:        { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:      { background: 'linear-gradient(135deg,#0f172a 0%,#1a56db 100%)', color: '#fff', padding: '2rem 0' },
  bannerInner: { maxWidth: 1440, margin: '0 auto', padding: '0 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 },
  h1:          { fontSize: 'clamp(20px,3vw,28px)', fontWeight: 900, margin: 0 },
  sub:         { fontSize: 13, opacity: 0.75, marginTop: 4 },
  bannerActions:{ display: 'flex', gap: 10 },
  viewToggle:  { background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)', color: '#fff', borderRadius: 10, padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  addBtn:      { background: '#fff', color: '#1a56db', border: 'none', borderRadius: 10, padding: '9px 20px', fontWeight: 800, fontSize: 14, cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' },
  statsBar:    { background: '#fff', borderBottom: '1px solid #e2e8f0', boxShadow: '0 1px 8px rgba(0,0,0,0.04)' },
  statsInner:  { maxWidth: 1440, margin: '0 auto', padding: '0 1.5rem', display: 'flex', gap: 0, justifyContent: 'space-around', flexWrap: 'wrap' },
  statCard:    { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '20px 16px' },
  wrap:        { maxWidth: 1440, margin: '0 auto', padding: '1.5rem' },
  searchRow:   { marginBottom: 20 },
  searchInput: { width: '100%', border: '1.5px solid #e2e8f0', borderRadius: 12, padding: '11px 16px', fontSize: 14, outline: 'none', boxSizing: 'border-box', background: '#fff' },
  kanban:      { display: 'flex', gap: 16, minWidth: 1100 },
  kanbanCol:   { flex: 1, minWidth: 160, background: '#f1f5f9', borderRadius: 14, padding: '12px', display: 'flex', flexDirection: 'column', gap: 0 },
  kanbanHeader:{ background: '#fff', borderRadius: 10, padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, boxShadow: '0 1px 4px rgba(0,0,0,0.05)' },
  kanbanCount: { borderRadius: 20, padding: '2px 10px', fontSize: 12, fontWeight: 800 },
  kanbanCards: { display: 'flex', flexDirection: 'column', gap: 8, flex: 1 },
  emptyCol:    { fontSize: 12, color: '#94a3b8', textAlign: 'center', padding: '20px 0', border: '2px dashed #e2e8f0', borderRadius: 10 },
  leadCard:    { background: '#fff', borderRadius: 12, padding: '14px', border: '1px solid #e2e8f0', cursor: 'pointer', transition: 'box-shadow 0.15s', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' },
  leadTop:     { display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 },
  leadAvatar:  { width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg,#1a56db,#7c3aed)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 14, flexShrink: 0 },
  leadName:    { fontSize: 13, fontWeight: 800, color: '#0f172a', lineHeight: 1.3 },
  leadPhone:   { fontSize: 11, color: '#64748b' },
  scoreCircle: { borderRadius: '50%', width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 900, flexShrink: 0 },
  leadInterest:{ fontSize: 12, color: '#374151', marginBottom: 4 },
  leadBudget:  { fontSize: 13, fontWeight: 800, color: '#1a56db', marginBottom: 6 },
  leadMeta:    { display: 'flex', justifyContent: 'space-between', marginBottom: 8 },
  leadSource:  { fontSize: 11, background: '#eff6ff', color: '#1d4ed8', borderRadius: 20, padding: '2px 8px', fontWeight: 600 },
  moveSelect:  { width: '100%', border: '1px solid #e2e8f0', borderRadius: 8, padding: '5px 8px', fontSize: 12, background: '#f8fafc', cursor: 'pointer', outline: 'none' },
  table:       { width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 16, overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: '0 1px 8px rgba(0,0,0,0.05)' },
  th:          { padding: '12px 14px', textAlign: 'left', fontSize: 12, fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5, borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' },
  td:          { padding: '13px 14px', fontSize: 14, color: '#0f172a', borderBottom: '1px solid #f1f5f9', verticalAlign: 'middle' },
  statusChip:  { borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 700 },
  scoreWrap:   { display: 'flex', alignItems: 'center', background: '#f1f5f9', borderRadius: 99, height: 8, width: 80, overflow: 'hidden', position: 'relative' },
  scoreFill:   { height: '100%', borderRadius: 99 },
  actionBtn:   { background: '#eff6ff', color: '#1a56db', border: 'none', borderRadius: 8, padding: '5px 10px', fontSize: 12, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' },
  overlay:     { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' },
  modal:       { background: '#fff', borderRadius: 20, width: '100%', maxWidth: 680, maxHeight: '85vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 24px 80px rgba(0,0,0,0.3)' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '20px 24px', borderBottom: '1px solid #e2e8f0' },
  modalTitle:  { fontSize: 20, fontWeight: 900, color: '#0f172a', margin: '0 0 8px' },
  closeBtn:    { background: '#f1f5f9', border: 'none', borderRadius: 8, padding: '6px 12px', cursor: 'pointer', fontSize: 16, fontWeight: 700, flexShrink: 0 },
  modalBody:   { overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 },
  detailGrid:  { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  detailItem:  { background: '#f8fafc', borderRadius: 10, padding: '12px' },
  detailLabel: { fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 },
  detailVal:   { fontSize: 14, fontWeight: 700, color: '#0f172a' },
  modalSection:{ fontSize: 13, fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, paddingTop: 4 },
  intrCard:    { background: '#f8fafc', borderRadius: 12, padding: '14px', border: '1px solid #e2e8f0' },
  intrType:    { fontSize: 12, fontWeight: 800, background: '#eff6ff', color: '#1d4ed8', borderRadius: 20, padding: '3px 10px' },
  moveRow:     { display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', paddingTop: 8, borderTop: '1px solid #f1f5f9' },
  moveBtn:     { borderRadius: 20, padding: '5px 14px', fontSize: 12, fontWeight: 700, cursor: 'pointer' },
  fieldLabel:  { fontSize: 13, fontWeight: 700, color: '#374151', display: 'block', marginBottom: 6 },
  fieldInput:  { width: '100%', border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none', boxSizing: 'border-box', background: '#fafafa', fontFamily: 'inherit' },
  submitBtn:   { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '13px', fontSize: 15, fontWeight: 800, cursor: 'pointer' },
}
