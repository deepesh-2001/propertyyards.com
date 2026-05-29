import React, { useState } from 'react'
import { FiShare2, FiCopy, FiCheck } from 'react-icons/fi'
import { FaWhatsapp, FaTelegram, FaFacebook, FaTwitter, FaLinkedin } from 'react-icons/fa'
import './SocialShare.css'

/**
 * SocialShare — share a property via WhatsApp, Telegram, Twitter, FB, LinkedIn, copy link.
 * Uses navigator.share when available (mobile), else falls back to per-network links.
 */
export function SocialShare({ title = 'Check out this property', url, text }) {
  const [copied, setCopied] = useState(false)
  const shareUrl = url || (typeof window !== 'undefined' ? window.location.href : '')
  const message = text || `${title} - ${shareUrl}`
  const enc = encodeURIComponent

  const tryNative = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title, text, url: shareUrl })
      } catch {/* user cancelled */}
    }
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {/* ignore */}
  }

  return (
    <div className="share">
      <button className="share-main" onClick={tryNative} title="Share">
        <FiShare2 /> Share
      </button>
      <div className="share-row">
        <a className="share-btn share-wa" target="_blank" rel="noreferrer"
           href={`https://wa.me/?text=${enc(message)}`} aria-label="WhatsApp">
          <FaWhatsapp />
        </a>
        <a className="share-btn share-tg" target="_blank" rel="noreferrer"
           href={`https://t.me/share/url?url=${enc(shareUrl)}&text=${enc(title)}`} aria-label="Telegram">
          <FaTelegram />
        </a>
        <a className="share-btn share-tw" target="_blank" rel="noreferrer"
           href={`https://twitter.com/intent/tweet?text=${enc(title)}&url=${enc(shareUrl)}`} aria-label="Twitter">
          <FaTwitter />
        </a>
        <a className="share-btn share-fb" target="_blank" rel="noreferrer"
           href={`https://www.facebook.com/sharer/sharer.php?u=${enc(shareUrl)}`} aria-label="Facebook">
          <FaFacebook />
        </a>
        <a className="share-btn share-ln" target="_blank" rel="noreferrer"
           href={`https://www.linkedin.com/sharing/share-offsite/?url=${enc(shareUrl)}`} aria-label="LinkedIn">
          <FaLinkedin />
        </a>
        <button className="share-btn share-copy" onClick={copy} aria-label="Copy link">
          {copied ? <FiCheck /> : <FiCopy />}
        </button>
      </div>
    </div>
  )
}

export default SocialShare
