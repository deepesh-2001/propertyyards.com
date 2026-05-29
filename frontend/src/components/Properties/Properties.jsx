import React, { useState, useEffect } from 'react'
import { propertyAPI, wishlistAPI } from '../services/api'
import { FiMapPin, FiBed, FiBath, FiSquare, FiHeart, FiX, FiBarChart2, FiUser } from 'react-icons/fi'
import { RERABadge } from '../RERABadge'
import { EMICalculator } from '../EMICalculator'
import { useCompareStore } from '../../stores/compareStore'
import './Properties.css'

export function PropertyList() {
  const [properties, setProperties] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState(null)
  const limit = 20

  useEffect(() => {
    fetchProperties()
  }, [page])

  const fetchProperties = async () => {
    setIsLoading(true)
    try {
      const response = await propertyAPI.listProperties(page, limit)
      setProperties(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Error fetching properties:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddToWishlist = async (propertyId) => {
    try {
      await wishlistAPI.addToWishlist(propertyId)
      alert('Added to wishlist!')
    } catch (error) {
      alert('Error adding to wishlist')
    }
  }

  const pages = Math.ceil(total / limit)

  return (
    <div className="properties-container">
      <h1>Available Properties</h1>

      {isLoading ? (
        <div className="loading">Loading properties...</div>
      ) : properties.length === 0 ? (
        <div className="no-results">No properties found</div>
      ) : (
        <>
          <div className="properties-grid">
            {properties.map((property) => (
              <div
                key={property.id}
                className="property-card"
                onClick={() => setSelectedProperty(property)}
              >
                {property.images && property.images.length > 0 && (
                  <div className="property-image">
                    <img
                      src={property.images[0]}
                      alt={property.title}
                    />
                  </div>
                )}
                <div className="property-details">
                  <h3>{property.title}</h3>
                  <RERABadge rera_id={property.rera_id} verified={property.verified} />
                  <p className="price">${property.price.toLocaleString()}</p>
                  <p className="location">
                    <FiMapPin /> {property.city}, {property.state}
                  </p>
                  <div className="specs">
                    <span>
                      <FiBed /> {property.bedrooms}
                    </span>
                    <span>
                      <FiBath /> {property.bathrooms}
                    </span>
                    <span>
                      <FiSquare /> {property.area.toLocaleString()} sqft
                    </span>
                  </div>
                  {property.is_owner && (
                    <span className="owner-tag"><FiUser /> Listed by Owner</span>
                  )}
                  <div className="card-actions">
                    <button
                      className="wishlist-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAddToWishlist(property.id)
                      }}
                    >
                      <FiHeart /> Wishlist
                    </button>
                    <CompareToggle property={property} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pagination">
            <button
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            <span>
              Page {page} of {pages}
            </span>
            <button
              disabled={page === pages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}

      {selectedProperty && (
        <PropertyModal
          property={selectedProperty}
          onClose={() => setSelectedProperty(null)}
        />
      )}
    </div>
  )
}

function CompareToggle({ property }) {
  const has = useCompareStore((s) => s.has(property.id))
  const add = useCompareStore((s) => s.add)
  const remove = useCompareStore((s) => s.remove)
  const max = useCompareStore((s) => s.max)
  const count = useCompareStore((s) => s.items.length)

  return (
    <button
      className={`compare-toggle ${has ? 'active' : ''}`}
      onClick={(e) => {
        e.stopPropagation()
        if (has) remove(property.id)
        else {
          const ok = add(property)
          if (!ok && count >= max) alert(`You can only compare up to ${max} properties.`)
        }
      }}
      title={has ? 'Remove from compare' : 'Add to compare'}
    >
      <FiBarChart2 /> {has ? 'In compare' : 'Compare'}
    </button>
  )
}

function PropertyModal({ property, onClose }) {
  const [isInquiryOpen, setIsInquiryOpen] = useState(false)
  const [showEMI, setShowEMI] = useState(false)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <FiX />
        </button>

        {property.images && property.images.length > 0 && (
          <div className="modal-image">
            <img src={property.images[0]} alt={property.title} />
          </div>
        )}

        <div className="modal-body">
          <h2>{property.title}</h2>
          <RERABadge rera_id={property.rera_id} verified={property.verified} size="md" />
          <p className="price">${property.price.toLocaleString()}</p>
          <p className="location">
            <FiMapPin /> {property.location}, {property.city}, {property.state}
          </p>

          <div className="property-specs">
            <div>
              <FiBed /> {property.bedrooms} Bedrooms
            </div>
            <div>
              <FiBath /> {property.bathrooms} Bathrooms
            </div>
            <div>
              <FiSquare /> {property.area.toLocaleString()} sqft
            </div>
          </div>

          <p className="description">{property.description}</p>

          {property.amenities && property.amenities.length > 0 && (
            <div className="amenities">
              <h3>Amenities</h3>
              <ul>
                {property.amenities.map((amenity, idx) => (
                  <li key={idx}>{amenity}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="modal-actions">
            <button
              className="btn btn-primary"
              onClick={() => setIsInquiryOpen(true)}
            >
              Send Inquiry
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setShowEMI((v) => !v)}
            >
              {showEMI ? 'Hide' : 'Calculate'} EMI
            </button>
          </div>

          {showEMI && (
            <div style={{ marginTop: 16 }}>
              <EMICalculator price={property.price || 5000000} />
            </div>
          )}
        </div>

        {isInquiryOpen && (
          <InquiryForm
            propertyId={property.id}
            onClose={() => setIsInquiryOpen(false)}
          />
        )}
      </div>
    </div>
  )
}

function InquiryForm({ propertyId, onClose }) {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const { inquiryAPI } = await import('../services/api')
      await inquiryAPI.createInquiry({
        property_id: propertyId,
        message
      })
      alert('Inquiry sent successfully!')
      onClose()
    } catch (error) {
      alert('Error sending inquiry')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="inquiry-form">
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Enter your message..."
        required
        minLength="10"
      />
      <div className="form-buttons">
        <button type="submit" disabled={isLoading} className="btn btn-primary">
          {isLoading ? 'Sending...' : 'Send Inquiry'}
        </button>
        <button type="button" onClick={onClose} className="btn btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  )
}

export function PropertySearch() {
  const [filters, setFilters] = useState({
    query: '',
    city: '',
    min_price: '',
    max_price: '',
    min_bedrooms: '',
    property_type: '',
    owner_only: false,
    page: 1,
    limit: 20
  })
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [total, setTotal] = useState(0)

  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters((prev) => ({ ...prev, [name]: value, page: 1 }))
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const searchFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '')
      )
      const response = await propertyAPI.searchProperties(searchFilters)
      setResults(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Error searching properties:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="search-container">
      <h1>Search Properties</h1>

      <form onSubmit={handleSearch} className="search-form">
        <div className="form-row">
          <input
            type="text"
            name="query"
            placeholder="Search by title or location..."
            value={filters.query}
            onChange={handleFilterChange}
          />

          <input
            type="text"
            name="city"
            placeholder="City"
            value={filters.city}
            onChange={handleFilterChange}
          />
        </div>

        <div className="form-row">
          <input
            type="number"
            name="min_price"
            placeholder="Min Price"
            value={filters.min_price}
            onChange={handleFilterChange}
          />

          <input
            type="number"
            name="max_price"
            placeholder="Max Price"
            value={filters.max_price}
            onChange={handleFilterChange}
          />
        </div>

        <div className="form-row">
          <input
            type="number"
            name="min_bedrooms"
            placeholder="Min Bedrooms"
            value={filters.min_bedrooms}
            onChange={handleFilterChange}
          />

          <select
            name="property_type"
            value={filters.property_type}
            onChange={handleFilterChange}
          >
            <option value="">All Types</option>
            <option value="apartment">Apartment</option>
            <option value="house">House</option>
            <option value="condo">Condo</option>
            <option value="townhouse">Townhouse</option>
          </select>
        </div>

        <label className="owner-only-toggle">
          <input
            type="checkbox"
            name="owner_only"
            checked={filters.owner_only}
            onChange={(e) => setFilters((p) => ({ ...p, owner_only: e.target.checked, page: 1 }))}
          />
          <FiUser /> Listed by Owner only (No Broker)
        </label>

        <button type="submit" className="btn btn-primary">
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results.length > 0 && (
        <div className="search-results">
          <p>Found {total} properties</p>
          <div className="properties-grid">
            {results.map((property) => (
              <div key={property.id} className="property-card">
                {property.images && property.images.length > 0 && (
                  <div className="property-image">
                    <img src={property.images[0]} alt={property.title} />
                  </div>
                )}
                <div className="property-details">
                  <h3>{property.title}</h3>
                  <p className="price">${property.price.toLocaleString()}</p>
                  <p className="location">
                    <FiMapPin /> {property.city}
                  </p>
                  <div className="specs">
                    <span>
                      <FiBed /> {property.bedrooms}
                    </span>
                    <span>
                      <FiBath /> {property.bathrooms}
                    </span>
                    <span>
                      <FiSquare /> {property.area}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

