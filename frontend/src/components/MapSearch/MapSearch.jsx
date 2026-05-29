import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { propertyAPI } from '../services/api'
import { Link } from 'react-router-dom'
import './MapSearch.css'

// Fix default marker icon path issue with Vite bundling.
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const DEFAULT_CENTER = [20.5937, 78.9629] // India
const DEFAULT_ZOOM = 5

function FitBounds({ points }) {
  const map = useMap()
  useEffect(() => {
    if (!points.length) return
    const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lng]))
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 })
  }, [points, map])
  return null
}

export function MapSearch() {
  const [properties, setProperties] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        const res = await propertyAPI.listProperties(1, 100)
        setProperties(res?.data?.items || [])
      } catch {
        // Mock data for offline / no-backend dev
        setProperties([
          { id: 'mock1', title: 'Sample Apartment', price: 7500000, lat: 12.9716, lng: 77.5946, city: 'Bengaluru' },
          { id: 'mock2', title: 'Beach House', price: 25000000, lat: 19.0760, lng: 72.8777, city: 'Mumbai' },
          { id: 'mock3', title: 'Studio Flat', price: 4500000, lat: 28.6139, lng: 77.2090, city: 'New Delhi' },
        ])
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [])

  const points = properties.filter((p) => p.lat && p.lng)

  return (
    <div className="map-search-page">
      <div className="map-search-header">
        <h1>Map Search</h1>
        <p>{isLoading ? 'Loading...' : `${points.length} properties on map`}</p>
      </div>
      <div className="map-search-container">
        <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} style={{ height: '70vh', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitBounds points={points} />
          {points.map((p) => (
            <Marker key={p.id} position={[p.lat, p.lng]}>
              <Popup>
                <strong>{p.title}</strong>
                <br />
                {p.city}
                <br />
                {typeof p.price === 'number' && `₹${p.price.toLocaleString('en-IN')}`}
                <br />
                <Link to={`/properties#${p.id}`}>View details</Link>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}

export default MapSearch
