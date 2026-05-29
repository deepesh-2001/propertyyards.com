import React, { useEffect, useState } from 'react'
import { FiRss, FiExternalLink } from 'react-icons/fi'
import './NewsFeed.css'

const MOCK = [
  { id: 1, title: 'RBI keeps repo rate unchanged — home loans steady', source: 'Economic Times', url: '#', publishedAt: new Date().toISOString() },
  { id: 2, title: 'Bengaluru property prices rise 4.1% YoY', source: 'Hindu Business Line', url: '#', publishedAt: new Date().toISOString() },
  { id: 3, title: 'Top 10 affordable localities in Mumbai 2025', source: 'PropertyYards Blog', url: '#', publishedAt: new Date().toISOString() },
  { id: 4, title: 'Stamp duty changes in Maharashtra explained', source: 'LiveMint', url: '#', publishedAt: new Date().toISOString() },
  { id: 5, title: 'NRIs driving demand in Hyderabad luxury market', source: 'Moneycontrol', url: '#', publishedAt: new Date().toISOString() },
]

/**
 * NewsFeed — list of real-estate headlines. Hits /api/news and falls back to mock.
 * Use as a sidebar or full page.
 */
export function NewsFeed({ limit = 5, compact = false }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    let cancelled = false
    fetch('/api/news?category=real-estate')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => !cancelled && setItems(Array.isArray(data) ? data : data.items || []))
      .catch(() => !cancelled && setItems(MOCK))
    return () => { cancelled = true }
  }, [])

  const list = items.slice(0, limit)

  return (
    <div className={`news-feed ${compact ? 'compact' : ''}`}>
      <div className="news-header">
        <FiRss /> <h3>Real Estate News</h3>
      </div>
      <ul>
        {list.map((n) => (
          <li key={n.id} className="news-item">
            <a href={n.url} target="_blank" rel="noreferrer">
              {n.title} <FiExternalLink />
            </a>
            <small>{n.source} · {new Date(n.publishedAt).toLocaleDateString()}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function NewsPage() {
  return (
    <div className="news-page">
      <div className="news-page-inner">
        <NewsFeed limit={50} />
      </div>
    </div>
  )
}

export default NewsFeed
