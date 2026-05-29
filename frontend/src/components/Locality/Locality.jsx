import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FiMapPin, FiTrendingUp, FiHome, FiUsers, FiAlertCircle } from 'react-icons/fi'
import './Locality.css'

// Curated featured localities for SEO-rich pages.
const FEATURED = [
  { slug: 'bengaluru-koramangala', city: 'Bengaluru', name: 'Koramangala' },
  { slug: 'mumbai-bandra', city: 'Mumbai', name: 'Bandra West' },
  { slug: 'delhi-saket', city: 'Delhi', name: 'Saket' },
  { slug: 'pune-hinjewadi', city: 'Pune', name: 'Hinjewadi' },
  { slug: 'hyderabad-gachibowli', city: 'Hyderabad', name: 'Gachibowli' },
  { slug: 'chennai-omr', city: 'Chennai', name: 'OMR' },
]

export function LocalityIndex() {
  return (
    <div className="locality-page">
      <div className="locality-header">
        <h1><FiMapPin /> Explore Localities</h1>
        <p>Average prices, amenities, and properties for the most-searched neighborhoods.</p>
      </div>
      <div className="locality-grid">
        {FEATURED.map((l) => (
          <Link key={l.slug} to={`/locality/${l.slug}`} className="locality-card">
            <div className="locality-card-img" style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }} />
            <div className="locality-card-body">
              <h3>{l.name}</h3>
              <span>{l.city}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

export function LocalityDetail() {
  const { slug } = useParams()
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch(`/api/localities/${slug}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setData)
      .catch(() => {
        // mock data fallback
        const meta = FEATURED.find((f) => f.slug === slug)
        setData({
          name: meta?.name || slug,
          city: meta?.city || '',
          avg_price_sqft: 8500,
          ytd_change_pct: 4.2,
          properties_count: 142,
          population_estimate: 95000,
          schools: ['Delhi Public School', 'Greenwood High', 'St. Joseph’s'],
          metros: ['Indiranagar', 'MG Road'],
          hospitals: ['Manipal Hospital', 'Apollo Clinic'],
          summary:
            `${meta?.name || 'This area'} is a well-connected residential locality known for vibrant nightlife, modern apartments, and easy access to tech parks.`,
          highlights: [
            'Walkable streets',
            'High rental yield',
            'Strong metro connectivity',
            'Top-rated international schools',
          ],
        })
      })
  }, [slug])

  if (!data) return <div className="locality-page">Loading…</div>

  return (
    <div className="locality-page">
      <Link to="/locality" className="locality-back">← All localities</Link>
      <div className="locality-detail-header">
        <h1>{data.name}{data.city && `, ${data.city}`}</h1>
        <p>{data.summary}</p>
      </div>

      <div className="locality-stats">
        <div className="locality-stat">
          <FiHome /> <strong>{data.properties_count}</strong> Properties
        </div>
        <div className="locality-stat">
          <FiTrendingUp /> <strong>₹{data.avg_price_sqft?.toLocaleString('en-IN')}</strong>/sqft
        </div>
        <div className="locality-stat">
          <FiTrendingUp /> <strong>{data.ytd_change_pct > 0 ? '+' : ''}{data.ytd_change_pct}%</strong> YoY
        </div>
        <div className="locality-stat">
          <FiUsers /> <strong>{data.population_estimate?.toLocaleString('en-IN')}</strong> Residents
        </div>
      </div>

      <div className="locality-sections">
        <section>
          <h2>Highlights</h2>
          <ul>{data.highlights?.map((h, i) => <li key={i}>{h}</li>)}</ul>
        </section>
        <section>
          <h2>Nearby</h2>
          <div className="locality-nearby">
            {data.schools?.length > 0 && (
              <div><h4>🏫 Schools</h4><ul>{data.schools.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            )}
            {data.hospitals?.length > 0 && (
              <div><h4>🏥 Hospitals</h4><ul>{data.hospitals.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            )}
            {data.metros?.length > 0 && (
              <div><h4>🚇 Metro</h4><ul>{data.metros.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            )}
          </div>
        </section>
      </div>

      <div className="locality-cta">
        <FiAlertCircle />
        <span>Showing estimated stats. Live data appears once backend localities are wired.</span>
      </div>
    </div>
  )
}
