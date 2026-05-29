import { useState } from 'react'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useToast } from '../context/ToastContext'

const TOOLS = [
  { id: 'desc',   icon: '✍️',  title: 'AI Description Generator',   sub: 'Auto-generate compelling property descriptions' },
  { id: '3d',     icon: '🏗',  title: 'AI 3D Model Generator',      sub: 'Visualize buildings with architecture styles' },
  { id: 'image',  icon: '🖼',  title: 'AI Image Generator',         sub: 'Generate property renders & visuals' },
  { id: 'price',  icon: '📈',  title: 'AI Price Predictor',         sub: 'Predict property prices with ML models' },
  { id: 'vastu',  icon: '🧿',  title: 'Vastu Compatibility',        sub: 'Check & fix Vastu for any room or property' },
  { id: 'seo',    icon: '🔍',  title: 'AI SEO Optimizer',           sub: 'Generate SEO titles, meta, keywords' },
  { id: 'chat',   icon: '🤖',  title: 'AI Property Chatbot',        sub: 'Answer buyer/renter queries 24×7' },
]

const ARCH_STYLES = ['Modern','Contemporary','Traditional','Minimalist','Luxury','Smart Home','Sustainable','Mediterranean','Art Deco','Classic']
const BUILDING_TYPES = ['Apartment','Villa','Penthouse','Commercial','Office','House','Retail','Mixed Use']
const PROP_TYPES = ['Apartment','Villa','Plot','Commercial','House','Studio']

const SAMPLE_DESCRIPTIONS = {
  apartment: `Welcome to this stunning 3BHK apartment nestled in the heart of Gurgaon's most sought-after corridor. Spread across 1,850 sq ft of intelligently designed space, this residence offers an unparalleled lifestyle upgrade. The living area opens into a spacious balcony with panoramic city views, while the modular kitchen features premium fittings and a breakfast bar perfect for morning rituals.\n\nAll three bedrooms are designed as private retreats — the master suite boasts an ensuite bath, walk-in wardrobe, and floor-to-ceiling windows that flood the room with natural light. The two additional bedrooms come with dedicated study nooks ideal for a hybrid work lifestyle.\n\nLocated within a RERA-certified township, residents enjoy 24×7 concierge, a fully-equipped gymnasium, resort-style swimming pool, children's play area, and lush landscaped gardens. Connectivity to NH-48 and the Delhi Metro's Yellow Line ensures seamless commutes.`,
  villa: `Experience absolute privacy and luxury in this magnificent 4BHK independent villa set across 4,200 sq ft in one of Bangalore's most exclusive enclaves. Designed by award-winning architects, the villa seamlessly blends modern aesthetics with functional elegance.\n\nThe ground floor features an expansive drawing room with 12-ft ceilings, a formal dining area seating 12, a fully-equipped chef's kitchen, and a private study. Step outside to your personal garden oasis complete with a temperature-controlled swimming pool and a covered alfresco dining terrace — perfect for entertaining.\n\nUpstairs, four generously sized bedrooms include a master suite with a boutique walk-in wardrobe, spa-inspired ensuite with a freestanding bathtub, and a private terrace. Smart home automation controls lighting, climate, security, and entertainment throughout.`,
}

const PRICE_FACTORS = [
  { label: 'Location Premium', val: '+12%', color: '#059669' },
  { label: 'Floor Level Bonus', val: '+4%', color: '#059669' },
  { label: 'Age Depreciation', val: '-2%', color: '#dc2626' },
  { label: 'Market Trend',     val: '+8%', color: '#059669' },
  { label: 'Amenity Score',    val: '+5%', color: '#059669' },
]

const SAMPLE_3D_RENDERS = [
  { style: 'Modern',       img: 'https://picsum.photos/seed/arch_modern/800/500',       time: '2.3s' },
  { style: 'Luxury',       img: 'https://picsum.photos/seed/arch_luxury/800/500',       time: '1.8s' },
  { style: 'Minimalist',   img: 'https://picsum.photos/seed/arch_mini/800/500',         time: '2.1s' },
  { style: 'Sustainable',  img: 'https://picsum.photos/seed/arch_eco/800/500',          time: '2.5s' },
]

export default function AITools() {
  const { isMobile } = useBreakpoint()
  const { toast }    = useToast()
  const [active, setActive]   = useState('desc')

  return (
    <div style={s.page}>
      <div style={s.banner}>
        <div style={s.bannerInner}>
          <div style={s.heroBadge}>✨ Powered by Google Gemini & Imagen</div>
          <h1 style={s.h1}>AI Tools for Real Estate</h1>
          <p style={s.sub}>Generate descriptions, 3D models, images, price predictions and more — instantly with AI</p>
        </div>
      </div>

      <div style={s.layout}>
        {/* Sidebar */}
        <div style={s.sidebar}>
          {TOOLS.map(t => (
            <button key={t.id} onClick={() => setActive(t.id)}
              style={{ ...s.sideBtn, ...(active === t.id ? s.sideBtnActive : {}) }}>
              <span style={{ fontSize: 22 }}>{t.icon}</span>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{t.title}</div>
                {!isMobile && <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>{t.sub}</div>}
              </div>
            </button>
          ))}
        </div>

        {/* Tool Panel */}
        <div style={s.panel}>
          {active === 'desc'  && <DescriptionTool  toast={toast} isMobile={isMobile} />}
          {active === '3d'    && <Model3DTool       toast={toast} isMobile={isMobile} />}
          {active === 'image' && <ImageGenTool      toast={toast} isMobile={isMobile} />}
          {active === 'price' && <PricePredictTool  toast={toast} isMobile={isMobile} />}
          {active === 'vastu' && <VastuTool          toast={toast} isMobile={isMobile} />}
          {active === 'seo'   && <SEOTool           toast={toast} isMobile={isMobile} />}
          {active === 'chat'  && <ChatbotTool       toast={toast} isMobile={isMobile} />}
        </div>
      </div>
    </div>
  )
}

/* ─── Description Generator ─── */
function DescriptionTool({ toast, isMobile }) {
  const [form, setForm] = useState({ type: 'apartment', bedrooms: '3', area: '1850', city: 'Gurgaon', price: '1.8 Cr', furnished: true, amenities: 'Pool,Gym,Parking' })
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    await new Promise(r => setTimeout(r, 1800))
    setResult(SAMPLE_DESCRIPTIONS[form.type] || SAMPLE_DESCRIPTIONS.apartment)
    setLoading(false)
    toast('✅ Description generated!', 'success')
  }

  return (
    <ToolCard title="✍️ AI Description Generator" sub="Generate compelling, SEO-optimised property descriptions instantly">
      <div style={g.twoCol(isMobile)}>
        <FormRow label="Property Type">
          <select value={form.type} onChange={e => setForm(p=>({...p,type:e.target.value}))} style={g.input}>
            {PROP_TYPES.map(t => <option key={t} value={t.toLowerCase()}>{t}</option>)}
          </select>
        </FormRow>
        <FormRow label="City">
          <input value={form.city} onChange={e => setForm(p=>({...p,city:e.target.value}))} style={g.input} placeholder="e.g. Gurgaon" />
        </FormRow>
        <FormRow label="Bedrooms">
          <input value={form.bedrooms} onChange={e => setForm(p=>({...p,bedrooms:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Area (sq ft)">
          <input value={form.area} onChange={e => setForm(p=>({...p,area:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Price">
          <input value={form.price} onChange={e => setForm(p=>({...p,price:e.target.value}))} style={g.input} placeholder="e.g. 1.8 Cr" />
        </FormRow>
        <FormRow label="Key Amenities">
          <input value={form.amenities} onChange={e => setForm(p=>({...p,amenities:e.target.value}))} style={g.input} placeholder="Pool, Gym, Parking..." />
        </FormRow>
      </div>
      <button onClick={generate} disabled={loading} style={g.genBtn}>
        {loading ? '⏳ Generating...' : '✨ Generate Description'}
      </button>
      {result && (
        <div style={g.resultBox} className="fade-in">
          <div style={g.resultHeader}>
            <span style={{ fontWeight: 800, color: '#0f172a' }}>Generated Description</span>
            <button onClick={() => { navigator.clipboard?.writeText(result); toast('Copied!','success') }} style={g.copyBtn}>📋 Copy</button>
          </div>
          <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.8, margin: 0, whiteSpace: 'pre-line' }}>{result}</p>
        </div>
      )}
    </ToolCard>
  )
}

/* ─── 3D Model Generator ─── */
function Model3DTool({ toast, isMobile }) {
  const [form, setForm] = useState({ type: 'Apartment', style: 'Modern', floors: '4', bedrooms: '3', area: '2000', vastu: true })
  const [renders, setRenders] = useState([])
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    await new Promise(r => setTimeout(r, 2400))
    setRenders(SAMPLE_3D_RENDERS)
    setLoading(false)
    toast('🏗 3D models generated!', 'success')
  }

  return (
    <ToolCard title="🏗 AI 3D Model Generator" sub="Powered by architecture_service.py · Gemini Imagen API">
      <div style={g.twoCol(isMobile)}>
        <FormRow label="Building Type">
          <select value={form.type} onChange={e => setForm(p=>({...p,type:e.target.value}))} style={g.input}>
            {BUILDING_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
        </FormRow>
        <FormRow label="Architecture Style">
          <select value={form.style} onChange={e => setForm(p=>({...p,style:e.target.value}))} style={g.input}>
            {ARCH_STYLES.map(s => <option key={s}>{s}</option>)}
          </select>
        </FormRow>
        <FormRow label="Floors">
          <input value={form.floors} onChange={e => setForm(p=>({...p,floors:e.target.value}))} style={g.input} type="number" min="1" max="50" />
        </FormRow>
        <FormRow label="Total Area (sq ft)">
          <input value={form.area} onChange={e => setForm(p=>({...p,area:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Bedrooms">
          <input value={form.bedrooms} onChange={e => setForm(p=>({...p,bedrooms:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Vastu Compliant">
          <label style={{ display:'flex', alignItems:'center', gap: 8, fontSize: 14, cursor: 'pointer', paddingTop: 10 }}>
            <input type="checkbox" checked={form.vastu} onChange={e => setForm(p=>({...p,vastu:e.target.checked}))} style={{ width:18,height:18 }} />
            Yes, apply Vastu principles
          </label>
        </FormRow>
      </div>
      <button onClick={generate} disabled={loading} style={g.genBtn}>
        {loading ? '⏳ Generating 3D Models...' : '🏗 Generate 3D Visualizations'}
      </button>
      {loading && (
        <div style={g.loadBox}>
          <div style={g.loadBar}><div style={g.loadFill} /></div>
          <div style={{ fontSize: 13, color: '#64748b', marginTop: 10 }}>AI is rendering architectural models in {form.style} style…</div>
        </div>
      )}
      {renders.length > 0 && !loading && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)', gap: 16 }} className="fade-in">
          {renders.map(r => (
            <div key={r.style} style={g.renderCard}>
              <img src={r.img} alt={r.style} style={g.renderImg}
                onError={e => { e.target.src = `https://picsum.photos/seed/arch${r.style}/800/500` }} />
              <div style={g.renderFooter}>
                <span style={{ fontWeight: 800, fontSize: 13 }}>{r.style} Style</span>
                <span style={g.renderTime}>⚡ {r.time}</span>
                <button onClick={() => toast(`Downloading ${r.style} model...`,'info')} style={g.dlBtn}>⬇ Download</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </ToolCard>
  )
}

/* ─── Image Generator ─── */
function ImageGenTool({ toast, isMobile }) {
  const [prompt, setPrompt]   = useState('')
  const [style,  setStyle]    = useState('Photorealistic')
  const [images, setImages]   = useState([])
  const [loading, setLoading] = useState(false)
  const PRESETS = ['Luxury apartment exterior at golden hour', 'Modern kitchen with marble countertops', 'Swimming pool with city view at night', 'Cozy 3BHK living room with natural light']

  const generate = async () => {
    if (!prompt) { toast('Enter a prompt first', 'error'); return }
    setLoading(true)
    await new Promise(r => setTimeout(r, 2000))
    setImages([
      `https://picsum.photos/seed/${encodeURIComponent(prompt)}1/800/600`,
      `https://picsum.photos/seed/${encodeURIComponent(prompt)}2/800/600`,
      `https://picsum.photos/seed/${encodeURIComponent(prompt)}3/800/600`,
      `https://picsum.photos/seed/${encodeURIComponent(prompt)}4/800/600`,
    ])
    setLoading(false)
    toast('🖼 Images generated!', 'success')
  }

  return (
    <ToolCard title="🖼 AI Image Generator" sub="Powered by Google Imagen 3.0 · 1024×1024 HD renders">
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {PRESETS.map(p => (
          <button key={p} onClick={() => setPrompt(p)} style={g.presetBtn}>{p}</button>
        ))}
      </div>
      <FormRow label="Image Prompt">
        <textarea value={prompt} onChange={e => setPrompt(e.target.value)} rows={3}
          placeholder="Describe the image you want to generate... e.g. 'Luxury penthouse rooftop pool with Mumbai skyline at sunset'" style={{ ...g.input, resize:'vertical' }} />
      </FormRow>
      <FormRow label="Art Style">
        <select value={style} onChange={e => setStyle(e.target.value)} style={g.input}>
          {['Photorealistic','Architectural Render','Watercolor','Sketch','3D Render','Cinematic'].map(s => <option key={s}>{s}</option>)}
        </select>
      </FormRow>
      <button onClick={generate} disabled={loading} style={g.genBtn}>
        {loading ? '⏳ Generating Images...' : '🖼 Generate 4 Images'}
      </button>
      {images.length > 0 && !loading && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(2,1fr)', gap: 12 }} className="fade-in">
          {images.map((img, i) => (
            <div key={i} style={g.imgCard}>
              <img src={img} alt={`gen-${i}`} style={g.genImg} />
              <div style={g.imgFooter}>
                <span style={{ fontSize: 12, color: '#64748b' }}>Variation {i+1}</span>
                <button onClick={() => toast('Downloading...','info')} style={g.dlBtn}>⬇</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </ToolCard>
  )
}

/* ─── Price Predictor ─── */
function PricePredictTool({ toast, isMobile }) {
  const [form, setForm] = useState({ city: 'Gurgaon', area: '1500', bedrooms: '3', age: '2', floor: '8', type: 'Apartment' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const predict = async () => {
    setLoading(true)
    await new Promise(r => setTimeout(r, 1500))
    const base    = Number(form.area) * { Gurgaon: 12500, Noida: 8400, Mumbai: 28600, Bangalore: 9800 }[form.city] || 10000
    const predicted = Math.round(base * 1.127 / 100000) * 100000
    setResult({ predicted, low: predicted * 0.92, high: predicted * 1.08, confidence: 87 })
    setLoading(false)
    toast('📈 Price prediction ready!', 'success')
  }

  return (
    <ToolCard title="📈 AI Price Predictor" sub="ML-powered valuation using 50+ market signals · prediction.py">
      <div style={g.twoCol(isMobile)}>
        <FormRow label="City">
          <select value={form.city} onChange={e => setForm(p=>({...p,city:e.target.value}))} style={g.input}>
            {['Gurgaon','Noida','Mumbai','Bangalore','Hyderabad','Pune','Chennai'].map(c => <option key={c}>{c}</option>)}
          </select>
        </FormRow>
        <FormRow label="Property Type">
          <select value={form.type} onChange={e => setForm(p=>({...p,type:e.target.value}))} style={g.input}>
            {PROP_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
        </FormRow>
        <FormRow label="Area (sq ft)">
          <input value={form.area} onChange={e => setForm(p=>({...p,area:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Bedrooms">
          <input value={form.bedrooms} onChange={e => setForm(p=>({...p,bedrooms:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Building Age (years)">
          <input value={form.age} onChange={e => setForm(p=>({...p,age:e.target.value}))} style={g.input} type="number" />
        </FormRow>
        <FormRow label="Floor Number">
          <input value={form.floor} onChange={e => setForm(p=>({...p,floor:e.target.value}))} style={g.input} type="number" />
        </FormRow>
      </div>
      <button onClick={predict} disabled={loading} style={g.genBtn}>
        {loading ? '⏳ Predicting...' : '📈 Predict Price'}
      </button>
      {result && !loading && (
        <div style={g.resultBox} className="fade-in">
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600, marginBottom: 6 }}>Predicted Market Value</div>
            <div style={{ fontSize: 36, fontWeight: 900, color: '#1a56db', letterSpacing: '-1px' }}>
              ₹{result.predicted >= 10000000 ? `${(result.predicted/10000000).toFixed(2)} Cr` : `${(result.predicted/100000).toFixed(1)} L`}
            </div>
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
              Range: ₹{(result.low/100000).toFixed(0)}L – ₹{(result.high/100000).toFixed(0)}L
            </div>
            <div style={{ display:'inline-block', background:'#d1fae5', color:'#065f46', borderRadius:20, padding:'4px 14px', fontSize:13, fontWeight:800, marginTop:10 }}>
              {result.confidence}% Confidence
            </div>
          </div>
          <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#64748b', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>Price Factors</div>
            {PRICE_FACTORS.map(f => (
              <div key={f.label} style={{ display:'flex', justifyContent:'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, color: '#374151' }}>{f.label}</span>
                <span style={{ fontSize: 13, fontWeight: 800, color: f.color }}>{f.val}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </ToolCard>
  )
}

/* ─── SEO Tool ─── */
function SEOTool({ toast, isMobile }) {
  const [form, setForm] = useState({ title: '', city: 'Gurgaon', type: 'Apartment', keywords: '' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    await new Promise(r => setTimeout(r, 1200))
    const t = form.title || `3BHK ${form.type} in ${form.city}`
    setResult({
      metaTitle: `${t} | Buy/Rent in ${form.city} 2025 | PropertyYards`,
      metaDesc: `Explore this premium ${t.toLowerCase()} on PropertyYards. RERA verified, best price, easy EMI. ${form.city}'s top locality. Book a free site visit today!`,
      keywords: [`${form.type.toLowerCase()} in ${form.city}`, `buy ${form.type.toLowerCase()} ${form.city}`, `${form.city} real estate 2025`, `${form.type.toLowerCase()} for sale`, `RERA verified ${form.city}`],
      h1: `Premium ${t} — Best Price in ${form.city}`,
      slug: t.toLowerCase().replace(/\s+/g,'-').replace(/[^a-z0-9-]/g,''),
    })
    setLoading(false)
    toast('🔍 SEO content generated!', 'success')
  }

  return (
    <ToolCard title="🔍 AI SEO Optimizer" sub="Generate meta tags, keywords, and slugs — ai_seo_optimizer.py">
      <div style={g.twoCol(isMobile)}>
        <FormRow label="Property Title">
          <input value={form.title} onChange={e => setForm(p=>({...p,title:e.target.value}))} style={g.input} placeholder="e.g. 3BHK Apartment in Sector 45" />
        </FormRow>
        <FormRow label="City">
          <input value={form.city} onChange={e => setForm(p=>({...p,city:e.target.value}))} style={g.input} />
        </FormRow>
        <FormRow label="Property Type">
          <select value={form.type} onChange={e => setForm(p=>({...p,type:e.target.value}))} style={g.input}>
            {PROP_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
        </FormRow>
      </div>
      <button onClick={generate} disabled={loading} style={g.genBtn}>
        {loading ? '⏳ Optimizing...' : '🔍 Generate SEO Package'}
      </button>
      {result && !loading && (
        <div style={g.resultBox} className="fade-in">
          {[['Meta Title', result.metaTitle],['Meta Description', result.metaDesc],['H1 Tag', result.h1],['URL Slug', `/${result.slug}`]].map(([label, val]) => (
            <div key={label} style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>{label}</div>
              <div style={{ fontSize: 14, color: '#0f172a', background: '#f8fafc', borderRadius: 8, padding: '10px 14px', fontFamily: label === 'URL Slug' ? 'monospace' : 'inherit' }}>{val}</div>
            </div>
          ))}
          <div>
            <div style={{ fontSize: 11, fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Target Keywords</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {result.keywords.map(k => <span key={k} style={g.kwChip}>{k}</span>)}
            </div>
          </div>
        </div>
      )}
    </ToolCard>
  )
}

/* ─── Chatbot Tool ─── */
function ChatbotTool({ toast }) {
  const [messages, setMessages] = useState([
    { role: 'bot', text: '👋 Hi! I\'m PropertyYards AI. Ask me anything about properties, loans, localities, or the buying/renting process.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const RESPONSES = {
    loan: 'For a ₹1 Cr property, most banks offer 80% LTV. At 8.5% interest over 20 years, your EMI would be ~₹69,000/month. SBI, HDFC and ICICI currently offer the best rates. Want me to compare loans?',
    rera: 'All developers on PropertyYards are RERA-registered. You can verify a project by visiting your state RERA portal and entering the project RERA number. Always check before booking!',
    gurgaon: 'Gurgaon (Gurugram) is India\'s top corporate hub. Sectors 45-60 are premium residential. Current avg price: ₹12,500/sq ft. Annual appreciation: +14.2%. Best for IT professionals and investors.',
    default: 'That\'s a great question! Based on current market data, I can tell you that PropertyYards has 15,000+ verified listings across 10 cities, with RERA-certified brokers. Can you be more specific about what you\'re looking for?',
  }

  const send = async () => {
    if (!input.trim()) return
    const userMsg = input
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setInput('')
    setLoading(true)
    await new Promise(r => setTimeout(r, 900))
    const lower = userMsg.toLowerCase()
    const reply = lower.includes('loan') || lower.includes('emi') ? RESPONSES.loan
      : lower.includes('rera') ? RESPONSES.rera
      : lower.includes('gurgaon') || lower.includes('gurugram') ? RESPONSES.gurgaon
      : RESPONSES.default
    setMessages(prev => [...prev, { role: 'bot', text: reply }])
    setLoading(false)
  }

  return (
    <ToolCard title="🤖 AI Property Chatbot" sub="24×7 buyer/renter assistant — chatbot.py backend">
      <div style={g.chatBox}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ ...g.bubble, ...(m.role === 'user' ? g.bubbleUser : g.bubbleBot) }}>{m.text}</div>
          </div>
        ))}
        {loading && (
          <div style={{ display:'flex' }}>
            <div style={g.bubbleBot}>🤖 Thinking<span style={g.dots}>...</span></div>
          </div>
        )}
      </div>
      <div style={g.chatInput}>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==='Enter' && send()}
          placeholder="Ask about properties, loans, RERA, localities..." style={g.chatField} />
        <button onClick={send} disabled={loading || !input.trim()} style={g.sendBtn}>Send →</button>
      </div>
    </ToolCard>
  )
}

/* ─── Vastu Compatibility Tool ─── */
const VASTU_ROOMS = [
  { id: 'main_door',    label: 'Main Door',       icon: '🚪' },
  { id: 'living',      label: 'Living Room',     icon: '🛋' },
  { id: 'master_bed',  label: 'Master Bedroom',  icon: '🛏' },
  { id: 'kitchen',     label: 'Kitchen',         icon: '🍳' },
  { id: 'bathroom',    label: 'Bathroom',        icon: '🚿' },
  { id: 'pooja',       label: 'Pooja Room',      icon: '🪔' },
  { id: 'study',       label: 'Study / Office',  icon: '📚' },
  { id: 'staircase',   label: 'Staircase',       icon: '🪜' },
]

const DIRECTIONS = ['North','North-East (Ishan)','East','South-East (Agni)','South','South-West (Nairutya)','West','North-West (Vayu)']
const SHORT_DIR   = { 'North':'N','North-East (Ishan)':'NE','East':'E','South-East (Agni)':'SE','South':'S','South-West (Nairutya)':'SW','West':'W','North-West (Vayu)':'NW' }

const VASTU_RULES = {
  main_door:   {
    ideal:   ['North','North-East (Ishan)','East'],
    avoid:   ['South','South-West (Nairutya)'],
    tips: {
      'North':              { score:95, verdict:'Excellent', color:'#059669', fix: null,          reason: 'North-facing entrance attracts prosperity and career growth. Ruled by Kuber (god of wealth).' },
      'North-East (Ishan)': { score:98, verdict:'Best',      color:'#059669', fix: null,          reason: 'Most auspicious direction. Brings health, wealth and positive energy into the home.' },
      'East':               { score:90, verdict:'Very Good', color:'#059669', fix: null,          reason: 'East brings morning sunlight and positive solar energy. Good for overall wellbeing.' },
      'South-East (Agni)':  { score:65, verdict:'Average',   color:'#f59e0b', fix: 'Place a Swastik symbol on the door. Use a green plant on left side of entrance.', reason: 'South-East is the Agni corner. Can cause financial instability.' },
      'South':              { score:30, verdict:'Avoid',     color:'#dc2626', fix: 'Place a Vastu pyramid on the door threshold. Hang a brass Ganesha inside. Use a red bulb above the entrance.', reason: 'South-facing entrance is considered inauspicious — associated with Yama (god of death). Can bring health issues.' },
      'South-West (Nairutya)':{ score:20, verdict:'Bad',    color:'#dc2626', fix: 'Install a lead metal strip at entrance. Place 7 horses painting on south wall. Use heavy furniture near south wall.', reason: 'Most inauspicious direction for entrance. Associated with negative energy, debt and health issues.' },
      'West':               { score:70, verdict:'Good',     color:'#059669', fix: null,          reason: 'West entrance is acceptable. Place a Vastu fish painting inside for added positivity.' },
      'North-West (Vayu)':  { score:75, verdict:'Good',     color:'#059669', fix: 'Place wind chimes near entrance for better air circulation energy.', reason: 'North-West is the Vayu (air) corner. Good for social connections and relationships.' },
    }
  },
  living: {
    ideal:   ['North','North-East (Ishan)','East'],
    avoid:   ['South-West (Nairutya)'],
    tips: {
      'North':              { score:92, verdict:'Excellent', color:'#059669', fix: null,       reason: 'North living room promotes prosperity and family harmony.' },
      'North-East (Ishan)': { score:95, verdict:'Best',     color:'#059669', fix: null,       reason: 'Most ideal for living — brings light, positivity and social well-being.' },
      'East':               { score:88, verdict:'Very Good',color:'#059669', fix: null,       reason: 'East-facing living room fills with morning light — energising and positive.' },
      'South-East (Agni)':  { score:60, verdict:'Average', color:'#f59e0b', fix: 'Place sofa on south or west wall. Use blue or green décor. Avoid red color scheme.', reason: 'Fire energy may cause arguments. Neutral tones help.' },
      'South':              { score:55, verdict:'Average', color:'#f59e0b', fix: 'Place a Vastu yantra on south wall. Use heavy sofa on south side. Avoid yellow walls.', reason: 'South living room is acceptable with corrections.' },
      'South-West (Nairutya)':{ score:40, verdict:'Poor', color:'#dc2626', fix: 'Use heavy furniture on SW corner. Paint walls in earthy tones. Place a clay pot with soil.', reason: 'SW is not ideal for living — causes instability and conflicts.' },
      'West':               { score:75, verdict:'Good',   color:'#059669', fix: null,       reason: 'West living room is acceptable — good for entertainment and social life.' },
      'North-West (Vayu)':  { score:70, verdict:'Good',   color:'#059669', fix: 'Keep NW corner clutter-free. Place moving objects like a clock.',  reason: 'NW living room is good but can cause restlessness for some family members.' },
    }
  },
  master_bed: {
    ideal:   ['South-West (Nairutya)','South','West'],
    avoid:   ['North-East (Ishan)','South-East (Agni)'],
    tips: {
      'South-West (Nairutya)':{ score:98, verdict:'Best',     color:'#059669', fix: null,       reason: 'SW is the most powerful zone — ideal for the master bedroom. Promotes stability, health and authority for head of family.' },
      'South':              { score:88, verdict:'Very Good', color:'#059669', fix: null,       reason: 'South bedroom provides sound sleep and stability.' },
      'West':               { score:82, verdict:'Very Good', color:'#059669', fix: null,       reason: 'West bedroom is good for career-oriented individuals.' },
      'North-West (Vayu)':  { score:65, verdict:'Average',  color:'#f59e0b', fix: 'Use heavy curtains to reduce air movement energy. Place rose quartz crystal near bed.', reason: 'NW bedroom can cause frequent travel or marital instability.' },
      'North':              { score:60, verdict:'Average',  color:'#f59e0b', fix: 'Avoid sleeping with head towards North. Sleep with head South or East.', reason: 'North is acceptable but not ideal — can cause health issues if head points North while sleeping.' },
      'East':               { score:70, verdict:'Good',     color:'#059669', fix: 'Place bed on south or west wall. Avoid head facing East.', reason: 'East bedroom is acceptable for younger family members.' },
      'North-East (Ishan)': { score:25, verdict:'Avoid',   color:'#dc2626', fix: 'Convert to pooja room if possible. If unavoidable: paint walls white/cream, no dark furniture, keep extremely clean.', reason: 'NE is a sacred zone — using as bedroom causes health issues and mental stress.' },
      'South-East (Agni)':  { score:35, verdict:'Poor',    color:'#dc2626', fix: 'Paint room in cool blue/green. Place Vastu pyramid. Avoid red/orange décor. Keep fire appliances out.', reason: 'SE (Agni zone) as bedroom can cause quarrels and health problems.' },
    }
  },
  kitchen: {
    ideal:   ['South-East (Agni)'],
    avoid:   ['North-East (Ishan)','South-West (Nairutya)'],
    tips: {
      'South-East (Agni)':  { score:100, verdict:'Perfect', color:'#059669', fix: null,       reason: 'SE is the Agni (fire) zone — absolutely ideal for kitchen. Promotes good health and positive cooking energy.' },
      'North-West (Vayu)':  { score:75,  verdict:'Good',    color:'#059669', fix: 'Keep stove on SE side of the kitchen. Face East while cooking.', reason: 'NW kitchen is acceptable as a secondary option.' },
      'North':              { score:55,  verdict:'Average', color:'#f59e0b', fix: 'Place a copper plate on east wall. Cook facing East. Keep a Tulsi plant outside kitchen.', reason: 'North kitchen conflicts with water energy — needs remedies.' },
      'East':               { score:70,  verdict:'Good',   color:'#059669', fix: 'Good if stove is on SE side of the kitchen.',  reason: 'East kitchen is acceptable. Morning sunlight purifies cooking area.' },
      'South':              { score:60,  verdict:'Average',color:'#f59e0b', fix: 'Ensure proper ventilation. Place blue tiles on north wall of kitchen.',  reason: 'South kitchen can cause excess heat and temperamental issues.' },
      'South-West (Nairutya)':{ score:20, verdict:'Bad',  color:'#dc2626', fix: 'Place a Vastu copper pyramid in SW corner. Paint walls yellow or orange. Move stove to SE corner.', reason: 'SW kitchen is highly inauspicious — causes financial drain and health problems.' },
      'West':               { score:65,  verdict:'Average',color:'#f59e0b', fix: 'Face East while cooking. Use yellow or orange walls.', reason: 'West kitchen is manageable with proper remedies.' },
      'North-East (Ishan)': { score:15,  verdict:'Worst', color:'#dc2626', fix: 'This is the most problematic kitchen placement. Move kitchen if possible. If not: place a copper pyramid, paint walls white, never use red. Pooja room ideal here instead.', reason: 'NE is the sacred Ishan zone — kitchen here causes severe health, financial and relationship problems.' },
    }
  },
  bathroom: {
    ideal:   ['North-West (Vayu)','West'],
    avoid:   ['North-East (Ishan)','South-West (Nairutya)'],
    tips: {
      'North-West (Vayu)':  { score:95, verdict:'Best',     color:'#059669', fix: null,       reason: 'NW is the best zone for bathrooms — removes negative energy effectively.' },
      'West':               { score:85, verdict:'Very Good',color:'#059669', fix: null,       reason: 'West bathroom is highly acceptable per Vastu.' },
      'South':              { score:70, verdict:'Good',     color:'#059669', fix: 'Keep bathroom door closed always.',  reason: 'South bathroom is acceptable. Ensure good drainage.' },
      'East':               { score:65, verdict:'Average',  color:'#f59e0b', fix: 'Use white tiles. Keep a sea salt bowl inside. Ensure proper ventilation.', reason: 'East is generally positive — bathroom here slightly reduces its energy.' },
      'North':              { score:55, verdict:'Average',  color:'#f59e0b', fix: 'Always keep the bathroom door shut. Place a Vastu crystal near drain.',  reason: 'North bathroom can drain wealth energy — remedies needed.' },
      'South-East (Agni)':  { score:50, verdict:'Average', color:'#f59e0b', fix: 'Place a blue light inside. Ensure drainage goes west or north.', reason: 'SE (fire zone) conflicts with water — can cause health issues.' },
      'South-West (Nairutya)':{ score:25, verdict:'Poor',  color:'#dc2626', fix: 'Place a heavy stone or lead plate on floor. Use only white/cream tiles. Keep extremely dry.', reason: 'SW bathroom causes health deterioration and relationship problems.' },
      'North-East (Ishan)': { score:10, verdict:'Worst',   color:'#dc2626', fix: 'Critical issue. Use rock salt regularly. Place a Vastu yantra on door. Seal any leaky taps immediately. Consider conversion to pooja room.', reason: 'Absolute worst placement — causes severe loss of wealth and health for all occupants.' },
    }
  },
  pooja: {
    ideal:   ['North-East (Ishan)','East','North'],
    avoid:   ['South','South-West (Nairutya)'],
    tips: {
      'North-East (Ishan)': { score:100, verdict:'Perfect', color:'#059669', fix: null,       reason: 'NE is the most sacred zone — perfect for pooja room. Divine energy concentrates here.' },
      'North':              { score:90,  verdict:'Excellent',color:'#059669',fix: null,        reason: 'North pooja room channels wealth energy with divine blessings.' },
      'East':               { score:88,  verdict:'Very Good',color:'#059669',fix: null,        reason: 'East pooja room receives auspicious morning light during prayers.' },
      'West':               { score:65,  verdict:'Average', color:'#f59e0b', fix: 'Ensure devotees face East during prayer. Keep room very clean.', reason: 'West is average for pooja — face East while praying.' },
      'North-West (Vayu)':  { score:55,  verdict:'Average', color:'#f59e0b', fix: 'Face East while praying. Use yellow/gold décor.',  reason: 'NW is acceptable with corrections.' },
      'South-East (Agni)':  { score:60,  verdict:'Average', color:'#f59e0b', fix: 'Avoid placing pooja in Agni corner. If unavoidable, use copper idols.', reason: 'SE is manageable — fire energy can be used for diyas and lamps.' },
      'South':              { score:30,  verdict:'Avoid',   color:'#dc2626', fix: 'Place a Vastu yantra. Always keep incense lit. Use copper accessories.', reason: 'South pooja room reduces the positive impact of prayers.' },
      'South-West (Nairutya)':{ score:15, verdict:'Worst', color:'#dc2626', fix: 'Relocate pooja room immediately. Place a copper pyramid in SW. Use this area for storage instead.', reason: 'SW pooja room is considered very inauspicious in Vastu.' },
    }
  },
  study: {
    ideal:   ['North','North-East (Ishan)','East','West'],
    avoid:   ['South-West (Nairutya)'],
    tips: {
      'North':              { score:95, verdict:'Best',      color:'#059669', fix: null,       reason: 'North study room — ruled by Mercury (Budh) — ideal for concentration, learning and career growth.' },
      'North-East (Ishan)': { score:92, verdict:'Excellent', color:'#059669', fix: null,       reason: 'NE brings divine knowledge energy — excellent for students and professionals.' },
      'East':               { score:85, verdict:'Very Good', color:'#059669', fix: null,       reason: 'East-facing study with morning sun boosts alertness and memory.' },
      'West':               { score:80, verdict:'Good',      color:'#059669', fix: 'Face North or East while studying.',  reason: 'West study is good for creative professionals.' },
      'South':              { score:60, verdict:'Average',   color:'#f59e0b', fix: 'Face North while studying. Place a green plant on desk. Use blue chair.', reason: 'South study can cause distraction — use remedies.' },
      'South-East (Agni)':  { score:55, verdict:'Average',  color:'#f59e0b', fix: 'Avoid studying facing South. Place a study lamp on left side of desk.', reason: 'SE study can cause mental fatigue — proper lighting helps.' },
      'South-West (Nairutya)':{ score:35, verdict:'Poor',   color:'#dc2626', fix: 'Face North or East. Keep north wall clean. Place a Saraswati idol on study table.', reason: 'SW is unstable energy — causes poor concentration and indecision.' },
      'North-West (Vayu)':  { score:65, verdict:'Average',  color:'#f59e0b', fix: 'Close windows while studying. Use heavy bookshelf on NW wall.',  reason: 'NW study can cause mental distraction — remedies help.' },
    }
  },
  staircase: {
    ideal:   ['South','South-West (Nairutya)','West'],
    avoid:   ['North-East (Ishan)','North'],
    tips: {
      'South':              { score:90, verdict:'Excellent', color:'#059669', fix: null,       reason: 'South staircase is ideal — does not block positive energy flow.' },
      'South-West (Nairutya)':{ score:88, verdict:'Very Good',color:'#059669',fix: null,       reason: 'SW staircase anchors the heavy structure perfectly in the earth zone.' },
      'West':               { score:82, verdict:'Very Good', color:'#059669', fix: null,       reason: 'West staircase is highly acceptable per Vastu.' },
      'South-East (Agni)':  { score:70, verdict:'Good',     color:'#059669', fix: 'Ensure staircase rises clockwise.',  reason: 'SE staircase is acceptable with clockwise direction.' },
      'North-West (Vayu)':  { score:60, verdict:'Average',  color:'#f59e0b', fix: 'Paint walls in warm tones. Place a potted plant at base.', reason: 'NW staircase can cause restlessness — use remedies.' },
      'East':               { score:50, verdict:'Average',  color:'#f59e0b', fix: 'Add a Vastu pyramid at the base. Use wooden steps.', reason: 'East staircase partially blocks positive morning energy.' },
      'North':              { score:25, verdict:'Poor',     color:'#dc2626', fix: 'Place copper Vastu pyramid under first step. Hang a Vastu energy plate on north wall. Use very bright lighting.', reason: 'North staircase blocks wealth energy flow — associated with financial decline.' },
      'North-East (Ishan)': { score:10, verdict:'Worst',   color:'#dc2626', fix: 'Critical Vastu defect. Install a large Vastu pyramid. Hang a Vastu strip on each step. Remove any storage under stairs immediately.', reason: 'NE staircase is the worst placement — cuts into the divine sacred zone. Causes major health, wealth and relationship problems.' },
    }
  },
}

const OVERALL_SCORE_LABEL = (s) => s >= 85 ? { label:'Vastu Compliant ✅',     color:'#059669', bg:'#d1fae5' }
  : s >= 65 ? { label:'Mostly Compliant 🟡',  color:'#d97706', bg:'#fef3c7' }
  : s >= 45 ? { label:'Needs Correction ⚠️',  color:'#f59e0b', bg:'#fffbeb' }
  :           { label:'Major Defects ❌',       color:'#dc2626', bg:'#fee2e2' }

function VastuTool({ toast, isMobile }) {
  const [facing, setFacing]   = useState('North')
  const [propType, setPropType] = useState('Apartment')
  const [selected, setSelected] = useState({})
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeRoom, setActiveRoom] = useState(null)

  const toggleRoom = (id, dir) =>
    setSelected(prev => ({ ...prev, [id]: dir }))

  const analyze = async () => {
    if (Object.keys(selected).length < 3) {
      toast('Select direction for at least 3 rooms', 'error')
      return
    }
    setLoading(true)
    await new Promise(r => setTimeout(r, 1600))
    const scores = Object.entries(selected).map(([roomId, dir]) => {
      const rule = VASTU_RULES[roomId]
      const tip  = rule?.tips?.[dir]
      return { roomId, dir, score: tip?.score ?? 70, verdict: tip?.verdict ?? 'Average', color: tip?.color ?? '#f59e0b', fix: tip?.fix ?? null, reason: tip?.reason ?? '' }
    })
    const overall = Math.round(scores.reduce((a, b) => a + b.score, 0) / scores.length)
    setResult({ scores, overall })
    setLoading(false)
    setActiveRoom(scores[0]?.roomId)
    toast('Vastu analysis complete!', 'success')
  }

  const compassArcs = [
    { dir: 'N',  angle: 0   }, { dir: 'NE', angle: 45  }, { dir: 'E',  angle: 90  }, { dir: 'SE', angle: 135 },
    { dir: 'S',  angle: 180 }, { dir: 'SW', angle: 225 }, { dir: 'W',  angle: 270 }, { dir: 'NW', angle: 315 },
  ]

  const facingAngle = (compassArcs.find(c => c.dir === SHORT_DIR[facing])?.angle ?? 0)
  const cx = 100, cy = 100, r = 80
  const toXY = (angle, radius) => ({
    x: cx + radius * Math.sin((angle * Math.PI) / 180),
    y: cy - radius * Math.cos((angle * Math.PI) / 180),
  })

  return (
    <ToolCard title="🧿 Vastu Compatibility" sub="Analyse any room or property against ancient Vastu Shastra principles">

      {/* Property Facing */}
      <div style={{ background: 'linear-gradient(135deg,#fefce8,#fff7ed)', borderRadius: 14, padding: '16px', border: '1px solid #fcd34d' }}>
        <div style={{ fontWeight: 800, fontSize: 14, color: '#92400e', marginBottom: 12 }}>🏠 Property Facing Direction</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {DIRECTIONS.map(d => (
            <button key={d} onClick={() => setFacing(d)}
              style={{ ...g.presetBtn, ...(facing === d ? { background: '#fef9c3', border: '1.5px solid #f59e0b', color: '#78350f', fontWeight: 800 } : {}) }}>
              {SHORT_DIR[d]} {d.includes('(') ? d.split('(')[0].trim() : d}
            </button>
          ))}
        </div>
      </div>

      {/* Compass + Room Grid side by side */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '200px 1fr', gap: 20, alignItems: 'start' }}>

        {/* Compass Rose SVG */}
        <div style={{ background: '#fff', borderRadius: 16, padding: '16px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#64748b', marginBottom: 8 }}>Compass Rose</div>
          <svg viewBox="0 0 200 200" style={{ width: '100%', maxWidth: 160, display: 'block', margin: '0 auto' }}>
            <circle cx={cx} cy={cy} r={r} fill="#f8fafc" stroke="#e2e8f0" strokeWidth="2" />
            <circle cx={cx} cy={cy} r={r * 0.55} fill="#fff" stroke="#e2e8f0" strokeWidth="1" />
            {compassArcs.map(({ dir, angle }) => {
              const outer = toXY(angle, r - 4)
              const inner = toXY(angle, r * 0.6)
              const label = toXY(angle, r + 14)
              const isFacing = SHORT_DIR[facing] === dir
              return (
                <g key={dir}>
                  <line x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y}
                    stroke={isFacing ? '#f59e0b' : '#e2e8f0'} strokeWidth={isFacing ? 3 : 1.5} />
                  <text x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle"
                    fontSize={isFacing ? 11 : 9} fontWeight={isFacing ? 900 : 600}
                    fill={isFacing ? '#b45309' : '#94a3b8'}>{dir}</text>
                </g>
              )
            })}
            {/* Arrow */}
            {(() => {
              const tip  = toXY(facingAngle, r * 0.52)
              const left = toXY(facingAngle + 160, r * 0.2)
              const right= toXY(facingAngle - 160, r * 0.2)
              return <polygon points={`${tip.x},${tip.y} ${left.x},${left.y} ${right.x},${right.y}`} fill="#f59e0b" />
            })()}
            <text x={cx} y={cy + 4} textAnchor="middle" dominantBaseline="middle" fontSize="9" fill="#94a3b8" fontWeight="700">{SHORT_DIR[facing]}</text>
          </svg>
          <div style={{ fontSize: 11, color: '#78350f', fontWeight: 700, marginTop: 4 }}>Facing: {facing.split('(')[0].trim()}</div>
        </div>

        {/* Room Direction Selectors */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: '#374151', marginBottom: 2 }}>Select direction for each room / element:</div>
          {VASTU_ROOMS.map(room => {
            const sel = selected[room.id]
            const rule = VASTU_RULES[room.id]
            const preview = sel ? rule?.tips?.[sel] : null
            return (
              <div key={room.id} style={{ background: '#f8fafc', borderRadius: 12, padding: '12px', border: sel ? `1.5px solid ${preview?.color ?? '#e2e8f0'}` : '1.5px solid #e2e8f0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 18 }}>{room.icon}</span>
                  <span style={{ fontSize: 13, fontWeight: 800, color: '#0f172a', flex: 1 }}>{room.label}</span>
                  {sel && preview && (
                    <span style={{ fontSize: 11, fontWeight: 800, background: `${preview.color}18`, color: preview.color, borderRadius: 20, padding: '2px 10px' }}>
                      {preview.verdict} ({preview.score})
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {DIRECTIONS.map(d => (
                    <button key={d} onClick={() => toggleRoom(room.id, d)}
                      style={{ fontSize: 11, fontWeight: 700, padding: '4px 9px', borderRadius: 8, cursor: 'pointer', border: '1px solid',
                        background: sel === d ? (rule?.tips?.[d]?.color + '18' ?? '#eff6ff') : '#fff',
                        borderColor: sel === d ? (rule?.tips?.[d]?.color ?? '#1a56db') : '#e2e8f0',
                        color: sel === d ? (rule?.tips?.[d]?.color ?? '#1a56db') : '#64748b' }}>
                      {SHORT_DIR[d]}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <button onClick={analyze} disabled={loading} style={g.genBtn}>
        {loading ? '🧿 Analysing Vastu...' : '🧿 Analyse Vastu Compatibility'}
      </button>

      {/* ── RESULTS ── */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Overall Score */}
          {(() => {
            const { label, color, bg } = OVERALL_SCORE_LABEL(result.overall)
            return (
              <div style={{ background: bg, borderRadius: 16, padding: '20px', border: `1px solid ${color}44`, display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ textAlign: 'center', minWidth: 90 }}>
                  <div style={{ fontSize: 52, fontWeight: 900, color, lineHeight: 1, letterSpacing: '-2px' }}>{result.overall}</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: 0.5 }}>Vastu Score</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 18, fontWeight: 900, color, marginBottom: 6 }}>{label}</div>
                  <div style={{ height: 10, background: '#e2e8f0', borderRadius: 99, overflow: 'hidden', maxWidth: 320 }}>
                    <div style={{ height: '100%', width: `${result.overall}%`, background: color, borderRadius: 99, transition: 'width 1s ease' }} />
                  </div>
                  <div style={{ fontSize: 12, color: '#64748b', marginTop: 6 }}>
                    Based on {result.scores.length} room{result.scores.length > 1 ? 's' : ''} analysed · {propType} · Facing {facing.split('(')[0].trim()}
                  </div>
                </div>
              </div>
            )
          })()}

          {/* Room Tab Selector */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {result.scores.map(sc => {
              const room = VASTU_ROOMS.find(r => r.id === sc.roomId)
              return (
                <button key={sc.roomId} onClick={() => setActiveRoom(sc.roomId)}
                  style={{ ...g.presetBtn, display: 'flex', gap: 6, alignItems: 'center',
                    ...(activeRoom === sc.roomId ? { background: `${sc.color}14`, border: `1.5px solid ${sc.color}`, color: sc.color, fontWeight: 800 } : {}) }}>
                  {room?.icon} {room?.label}
                  <span style={{ fontSize: 11, fontWeight: 900, background: `${sc.color}20`, color: sc.color, borderRadius: 10, padding: '1px 6px' }}>{sc.score}</span>
                </button>
              )
            })}
          </div>

          {/* Active Room Detail */}
          {activeRoom && (() => {
            const sc   = result.scores.find(s => s.roomId === activeRoom)
            const room = VASTU_ROOMS.find(r => r.id === activeRoom)
            if (!sc) return null
            return (
              <div style={{ background: '#fff', borderRadius: 16, padding: '20px', border: `1.5px solid ${sc.color}40` }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 14, flexWrap: 'wrap' }}>
                  <div style={{ width: 48, height: 48, borderRadius: 12, background: `${sc.color}14`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}>
                    {room?.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 16, fontWeight: 900, color: '#0f172a' }}>{room?.label}</span>
                      <span style={{ fontSize: 12, fontWeight: 800, background: `${sc.color}18`, color: sc.color, borderRadius: 20, padding: '3px 12px' }}>
                        {sc.verdict} — {sc.dir.split('(')[0].trim()}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, color: '#64748b', marginTop: 4, lineHeight: 1.6 }}>{sc.reason}</div>
                  </div>
                </div>

                {/* Score bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                  <div style={{ flex: 1, height: 8, background: '#f1f5f9', borderRadius: 99, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${sc.score}%`, background: sc.color, borderRadius: 99, transition: 'width 0.8s' }} />
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 900, color: sc.color, minWidth: 36 }}>{sc.score}/100</span>
                </div>

                {sc.fix ? (
                  <div style={{ background: '#fff7ed', borderRadius: 12, padding: '14px', border: '1px solid #fed7aa' }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#c2410c', marginBottom: 6 }}>🔧 Vastu Remedy</div>
                    <div style={{ fontSize: 13, color: '#7c2d12', lineHeight: 1.7 }}>{sc.fix}</div>
                  </div>
                ) : (
                  <div style={{ background: '#f0fdf4', borderRadius: 12, padding: '14px', border: '1px solid #bbf7d0' }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#065f46' }}>✅ No remedy needed — this placement is ideal per Vastu Shastra.</div>
                  </div>
                )}

                {/* Ideal directions */}
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: '#374151', marginBottom: 6 }}>Direction Reference:</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {DIRECTIONS.map(d => {
                      const t = VASTU_RULES[activeRoom]?.tips?.[d]
                      if (!t) return null
                      return (
                        <div key={d} title={d} style={{ fontSize: 11, fontWeight: 700, padding: '4px 10px', borderRadius: 8,
                          background: `${t.color}14`, color: t.color, border: `1px solid ${t.color}30` }}>
                          {SHORT_DIR[d]} · {t.score}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )
          })()}

          {/* Summary Table */}
          <div style={{ background: '#f8fafc', borderRadius: 14, padding: '16px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#374151', marginBottom: 10 }}>📋 Summary</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 400 }}>
                <thead>
                  <tr style={{ background: '#f1f5f9' }}>
                    {['Room','Direction','Score','Verdict','Remedy Needed'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', fontSize: 11, fontWeight: 800, color: '#64748b', textAlign: 'left', textTransform: 'uppercase', letterSpacing: 0.5, borderBottom: '2px solid #e2e8f0' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.scores.map((sc, i) => {
                    const room = VASTU_ROOMS.find(r => r.id === sc.roomId)
                    return (
                      <tr key={sc.roomId} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
                        <td style={{ padding: '9px 10px', fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{room?.icon} {room?.label}</td>
                        <td style={{ padding: '9px 10px', fontSize: 13, color: '#374151' }}>{sc.dir.split('(')[0].trim()}</td>
                        <td style={{ padding: '9px 10px' }}>
                          <span style={{ fontSize: 14, fontWeight: 900, color: sc.color }}>{sc.score}</span>
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          <span style={{ fontSize: 11, fontWeight: 800, background: `${sc.color}18`, color: sc.color, borderRadius: 20, padding: '2px 10px' }}>{sc.verdict}</span>
                        </td>
                        <td style={{ padding: '9px 10px', fontSize: 13 }}>{sc.fix ? '⚠️ Yes' : '✅ No'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <button onClick={() => toast('Vastu report downloaded!', 'success')} style={{ ...g.genBtn, background: 'linear-gradient(135deg,#059669,#0d9488)' }}>
            ⬇ Download Full Vastu Report
          </button>
        </div>
      )}
    </ToolCard>
  )
}

/* ─── Shared layout components ─── */
function ToolCard({ title, sub, children }) {
  return (
    <div style={g.toolCard}>
      <div style={g.toolHeader}>
        <h2 style={g.toolTitle}>{title}</h2>
        <p style={g.toolSub}>{sub}</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>{children}</div>
    </div>
  )
}
function FormRow({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 13, fontWeight: 700, color: '#374151' }}>{label}</label>
      {children}
    </div>
  )
}

const g = {
  twoCol:     (isMobile) => ({ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 14 }),
  input:      { border: '1.5px solid #e2e8f0', borderRadius: 10, padding: '10px 14px', fontSize: 14, outline: 'none', fontFamily: 'inherit', background: '#fafafa', width: '100%', boxSizing: 'border-box' },
  genBtn:     { background: 'linear-gradient(135deg,#1a56db,#7c3aed)', color: '#fff', border: 'none', borderRadius: 12, padding: '14px', fontSize: 15, fontWeight: 800, cursor: 'pointer', boxShadow: '0 4px 16px rgba(26,86,219,0.35)', letterSpacing: '-0.3px' },
  resultBox:  { background: '#f8fafc', borderRadius: 14, padding: '20px', border: '1px solid #e2e8f0' },
  resultHeader:{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  copyBtn:    { background: '#eff6ff', color: '#1a56db', border: 'none', borderRadius: 8, padding: '5px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer' },
  presetBtn:  { background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 20, padding: '5px 12px', fontSize: 12, cursor: 'pointer', color: '#374151' },
  loadBox:    { textAlign: 'center', padding: '20px' },
  loadBar:    { height: 6, background: '#e2e8f0', borderRadius: 99, overflow: 'hidden', maxWidth: 300, margin: '0 auto' },
  loadFill:   { height: '100%', background: 'linear-gradient(90deg,#1a56db,#7c3aed)', borderRadius: 99, animation: 'pulse 1.5s infinite', width: '60%' },
  renderCard: { borderRadius: 14, overflow: 'hidden', border: '1px solid #e2e8f0', background: '#fff' },
  renderImg:  { width: '100%', height: 200, objectFit: 'cover', display: 'block' },
  renderFooter:{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px' },
  renderTime: { fontSize: 11, color: '#94a3b8', flex: 1 },
  dlBtn:      { background: '#eff6ff', color: '#1a56db', border: 'none', borderRadius: 8, padding: '5px 10px', fontSize: 12, fontWeight: 700, cursor: 'pointer' },
  imgCard:    { borderRadius: 12, overflow: 'hidden', border: '1px solid #e2e8f0' },
  genImg:     { width: '100%', height: 180, objectFit: 'cover', display: 'block' },
  imgFooter:  { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px' },
  kwChip:     { background: '#eff6ff', color: '#1d4ed8', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 600 },
  chatBox:    { background: '#f8fafc', borderRadius: 14, padding: '16px', minHeight: 300, maxHeight: 400, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12, border: '1px solid #e2e8f0' },
  bubble:     { maxWidth: '80%', borderRadius: 14, padding: '10px 14px', fontSize: 14, lineHeight: 1.6 },
  bubbleBot:  { background: '#fff', border: '1px solid #e2e8f0', color: '#0f172a', borderTopLeftRadius: 4 },
  bubbleUser: { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', borderTopRightRadius: 4 },
  dots:       { letterSpacing: 2 },
  chatInput:  { display: 'flex', gap: 10 },
  chatField:  { flex: 1, border: '1.5px solid #e2e8f0', borderRadius: 12, padding: '11px 14px', fontSize: 14, outline: 'none' },
  sendBtn:    { background: 'linear-gradient(135deg,#1a56db,#2563eb)', color: '#fff', border: 'none', borderRadius: 12, padding: '11px 20px', fontSize: 14, fontWeight: 800, cursor: 'pointer', whiteSpace: 'nowrap' },
  toolCard:   { background: '#fff', borderRadius: 20, padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 1px 8px rgba(0,0,0,0.04)' },
  toolHeader: { marginBottom: 24, paddingBottom: 18, borderBottom: '1px solid #f1f5f9' },
  toolTitle:  { fontSize: 22, fontWeight: 900, color: '#0f172a', margin: '0 0 6px', letterSpacing: '-0.3px' },
  toolSub:    { fontSize: 14, color: '#64748b', margin: 0 },
}

const s = {
  page:       { background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem' },
  banner:     { background: 'linear-gradient(135deg,#0f172a 0%,#7c3aed 60%,#1a56db 100%)', color: '#fff', padding: '3.5rem 0', textAlign: 'center' },
  bannerInner:{ maxWidth: 700, margin: '0 auto', padding: '0 1.5rem' },
  heroBadge:  { display: 'inline-block', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 12, fontWeight: 700, marginBottom: 16 },
  h1:         { fontSize: 'clamp(26px,5vw,44px)', fontWeight: 900, margin: '0 0 12px', letterSpacing: '-1px' },
  sub:        { fontSize: 16, opacity: 0.8, lineHeight: 1.6, margin: 0 },
  layout:     { maxWidth: 1300, margin: '0 auto', padding: '2rem 1.5rem', display: 'grid', gridTemplateColumns: '240px 1fr', gap: 24, alignItems: 'start' },
  sidebar:    { display: 'flex', flexDirection: 'column', gap: 6, position: 'sticky', top: 80 },
  sideBtn:    { display: 'flex', alignItems: 'flex-start', gap: 12, background: '#fff', border: '1.5px solid #e2e8f0', borderRadius: 14, padding: '14px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s', color: '#374151' },
  sideBtnActive:{ background: 'linear-gradient(135deg,#eff6ff,#f5f3ff)', border: '1.5px solid #1a56db', color: '#1a56db', boxShadow: '0 4px 12px rgba(26,86,219,0.12)' },
  panel:      { minWidth: 0 },
}
