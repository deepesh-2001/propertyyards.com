import React, { useState, useEffect } from 'react'
import { usePricingStore, PRICING_TYPES, PRICING_TIERS } from '../../stores/pricingStore'
import { useAuthStore } from '../../stores/authStore'
import { useAccessControl } from '../../utils/accessControl'
import { FiDollarSign, FiTrendingUp, FiPercent, FiEdit2, FiTrash2, FiPlus, FiSave, FiRefreshCw, FiHistory } from 'react-icons/fi'
import './PricingAdmin.css'

const TYPE_LABELS = {
  property: '🏠 Property',
  subscription: '📦 Subscription',
  commission: '🤝 Commission',
  service_fee: '🔧 Service Fee',
  referral_bonus: '🎁 Referral Bonus'
}

const TIER_LABELS = {
  basic: 'Basic',
  standard: 'Standard',
  premium: 'Premium',
  enterprise: 'Enterprise'
}

export function PricingAdmin() {
  const user = useAuthStore((state) => state.user)
  const userRole = user?.role || 'external'
  const access = useAccessControl(userRole)

  const {
    pricingRules,
    subscriptionPlans,
    commissionRates,
    priceHistory,
    isLoading,
    error,
    fetchPricingRules,
    createPricingRule,
    updatePricingRule,
    deletePricingRule,
    bulkUpdatePrices,
    getPriceHistory,
    initializeDefaultPricing,
    getPricingStats,
    applyDiscount,
    setDynamicMultiplier
  } = usePricingStore()

  const [activeTab, setActiveTab] = useState('overview')
  const [selectedRule, setSelectedRule] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [editForm, setEditForm] = useState({})

  // Check admin access
  const isAdmin = userRole === 'admin'
  const isManager = userRole === 'manager'
  const canEdit = isAdmin || isManager

  useEffect(() => {
    fetchPricingRules()
  }, [])

  const handleEdit = (rule) => {
    if (!canEdit) {
      alert('Only admin or manager can edit pricing')
      return
    }
    setSelectedRule(rule)
    setEditForm({ ...rule })
    setIsEditing(true)
    setIsCreating(false)
  }

  const handleCreate = () => {
    if (!canEdit) {
      alert('Only admin or manager can create pricing rules')
      return
    }
    setIsCreating(true)
    setIsEditing(false)
    setEditForm({
      name: '',
      type: PRICING_TYPES.SUBSCRIPTION,
      tier: PRICING_TIERS.BASIC,
      base_price: 0,
      currency: 'USD',
      min_price: null,
      max_price: null,
      discount_percent: 0,
      dynamic_multiplier: 1.0,
      is_active: true,
      conditions: {},
      metadata: {}
    })
  }

  const handleSave = async () => {
    try {
      if (isCreating) {
        await createPricingRule(editForm, user.id)
        alert('Pricing rule created successfully!')
      } else {
        await updatePricingRule(selectedRule.id, editForm, user.id)
        alert('Pricing rule updated successfully!')
      }

      setIsEditing(false)
      setIsCreating(false)
      setSelectedRule(null)
      fetchPricingRules()
    } catch (error) {
      alert('Error: ' + error.message)
    }
  }

  const handleDelete = async (ruleId) => {
    if (!isAdmin) {
      alert('Only admin can delete pricing rules')
      return
    }

    if (!confirm('Are you sure you want to delete this pricing rule?')) return

    try {
      await deletePricingRule(ruleId)
      alert('Pricing rule deleted!')
      fetchPricingRules()
    } catch (error) {
      alert('Error: ' + error.message)
    }
  }

  const handleApplyDiscount = async (ruleId, discount) => {
    if (!canEdit) return

    try {
      await applyDiscount(ruleId, discount, user.id)
      alert(`Discount of ${discount}% applied!`)
      fetchPricingRules()
    } catch (error) {
      alert('Error: ' + error.message)
    }
  }

  const handleViewHistory = async (ruleId) => {
    await getPriceHistory(ruleId)
    setSelectedRule(pricingRules.find(r => r.id === ruleId))
    setActiveTab('history')
  }

  const filteredRules = filterType
    ? pricingRules.filter(r => r.type === filterType)
    : pricingRules

  const stats = getPricingStats()

  // Overview Tab
  const OverviewTab = () => (
    <div className="pricing-overview">
      <div className="stats-cards">
        <div className="stat-card blue">
          <FiDollarSign size={32} />
          <div className="stat-info">
            <span className="stat-value">{stats.totalRules}</span>
            <span className="stat-label">Total Rules</span>
          </div>
        </div>
        <div className="stat-card green">
          <FiTrendingUp size={32} />
          <div className="stat-info">
            <span className="stat-value">{stats.activeRules}</span>
            <span className="stat-label">Active Rules</span>
          </div>
        </div>
        <div className="stat-card purple">
          <FiPercent size={32} />
          <div className="stat-info">
            <span className="stat-value">{stats.subscriptionPlans}</span>
            <span className="stat-label">Subscription Plans</span>
          </div>
        </div>
        <div className="stat-card orange">
          <FiDollarSign size={32} />
          <div className="stat-info">
            <span className="stat-value">{stats.commissionRates}</span>
            <span className="stat-label">Commission Rates</span>
          </div>
        </div>
      </div>

      <div className="type-distribution">
        <h3>Pricing by Type</h3>
        <div className="type-bars">
          {Object.entries(stats.byType).map(([type, count]) => (
            <div key={type} className="type-bar">
              <span className="type-label">{TYPE_LABELS[type] || type}</span>
              <div className="bar-container">
                <div
                  className="bar"
                  style={{ width: `${stats.activeRules > 0 ? (count / stats.activeRules) * 100 : 0}%` }}
                />
              </div>
              <span className="type-count">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {!isAdmin && !isManager && (
        <div className="access-warning">
          <p>⚠️ View-only mode. Contact admin to modify pricing.</p>
        </div>
      )}
    </div>
  )

  // Rules Tab
  const RulesTab = () => (
    <div className="pricing-rules">
      <div className="rules-header">
        <div className="filter-section">
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="">All Types</option>
            {Object.entries(PRICING_TYPES).map(([key, value]) => (
              <option key={value} value={value}>{TYPE_LABELS[value] || value}</option>
            ))}
          </select>
        </div>
        {canEdit && (
          <button className="btn-create" onClick={handleCreate}>
            <FiPlus /> Create Rule
          </button>
        )}
      </div>

      <div className="rules-table-container">
        <table className="rules-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Tier</th>
              <th>Base Price</th>
              <th>Discount</th>
              <th>Multiplier</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredRules.map(rule => (
              <tr key={rule.id} className={rule.is_active ? '' : 'inactive'}>
                <td className="rule-name">{rule.name}</td>
                <td>{TYPE_LABELS[rule.type] || rule.type}</td>
                <td>{TIER_LABELS[rule.tier] || rule.tier || '-'}</td>
                <td className="price">${rule.base_price}</td>
                <td>{rule.discount_percent}%</td>
                <td>{rule.dynamic_multiplier}x</td>
                <td>
                  <span className={`status-badge ${rule.is_active ? 'active' : 'inactive'}`}>
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="actions">
                  {canEdit && (
                    <>
                      <button className="btn-action" onClick={() => handleEdit(rule)} title="Edit">
                        <FiEdit2 />
                      </button>
                      <button className="btn-action" onClick={() => handleViewHistory(rule.id)} title="History">
                        <FiHistory />
                      </button>
                    </>
                  )}
                  {isAdmin && (
                    <button className="btn-action danger" onClick={() => handleDelete(rule.id)} title="Delete">
                      <FiTrash2 />
                      </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredRules.length === 0 && (
          <div className="empty-state">
            <p>No pricing rules found</p>
            {canEdit && (
              <button className="btn-initialize" onClick={() => initializeDefaultPricing(user.id)}>
                Initialize Default Pricing
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )

  // Subscription Plans Tab
  const SubscriptionTab = () => (
    <div className="subscription-plans">
      <h3>Subscription Plans</h3>
      <div className="plans-grid">
        {subscriptionPlans.map(plan => (
          <div key={plan.id} className={`plan-card ${plan.tier}`}>
            <div className="plan-header">
              <h4>{plan.name}</h4>
              <span className="plan-tier">{TIER_LABELS[plan.tier]}</span>
            </div>
            <div className="plan-price">
              <span className="currency">$</span>
              <span className="amount">{plan.price}</span>
              <span className="period">/month</span>
            </div>
            {plan.discount > 0 && (
              <div className="plan-discount">{plan.discount}% OFF</div>
            )}
            <ul className="plan-features">
              {plan.features?.map((feature, idx) => (
                <li key={idx}>{feature}</li>
              )) || <li>Basic features</li>}
            </ul>
            {canEdit && (
              <div className="plan-actions">
                <button onClick={() => handleEdit(pricingRules.find(r => r.id === plan.id))}>
                  <FiEdit2 /> Edit
                </button>
                <div className="quick-discount">
                  <select onChange={(e) => e.target.value && handleApplyDiscount(plan.id, parseInt(e.target.value))}>
                    <option value="">Quick Discount...</option>
                    <option value="10">10% OFF</option>
                    <option value="20">20% OFF</option>
                    <option value="30">30% OFF</option>
                    <option value="50">50% OFF</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {subscriptionPlans.length === 0 && (
        <div className="empty-state">
          <p>No subscription plans configured</p>
          {canEdit && (
            <button className="btn-initialize" onClick={() => initializeDefaultPricing(user.id)}>
              Create Default Plans
            </button>
          )}
        </div>
      )}
    </div>
  )

  // Commission Rates Tab
  const CommissionTab = () => (
    <div className="commission-rates">
      <h3>Referral Commission Rates</h3>
      <div className="commission-cards">
        {commissionRates.map(rate => (
          <div key={rate.id} className="commission-card">
            <div className="commission-header">
              <h4>{rate.name}</h4>
              <span className="commission-percentage">{rate.percentage}%</span>
            </div>
            <div className="commission-details">
              <p>
                <strong>Min Amount:</strong> ${rate.min_amount?.toLocaleString() || 'None'}
              </p>
              <p>
                <strong>Max Amount:</strong> ${rate.max_amount?.toLocaleString() || 'None'}
              </p>
            </div>
            {canEdit && (
              <div className="commission-actions">
                <button onClick={() => handleEdit(pricingRules.find(r => r.id === rate.id))}>
                  <FiEdit2 /> Edit Rate
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {commissionRates.length === 0 && (
        <div className="empty-state">
          <p>No commission rates configured</p>
          {canEdit && (
            <button className="btn-initialize" onClick={() => initializeDefaultPricing(user.id)}>
              Create Default Rates
            </button>
          )}
        </div>
      )}
    </div>
  )

  // History Tab
  const HistoryTab = () => {
    const history = selectedRule ? priceHistory[selectedRule.id] : null

    return (
      <div className="price-history">
        {selectedRule ? (
          <>
            <h3>Price History: {selectedRule.name}</h3>
            <div className="history-list">
              {history?.history?.map((entry, idx) => (
                <div key={idx} className="history-item">
                  <div className="history-dot" />
                  <div className="history-content">
                    <span className="history-price">${entry.price}</span>
                    <span className="history-date">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                    <span className="history-reason">{entry.reason}</span>
                    <span className="history-by">by {entry.changed_by}</span>
                  </div>
                </div>
              )) || (
                <p className="no-history">No price history available</p>
              )}
            </div>
            <button className="btn-back" onClick={() => setActiveTab('rules')}>
              Back to Rules
            </button>
          </>
        ) : (
          <p>Select a pricing rule to view history</p>
        )}
      </div>
    )
  }

  // Edit/Create Modal
  const EditModal = () => (
    <div className="modal-overlay" onClick={() => { setIsEditing(false); setIsCreating(false); }}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>{isCreating ? 'Create Pricing Rule' : 'Edit Pricing Rule'}</h2>

        <div className="edit-form">
          <div className="form-group">
            <label>Rule Name</label>
            <input
              type="text"
              value={editForm.name || ''}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              placeholder="e.g., Premium Subscription"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select
                value={editForm.type}
                onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
              >
                {Object.entries(PRICING_TYPES).map(([key, value]) => (
                  <option key={value} value={value}>{TYPE_LABELS[value] || value}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Tier</label>
              <select
                value={editForm.tier || ''}
                onChange={(e) => setEditForm({ ...editForm, tier: e.target.value })}
              >
                <option value="">None</option>
                {Object.entries(PRICING_TIERS).map(([key, value]) => (
                  <option key={value} value={value}>{TIER_LABELS[value]}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Base Price ($)</label>
              <input
                type="number"
                step="0.01"
                value={editForm.base_price || 0}
                onChange={(e) => setEditForm({ ...editForm, base_price: parseFloat(e.target.value) })}
              />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <select
                value={editForm.currency || 'USD'}
                onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="INR">INR</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Discount %</label>
              <input
                type="number"
                min="0"
                max="100"
                value={editForm.discount_percent || 0}
                onChange={(e) => setEditForm({ ...editForm, discount_percent: parseFloat(e.target.value) })}
              />
            </div>
            <div className="form-group">
              <label>Dynamic Multiplier</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={editForm.dynamic_multiplier || 1.0}
                onChange={(e) => setEditForm({ ...editForm, dynamic_multiplier: parseFloat(e.target.value) })}
              />
              <small>1.0 = no change, 1.2 = 20% increase</small>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Price ($)</label>
              <input
                type="number"
                step="0.01"
                value={editForm.min_price || ''}
                onChange={(e) => setEditForm({ ...editForm, min_price: e.target.value ? parseFloat(e.target.value) : null })}
                placeholder="Optional"
              />
            </div>
            <div className="form-group">
              <label>Max Price ($)</label>
              <input
                type="number"
                step="0.01"
                value={editForm.max_price || ''}
                onChange={(e) => setEditForm({ ...editForm, max_price: e.target.value ? parseFloat(e.target.value) : null })}
                placeholder="Optional"
              />
            </div>
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={editForm.is_active}
                onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
              />
              Active
            </label>
          </div>

          <div className="final-price-preview">
            <strong>Final Price:</strong>
            <span className="final-amount">
              ${(editForm.base_price * (editForm.dynamic_multiplier || 1) * (1 - (editForm.discount_percent || 0) / 100)).toFixed(2)}
            </span>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn-save" onClick={handleSave}>
            <FiSave /> {isCreating ? 'Create' : 'Save'}
          </button>
          <button className="btn-cancel" onClick={() => { setIsEditing(false); setIsCreating(false); }}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  )

  if (!isAdmin && !isManager && userRole !== 'agent') {
    return (
      <div className="pricing-admin">
        <div className="access-denied">
          <h2>🔒 Access Denied</h2>
          <p>You do not have permission to view pricing management.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="pricing-admin">
      <div className="pricing-header">
        <div>
          <h1>💰 Dynamic Pricing Management</h1>
          <p>Manage prices, subscriptions, and commission rates</p>
        </div>
        <button className="btn-refresh" onClick={() => fetchPricingRules()}>
          <FiRefreshCw /> Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => usePricingStore.getState().clearError()}>×</button>
        </div>
      )}

      <div className="pricing-tabs">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={activeTab === 'rules' ? 'active' : ''} onClick={() => setActiveTab('rules')}>
          Pricing Rules
        </button>
        <button className={activeTab === 'subscriptions' ? 'active' : ''} onClick={() => setActiveTab('subscriptions')}>
          Subscriptions
        </button>
        <button className={activeTab === 'commission' ? 'active' : ''} onClick={() => setActiveTab('commission')}>
          Commission
        </button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          History
        </button>
      </div>

      <div className="pricing-content">
        {isLoading ? (
          <div className="loading">Loading pricing data...</div>
        ) : (
          <>
            {activeTab === 'overview' && <OverviewTab />}
            {activeTab === 'rules' && <RulesTab />}
            {activeTab === 'subscriptions' && <SubscriptionTab />}
            {activeTab === 'commission' && <CommissionTab />}
            {activeTab === 'history' && <HistoryTab />}
          </>
        )}
      </div>

      {(isEditing || isCreating) && <EditModal />}
    </div>
  )
}

export default PricingAdmin
