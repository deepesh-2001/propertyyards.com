import React, { useState, useEffect } from 'react'
import { useReferralStore } from '../../stores/referralStore'
import { useAuthStore } from '../../stores/authStore'
import { useAccessControl, ROLES, canEditReferral, canDeleteReferral, canAssignReferral, canApproveReferral, getEditRestrictionMessage } from '../../utils/accessControl'
import { FiEdit2, FiTrash2, FiCheck, FiX, FiUserPlus, FiDownload, FiEye, FiLock, FiUser } from 'react-icons/fi'
import './ReferralManagement.css'

// Mock agents list for assignment
const AGENTS = [
  { id: 'agent-1', name: 'Mike Agent' },
  { id: 'agent-2', name: 'Sarah Agent' },
  { id: 'agent-3', name: 'David Agent' }
]

const STATUS_COLORS = {
  pending: '#f59e0b',
  approved: '#22c55e',
  rejected: '#ef4444',
  converted: '#3b82f6'
}

const STATUS_LABELS = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  converted: 'Converted'
}

export function ReferralManagement() {
  const user = useAuthStore((state) => state.user)
  const userRole = user?.role || 'external'
  const userId = user?.id

  const access = useAccessControl(userRole)

  const {
    referrals,
    createReferral,
    updateReferralStatus,
    assignReferral,
    addReferralNote,
    editReferral,
    deleteReferral,
    getReferralsByAssignee,
    initializeTestData,
    getExportData
  } = useReferralStore()

  const [filteredReferrals, setFilteredReferrals] = useState([])
  const [selectedReferral, setSelectedReferral] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [filters, setFilters] = useState({ status: '', search: '' })
  const [editForm, setEditForm] = useState({})
  const [newNote, setNewNote] = useState('')
  const [notification, setNotification] = useState(null)

  // Initialize test data if empty
  useEffect(() => {
    if (referrals.length === 0) {
      initializeTestData()
    }
  }, [])

  // Filter referrals based on role and filters
  useEffect(() => {
    let data = referrals

    // Filter by role visibility
    if (!access.canViewAllReferrals()) {
      data = getReferralsByAssignee(userId)
    }

    // Apply status filter
    if (filters.status) {
      data = data.filter(r => r.status === filters.status)
    }

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      data = data.filter(r =>
        r.referrerName.toLowerCase().includes(searchLower) ||
        r.referrerEmail.toLowerCase().includes(searchLower) ||
        r.code.toLowerCase().includes(searchLower) ||
        r.propertyTitle.toLowerCase().includes(searchLower)
      )
    }

    setFilteredReferrals(data)
  }, [referrals, filters, userRole, userId])

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const handleCreateReferral = (formData) => {
    try {
      const referral = createReferral({
        ...formData,
        propertyValue: Number(formData.propertyValue) || 0,
        source: 'external'
      })
      setIsCreating(false)
      showNotification(`Referral created successfully! Code: ${referral.code}`)
    } catch (error) {
      showNotification(error.message, 'error')
    }
  }

  const handleStatusChange = (referralId, newStatus) => {
    try {
      const referral = referrals.find(r => r.id === referralId)
      if (!canApproveReferral(userRole, userId, referral)) {
        showNotification('You do not have permission to change this status', 'error')
        return
      }

      updateReferralStatus(referralId, newStatus, userRole)
      showNotification(`Status updated to ${STATUS_LABELS[newStatus]}`)
    } catch (error) {
      showNotification(error.message, 'error')
    }
  }

  const handleAssign = (referralId, agentId, agentName) => {
    try {
      if (!canAssignReferral(userRole)) {
        showNotification('You do not have permission to assign referrals', 'error')
        return
      }

      assignReferral(referralId, agentId, agentName, userRole)
      showNotification(`Assigned to ${agentName}`)
    } catch (error) {
      showNotification(error.message, 'error')
    }
  }

  const handleAddNote = (referralId) => {
    if (!newNote.trim()) return

    try {
      addReferralNote(referralId, newNote, userRole)
      setNewNote('')
      showNotification('Note added successfully')
    } catch (error) {
      showNotification(error.message, 'error')
    }
  }

  const handleEdit = (referral) => {
    if (!canEditReferral(userRole, userId, referral)) {
      showNotification('You do not have permission to edit this referral', 'error')
      return
    }

    setSelectedReferral(referral)
    setEditForm({
      notes: referral.notes,
      status: referral.status
    })
    setIsEditing(true)
  }

  const handleSaveEdit = () => {
    try {
      editReferral(selectedReferral.id, editForm, userRole, userId)
      setIsEditing(false)
      setSelectedReferral(null)
      showNotification('Changes saved successfully')
    } catch (error) {
      showNotification(error.message, 'error')
    }
  }

  const handleDelete = (referralId) => {
    if (!canDeleteReferral(userRole)) {
      showNotification('Only admin can delete referrals', 'error')
      return
    }

    if (!confirm('Are you sure you want to delete this referral?')) return

    try {
      deleteReferral(referralId, userRole)
      showNotification('Referral deleted')
    } catch (error) {
      showNotification(error.message, 'error')
    }
  }

  const exportToCSV = () => {
    if (!access.canExportData()) {
      showNotification('You do not have permission to export data', 'error')
      return
    }

    const data = getExportData('csv', filters)
    if (data.length === 0) {
      showNotification('No data to export', 'error')
      return
    }

    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `referrals-${new Date().toISOString().split('T')[0]}.csv`
    link.click()

    showNotification('CSV exported successfully')
  }

  return (
    <div className="referral-management">
      <div className="referral-header">
        <div>
          <h1>🤝 Referral Management</h1>
          <p className="access-info">
            <FiLock /> {getEditRestrictionMessage(userRole)}
          </p>
        </div>
        <div className="referral-actions">
          <button className="btn-action btn-primary" onClick={() => setIsCreating(true)}>
            + Create Referral
          </button>
          {access.canExportData() && (
            <button className="btn-action" onClick={exportToCSV}>
              <FiDownload /> Export CSV
            </button>
          )}
        </div>
      </div>

      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Filters */}
      <div className="filters-bar">
        <input
          type="text"
          placeholder="Search referrals..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="search-input"
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="filter-select"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="converted">Converted</option>
        </select>
      </div>

      {/* Referrals Table */}
      <div className="referrals-table-container">
        <table className="referrals-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Referrer</th>
              <th>Property</th>
              <th>Value</th>
              <th>Earnings</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredReferrals.map((referral) => (
              <tr key={referral.id} className={referral.status}>
                <td className="code-cell">
                  <span className="referral-code">{referral.code}</span>
                </td>
                <td>
                  <div className="referrer-info">
                    <span className="name">{referral.referrerName}</span>
                    <span className="email">{referral.referrerEmail}</span>
                  </div>
                </td>
                <td>{referral.propertyTitle}</td>
                <td>${referral.propertyValue?.toLocaleString()}</td>
                <td className="earnings">${referral.potentialEarnings?.toLocaleString()}</td>
                <td>
                  <span
                    className="status-badge"
                    style={{ backgroundColor: STATUS_COLORS[referral.status] + '20', color: STATUS_COLORS[referral.status] }}
                  >
                    {STATUS_LABELS[referral.status]}
                  </span>
                </td>
                <td>
                  {referral.assignedTo ? (
                    <span className="assigned-to">
                      <FiUser size={14} /> {referral.assignedTo.name}
                    </span>
                  ) : (
                    <span className="unassigned">Unassigned</span>
                  )}
                </td>
                <td>{new Date(referral.createdAt).toLocaleDateString()}</td>
                <td>
                  <div className="action-buttons">
                    <button
                      className="btn-icon"
                      onClick={() => setSelectedReferral(referral)}
                      title="View Details"
                    >
                      <FiEye />
                    </button>

                    {canEditReferral(userRole, userId, referral) && (
                      <button
                        className="btn-icon"
                        onClick={() => handleEdit(referral)}
                        title="Edit"
                      >
                        <FiEdit2 />
                      </button>
                    )}

                    {canApproveReferral(userRole, userId, referral) && referral.status === 'pending' && (
                      <>
                        <button
                          className="btn-icon btn-success"
                          onClick={() => handleStatusChange(referral.id, 'approved')}
                          title="Approve"
                        >
                          <FiCheck />
                        </button>
                        <button
                          className="btn-icon btn-danger"
                          onClick={() => handleStatusChange(referral.id, 'rejected')}
                          title="Reject"
                        >
                          <FiX />
                        </button>
                      </>
                    )}

                    {canApproveReferral(userRole, userId, referral) && referral.status === 'approved' && (
                      <button
                        className="btn-icon btn-primary"
                        onClick={() => handleStatusChange(referral.id, 'converted')}
                        title="Mark as Converted"
                      >
                        <FiCheck /> Convert
                      </button>
                    )}

                    {canAssignReferral(userRole) && !referral.assignedTo && (
                      <div className="assign-dropdown">
                        <button className="btn-icon" title="Assign">
                          <FiUserPlus />
                        </button>
                        <div className="dropdown-menu">
                          {AGENTS.map(agent => (
                            <button
                              key={agent.id}
                              onClick={() => handleAssign(referral.id, agent.id, agent.name)}
                            >
                              {agent.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {canDeleteReferral(userRole) && (
                      <button
                        className="btn-icon btn-danger"
                        onClick={() => handleDelete(referral.id)}
                        title="Delete"
                      >
                        <FiTrash2 />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredReferrals.length === 0 && (
          <div className="empty-state">
            <p>No referrals found</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {isCreating && (
        <div className="modal-overlay" onClick={() => setIsCreating(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Referral</h2>
            <ReferralForm onSubmit={handleCreateReferral} onCancel={() => setIsCreating(false)} />
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {isEditing && selectedReferral && (
        <div className="modal-overlay" onClick={() => setIsEditing(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Edit Referral</h2>
            <div className="edit-form">
              <div className="form-group">
                <label>Status</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                >
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="converted">Converted</option>
                </select>
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  rows={4}
                />
              </div>
              <div className="form-actions">
                <button className="btn-primary" onClick={handleSaveEdit}>Save Changes</button>
                <button className="btn-secondary" onClick={() => setIsEditing(false)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedReferral && !isEditing && (
        <div className="modal-overlay" onClick={() => setSelectedReferral(null)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h2>Referral Details</h2>
            <div className="referral-details">
              <div className="detail-section">
                <h3>Referrer Information</h3>
                <p><strong>Name:</strong> {selectedReferral.referrerName}</p>
                <p><strong>Email:</strong> {selectedReferral.referrerEmail}</p>
                <p><strong>Phone:</strong> {selectedReferral.referrerPhone}</p>
              </div>

              <div className="detail-section">
                <h3>Property Information</h3>
                <p><strong>Title:</strong> {selectedReferral.propertyTitle}</p>
                <p><strong>Value:</strong> ${selectedReferral.propertyValue?.toLocaleString()}</p>
                <p><strong>Potential Earnings:</strong> ${selectedReferral.potentialEarnings?.toLocaleString()}</p>
              </div>

              <div className="detail-section">
                <h3>Buyer Information</h3>
                <p><strong>Name:</strong> {selectedReferral.buyerName}</p>
                <p><strong>Email:</strong> {selectedReferral.buyerEmail}</p>
                <p><strong>Phone:</strong> {selectedReferral.buyerPhone}</p>
              </div>

              <div className="detail-section">
                <h3>Status & Assignment</h3>
                <p>
                  <strong>Status:</strong>
                  <span
                    className="status-badge"
                    style={{ backgroundColor: STATUS_COLORS[selectedReferral.status] + '20', color: STATUS_COLORS[selectedReferral.status] }}
                  >
                    {STATUS_LABELS[selectedReferral.status]}
                  </span>
                </p>
                <p><strong>Referral Code:</strong> {selectedReferral.code}</p>
                <p><strong>Assigned To:</strong> {selectedReferral.assignedTo?.name || 'Unassigned'}</p>
                <p><strong>Created:</strong> {new Date(selectedReferral.createdAt).toLocaleString()}</p>
                {selectedReferral.convertedAt && (
                  <p><strong>Converted:</strong> {new Date(selectedReferral.convertedAt).toLocaleString()}</p>
                )}
              </div>

              <div className="detail-section full-width">
                <h3>Notes</h3>
                <pre className="notes-content">{selectedReferral.notes || 'No notes'}</pre>

                {access.hasPermission('referral:edit') && (
                  <div className="add-note-form">
                    <textarea
                      placeholder="Add a note..."
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      rows={3}
                    />
                    <button className="btn-primary" onClick={() => handleAddNote(selectedReferral.id)}>
                      Add Note
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-actions">
              {canEditReferral(userRole, userId, selectedReferral) && (
                <button className="btn-primary" onClick={() => handleEdit(selectedReferral)}>
                  <FiEdit2 /> Edit
                </button>
              )}
              <button className="btn-secondary" onClick={() => setSelectedReferral(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Referral Form Component
function ReferralForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    referrerName: '',
    referrerEmail: '',
    referrerPhone: '',
    propertyId: '',
    propertyTitle: '',
    propertyValue: '',
    buyerName: '',
    buyerEmail: '',
    buyerPhone: '',
    notes: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="referral-form">
      <div className="form-row">
        <div className="form-group">
          <label>Referrer Name *</label>
          <input
            type="text"
            required
            value={formData.referrerName}
            onChange={(e) => setFormData({ ...formData, referrerName: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Referrer Email *</label>
          <input
            type="email"
            required
            value={formData.referrerEmail}
            onChange={(e) => setFormData({ ...formData, referrerEmail: e.target.value })}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Referrer Phone</label>
          <input
            type="tel"
            value={formData.referrerPhone}
            onChange={(e) => setFormData({ ...formData, referrerPhone: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Property Title *</label>
          <input
            type="text"
            required
            value={formData.propertyTitle}
            onChange={(e) => setFormData({ ...formData, propertyTitle: e.target.value })}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Property Value ($)</label>
          <input
            type="number"
            value={formData.propertyValue}
            onChange={(e) => setFormData({ ...formData, propertyValue: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Buyer Name *</label>
          <input
            type="text"
            required
            value={formData.buyerName}
            onChange={(e) => setFormData({ ...formData, buyerName: e.target.value })}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Buyer Email</label>
          <input
            type="email"
            value={formData.buyerEmail}
            onChange={(e) => setFormData({ ...formData, buyerEmail: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Buyer Phone</label>
          <input
            type="tel"
            value={formData.buyerPhone}
            onChange={(e) => setFormData({ ...formData, buyerPhone: e.target.value })}
          />
        </div>
      </div>

      <div className="form-group">
        <label>Notes</label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          rows={3}
        />
      </div>

      <div className="form-actions">
        <button type="submit" className="btn-primary">Create Referral</button>
        <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

export default ReferralManagement
