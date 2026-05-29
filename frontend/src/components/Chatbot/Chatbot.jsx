import React, { useState, useRef, useEffect } from 'react'
import { FiMessageCircle, FiX, FiSend } from 'react-icons/fi'
import './Chatbot.css'

const SUGGESTED = [
  'Show me 2BHK under ₹50L',
  'How does the EMI calculator work?',
  'Book a site visit',
  'What is RERA verification?',
]

export function Chatbot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'bot', text: '👋 Hi! I can help you find properties, calculate EMI, book site visits, or answer questions.' },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  const send = async (textOverride) => {
    const text = (textOverride ?? input).trim()
    if (!text) return
    setMessages((m) => [...m, { role: 'user', text }])
    setInput('')
    setSending(true)
    try {
      const r = await fetch('/api/chatbot/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({ message: text }),
      })
      let reply = 'Thanks! A team member will reach out via WhatsApp shortly.'
      if (r.ok) {
        const data = await r.json()
        reply = data.reply || data.message || reply
      }
      setMessages((m) => [...m, { role: 'bot', text: reply }])
    } catch {
      setMessages((m) => [...m, { role: 'bot', text: "I'm offline right now — but I've noted your message." }])
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <button className={`cb-fab ${open ? 'open' : ''}`} onClick={() => setOpen((v) => !v)} aria-label="Open chat">
        {open ? <FiX /> : <FiMessageCircle />}
      </button>
      {open && (
        <div className="cb-panel" role="dialog" aria-label="Chatbot">
          <div className="cb-header">
            <strong>PropertyYards Assistant</strong>
            <button onClick={() => setOpen(false)} aria-label="Close"><FiX /></button>
          </div>
          <div className="cb-messages">
            {messages.map((m, i) => (
              <div key={i} className={`cb-msg cb-${m.role}`}>{m.text}</div>
            ))}
            {sending && <div className="cb-msg cb-bot cb-typing">Typing…</div>}
            <div ref={endRef} />
          </div>
          <div className="cb-suggested">
            {SUGGESTED.map((s) => (
              <button key={s} className="cb-chip" onClick={() => send(s)}>{s}</button>
            ))}
          </div>
          <form
            className="cb-input"
            onSubmit={(e) => { e.preventDefault(); send() }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
            />
            <button type="submit" aria-label="Send"><FiSend /></button>
          </form>
        </div>
      )}
    </>
  )
}

export default Chatbot
