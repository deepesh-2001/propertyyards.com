import React, { useState } from 'react'
import { FiBell, FiMail, FiTrash2, FiPlus, FiSearch } from 'react-icons/fi'
import { useSavedSearchStore } from '../../stores/savedSearchStore'
import './SavedSearches.css'

export function SavedSearchesPage() {
  const searches = useSavedSearchStore((s) => s.searches)
  const remove = useSavedSearchStore((s) => s.remove)
  const updateAlerts = useSavedSearchStore((s) => s.updateAlerts)

  return (
    <div className="ss-page">
      <div className="ss-header">
        <h1><FiBell /> Saved Searches & Alerts</h1>
        <p>Get notified by email or WhatsApp when new properties match your saved searches.</p>
      </div>

      {!searches.length ? (
        <div className="ss-empty">
          <FiSearch size={32} />
          <h3>No saved searches yet</h3>
          <p>Save a search from the Search page and we'll alert you when matching properties appear.</p>
          <a className="ss-btn ss-btn-primary" href="/search">Go to Search</a>
        </div>
      ) : (
        <div className="ss-list">
          {searches.map((s) => (
            <div key={s.id} className="ss-item">
              <div className="ss-item-main">
                <h3>{s.name}</h3>
                <div className="ss-filters">
                  {Object.entries(s.filters)
                    .filter(([_, v]) => v !== '' && v != null && v !== false)
                    .map(([k, v]) => (
                      <span key={k} className="ss-chip">
                        <strong>{k.replace(/_/g, ' ')}:</strong> {String(v)}
                      </span>
                    ))}
                </div>
                <small>Saved {new Date(s.createdAt).toLocaleDateString()}</small>
              </div>
              <div className="ss-item-actions">
                <label className="ss-toggle">
                  <input
                    type="checkbox"
                    checked={s.alerts?.email ?? true}
                    onChange={(e) => updateAlerts(s.id, { email: e.target.checked })}
                  />
                  <FiMail /> Email
                </label>
                <label className="ss-toggle">
                  <input
                    type="checkbox"
                    checked={s.alerts?.whatsapp ?? false}
                    onChange={(e) => updateAlerts(s.id, { whatsapp: e.target.checked })}
                  />
                  <FiBell /> WhatsApp
                </label>
                <button className="ss-btn ss-btn-danger" onClick={() => remove(s.id)}>
                  <FiTrash2 />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * SaveSearchButton — drop into PropertySearch to save current filters.
 */
export function SaveSearchButton({ filters, defaultName }) {
  const add = useSavedSearchStore((s) => s.add)
  const [saving, setSaving] = useState(false)

  const handle = () => {
    setSaving(true)
    const name = defaultName || prompt('Name this search:', 'My search') || 'My search'
    add({ name, filters })
    setTimeout(() => setSaving(false), 800)
  }

  return (
    <button type="button" className="ss-btn ss-btn-secondary" onClick={handle} disabled={saving}>
      <FiPlus /> {saving ? 'Saved!' : 'Save search & alert me'}
    </button>
  )
}

export default SavedSearchesPage
