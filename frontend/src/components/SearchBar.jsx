import { useState, useRef, useEffect, useCallback } from 'react'
import { useLang } from '../context/LangContext'
import { useToast } from '../context/ToastContext'
import { useBreakpoint } from '../hooks/useBreakpoint'

const CITIES   = ['Gurgaon', 'Noida', 'Delhi', 'Greater Noida', 'Faridabad', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']
const TYPES    = ['apartment', 'villa', 'house', 'plot', 'commercial', 'studio']
const BED_OPTS = ['1', '2', '3', '4', '5']

const SUGGESTIONS = [
  ...CITIES,
  ...TYPES,
  '2 BHK apartment Gurgaon',
  '3 BHK villa Noida',
  'studio flat Delhi',
  'commercial space Mumbai',
  'independent house Bangalore',
  'plot Hyderabad',
  'furnished flat Pune',
]

export default function SearchBar({ filters, onChange }) {
  const { tr } = useLang()
  const { toast } = useToast()
  const { isMobile } = useBreakpoint()

  const { search, listingType, propType, beds, minPrice, maxPrice, city } = filters

  const [inputVal,   setInputVal]   = useState(search || '')
  const [suggestions,setSuggestions]= useState([])
  const [showSug,    setShowSug]    = useState(false)
  const [listening,  setListening]  = useState(false)
  const [micSupport, setMicSupport] = useState(false)
  const [showFilters,setShowFilters]= useState(!isMobile)

  const inputRef    = useRef()
  const recognRef   = useRef()
  const suggestRef  = useRef()

  /* ── Voice search setup ─────────────────── */
  useEffect(() => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRec) {
      setMicSupport(true)
      const rec = new SpeechRec()
      rec.continuous    = false
      rec.interimResults= true
      rec.maxAlternatives = 1

      rec.onresult = (e) => {
        const transcript = Array.from(e.results)
          .map(r => r[0].transcript)
          .join('')
        setInputVal(transcript)
        if (e.results[e.results.length - 1].isFinal) {
          onChange({ search: transcript })
          setListening(false)
          toast(`🎤 "${transcript}"`, 'info')
        }
      }
      rec.onerror = () => {
        setListening(false)
        toast('Microphone error. Please allow access.', 'error')
      }
      rec.onend = () => setListening(false)
      recognRef.current = rec
    }
  }, [])

  /* ── Suggestion filtering ───────────────── */
  useEffect(() => {
    if (inputVal.trim().length < 2) { setSuggestions([]); return }
    const q = inputVal.toLowerCase()
    setSuggestions(SUGGESTIONS.filter(s => s.toLowerCase().includes(q)).slice(0, 6))
  }, [inputVal])

  /* ── Close suggestions on outside click ─── */
  useEffect(() => {
    const handler = (e) => {
      if (suggestRef.current && !suggestRef.current.contains(e.target) &&
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowSug(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const toggleMic = () => {
    if (!recognRef.current) return
    if (listening) {
      recognRef.current.stop()
      setListening(false)
    } else {
      try {
        recognRef.current.lang = navigator.language || 'en-IN'
        recognRef.current.start()
        setListening(true)
        toast('🎤 Listening... speak now', 'info')
      } catch {
        toast('Could not start microphone', 'error')
      }
    }
  }

  const applySearch = (val) => {
    setShowSug(false)
    onChange({ search: val ?? inputVal })
  }

  const clearAll = () => {
    setInputVal('')
    onChange({ search: '', listingType: 'all', propType: 'All', beds: 'Any', minPrice: '', maxPrice: '', city: 'All' })
  }

  /* Count active filters */
  const activeCount = [
    listingType !== 'all',
    propType !== 'All',
    beds !== 'Any',
    !!minPrice,
    !!maxPrice,
    city !== 'All',
  ].filter(Boolean).length

  return (
    <div style={s.wrap}>
      {/* ── Main search row ── */}
      <div style={s.row}>
        <span style={s.searchIcon}>🔍</span>

        <div style={{ position: 'relative', flex: 1 }} ref={suggestRef}>
          <input
            ref={inputRef}
            value={inputVal}
            onChange={e => { setInputVal(e.target.value); setShowSug(true) }}
            onFocus={() => inputVal.length >= 2 && setShowSug(true)}
            onKeyDown={e => e.key === 'Enter' && applySearch()}
            placeholder={tr('searchPlaceholder')}
            style={s.input}
          />

          {/* Suggestions dropdown */}
          {showSug && suggestions.length > 0 && (
            <div style={s.sugBox}>
              {suggestions.map(sug => (
                <button key={sug} style={s.sugItem}
                  onMouseDown={() => { setInputVal(sug); applySearch(sug) }}>
                  <span style={s.sugIcon}>📍</span> {sug}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Clear button */}
        {(inputVal || activeCount > 0) && (
          <button onClick={clearAll} style={s.clearBtn} title="Clear all">✕</button>
        )}

        {/* Mic button */}
        {micSupport && (
          <button
            onClick={toggleMic}
            style={{ ...s.micBtn, ...(listening ? s.micActive : {}) }}
            title={listening ? 'Stop listening' : 'Search by voice'}
          >
            {listening
              ? <span style={s.pulse}>🔴</span>
              : '🎤'}
          </button>
        )}

        {/* Search button */}
        <button onClick={() => applySearch()} style={s.searchBtn}>
          {isMobile ? '→' : tr('search')}
        </button>

        {/* Filter toggle (mobile) */}
        {isMobile && (
          <button onClick={() => setShowFilters(f => !f)} style={s.filterToggle}>
            ⚙️ {activeCount > 0 && <span style={s.badge}>{activeCount}</span>}
          </button>
        )}
      </div>

      {/* Active filter tags */}
      {activeCount > 0 && (
        <div style={s.tagRow}>
          {listingType !== 'all' && (
            <Tag label={listingType === 'sale' ? tr('buy') : tr('rent')}
              onRemove={() => onChange({ listingType: 'all' })} />
          )}
          {propType !== 'All' && (
            <Tag label={propType} onRemove={() => onChange({ propType: 'All' })} />
          )}
          {beds !== 'Any' && (
            <Tag label={`${beds} ${tr('bhk')}`} onRemove={() => onChange({ beds: 'Any' })} />
          )}
          {city !== 'All' && (
            <Tag label={`📍 ${city}`} onRemove={() => onChange({ city: 'All' })} />
          )}
          {minPrice && (
            <Tag label={`≥ ₹${Number(minPrice).toLocaleString('en-IN')}`}
              onRemove={() => onChange({ minPrice: '' })} />
          )}
          {maxPrice && (
            <Tag label={`≤ ₹${Number(maxPrice).toLocaleString('en-IN')}`}
              onRemove={() => onChange({ maxPrice: '' })} />
          )}
        </div>
      )}

      {/* ── Filter panel ── */}
      {showFilters && (
        <div style={s.filterPanel}>
          {/* Row 1 */}
          <div style={s.filterGrid}>
            <FilterGroup label={tr('buyRent')}>
              <select value={listingType} onChange={e => onChange({ listingType: e.target.value })} style={s.sel}>
                <option value="all">{tr('buyRent')}</option>
                <option value="sale">{tr('buy')}</option>
                <option value="rent">{tr('rent')}</option>
              </select>
            </FilterGroup>

            <FilterGroup label={tr('allTypes')}>
              <select value={propType} onChange={e => onChange({ propType: e.target.value })} style={s.sel}>
                <option value="All">{tr('allTypes')}</option>
                {TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </FilterGroup>

            <FilterGroup label={tr('anyBeds')}>
              <select value={beds} onChange={e => onChange({ beds: e.target.value })} style={s.sel}>
                <option value="Any">{tr('anyBeds')}</option>
                {BED_OPTS.map(b => <option key={b} value={b}>{b} {tr('bhk')}</option>)}
              </select>
            </FilterGroup>
          </div>

          {/* Row 2 */}
          <div style={s.filterGrid}>
            <FilterGroup label={tr('minPrice')}>
              <input type="number" placeholder="e.g. 5000000" value={minPrice}
                onChange={e => onChange({ minPrice: e.target.value })} style={s.sel} />
            </FilterGroup>

            <FilterGroup label={tr('maxPrice')}>
              <input type="number" placeholder="e.g. 20000000" value={maxPrice}
                onChange={e => onChange({ maxPrice: e.target.value })} style={s.sel} />
            </FilterGroup>

            <FilterGroup label="City">
              <select value={city} onChange={e => onChange({ city: e.target.value })} style={s.sel}>
                <option value="All">All Cities</option>
                {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </FilterGroup>
          </div>

          {/* Quick bedroom chips */}
          <div style={s.chipRow}>
            <span style={s.chipLabel}>Quick:</span>
            {BED_OPTS.map(b => (
              <button key={b} onClick={() => onChange({ beds: beds === b ? 'Any' : b })}
                style={{ ...s.chip, ...(beds === b ? s.chipActive : {}) }}>
                {b} {tr('bhk')}
              </button>
            ))}
            {['sale','rent'].map(lt => (
              <button key={lt} onClick={() => onChange({ listingType: listingType === lt ? 'all' : lt })}
                style={{ ...s.chip, ...(listingType === lt ? s.chipActive : {}) }}>
                {lt === 'sale' ? tr('buy') : tr('rent')}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Listening indicator */}
      {listening && (
        <div style={s.listeningBar}>
          <span style={s.wave}>〜〜〜</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#dc2626' }}>Listening... speak now</span>
          <span style={s.wave}>〜〜〜</span>
        </div>
      )}
    </div>
  )
}

function Tag({ label, onRemove }) {
  return (
    <span style={s.tag}>
      {label}
      <button onClick={onRemove} style={s.tagX}>✕</button>
    </span>
  )
}

function FilterGroup({ label, children }) {
  return (
    <div style={s.filterGroup}>
      <div style={s.filterLabel}>{label}</div>
      {children}
    </div>
  )
}

const s = {
  wrap:        { background: '#fff', borderRadius: 16, padding: '18px 20px', maxWidth: 900, margin: '0 auto 1.5rem', boxShadow: '0 8px 40px rgba(0,0,0,0.18)' },
  row:         { display: 'flex', alignItems: 'center', gap: 8 },
  searchIcon:  { fontSize: 18, flexShrink: 0 },
  input:       { flex: 1, border: 'none', outline: 'none', fontSize: 16, padding: '8px 4px', background: 'transparent', minWidth: 0 },
  sugBox:      { position: 'absolute', top: 'calc(100% + 6px)', left: 0, right: 0, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.12)', zIndex: 500, overflow: 'hidden' },
  sugItem:     { display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '10px 16px', border: 'none', background: 'none', cursor: 'pointer', fontSize: 14, color: '#0f172a', textAlign: 'left', borderBottom: '1px solid #f1f5f9' },
  sugIcon:     { fontSize: 13 },
  clearBtn:    { background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 16, padding: '4px 6px', borderRadius: 6, flexShrink: 0 },
  micBtn:      { background: '#f1f5f9', border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '8px 12px', cursor: 'pointer', fontSize: 18, transition: 'all 0.2s', flexShrink: 0 },
  micActive:   { background: '#fef2f2', border: '1.5px solid #fca5a5', boxShadow: '0 0 0 4px rgba(239,68,68,0.15)' },
  pulse:       { display: 'inline-block', animation: 'pulse 1s infinite' },
  searchBtn:   { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 10, padding: '9px 20px', fontWeight: 700, fontSize: 14, cursor: 'pointer', flexShrink: 0, boxShadow: '0 2px 8px rgba(26,86,219,0.3)' },
  filterToggle:{ background: '#f1f5f9', border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '8px 12px', cursor: 'pointer', fontSize: 16, position: 'relative', flexShrink: 0 },
  badge:       { position: 'absolute', top: -6, right: -6, background: '#dc2626', color: '#fff', borderRadius: '50%', width: 18, height: 18, fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  tagRow:      { display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 },
  tag:         { display: 'inline-flex', alignItems: 'center', gap: 6, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 20, padding: '4px 12px', fontSize: 13, fontWeight: 600 },
  tagX:        { background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', fontSize: 12, padding: 0, lineHeight: 1 },
  filterPanel: { borderTop: '1px solid #f1f5f9', marginTop: 14, paddingTop: 14, display: 'flex', flexDirection: 'column', gap: 12 },
  filterGrid:  { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px,1fr))', gap: 12 },
  filterGroup: { display: 'flex', flexDirection: 'column', gap: 5 },
  filterLabel: { fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' },
  sel:         { border: '1.5px solid #e2e8f0', borderRadius: 8, padding: '8px 10px', fontSize: 14, color: '#0f172a', background: '#f8fafc', outline: 'none', width: '100%', boxSizing: 'border-box' },
  chipRow:     { display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' },
  chipLabel:   { fontSize: 12, color: '#94a3b8', fontWeight: 600 },
  chip:        { background: '#f1f5f9', border: '1.5px solid #e2e8f0', color: '#475569', borderRadius: 20, padding: '5px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' },
  chipActive:  { background: '#eff6ff', border: '1.5px solid #1a56db', color: '#1a56db' },
  listeningBar:{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 10, padding: '8px', background: '#fef2f2', borderRadius: 8, border: '1px solid #fca5a5' },
  wave:        { color: '#dc2626', fontWeight: 700, animation: 'pulse 0.8s infinite' },
}
