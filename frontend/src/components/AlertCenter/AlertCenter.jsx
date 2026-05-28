import React, { useState, useEffect } from 'react'
import { useAlertStore, ALERT_TYPES, ALERT_CATEGORIES } from '../../stores/alertStore'
import { 
  FiBell, FiCheckCircle, FiAlertTriangle, FiXCircle, FiInfo,
  FiShield, FiServer, FiTrendingUp, FiDollarSign, FiUsers,
  FiTrash2, FiCheck, FiSettings, FiVolume2, FiVolumeX,
  FiX, FiExternalLink, FiClock, FiFilter, FiRefreshCw
} from 'react-icons/fi'
import './AlertCenter.css'

const ALERT_CONFIG = {
  [ALERT_TYPES.SUCCESS]: { icon: <FiCheckCircle />, color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  [ALERT_TYPES.ERROR]: { icon: <FiXCircle />, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
  [ALERT_TYPES.WARNING]: { icon: <FiAlertTriangle />, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  [ALERT_TYPES.INFO]: { icon: <FiInfo />, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
  [ALERT_TYPES.SECURITY]: { icon: <FiShield />, color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)' },
  [ALERT_TYPES.SYSTEM]: { icon: <FiServer />, color: '#64748b', bg: 'rgba(100, 116, 139, 0.1)' },
  [ALERT_TYPES.REFERRAL]: { icon: <FiUsers />, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)' },
  [ALERT_TYPES.PRICING]: { icon: <FiDollarSign />, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  [ALERT_TYPES.SEO]: { icon: <FiTrendingUp />, color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' }
}

const PRIORITY_CONFIG = {
  high: { color: '#ef4444', label: 'High' },
  medium: { color: '#f59e0b', label: 'Medium' },
  low: { color: '#3b82f6', label: 'Low' }
}

export function AlertCenter() {
  const {
    alerts,
    unreadCount,
    isSoundEnabled,
    isNotificationsEnabled,
    alertHistory,
    addAlert,
    markAsRead,
    markAllAsRead,
    dismissAlert,
    clearAllAlerts,
    toggleSound,
    toggleNotifications,
    getFilteredAlerts,
    getAlertStats
  } = useAlertStore()

  const [activeTab, setActiveTab] = useState('all')
  const [filterType, setFilterType] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false)

  // Get filtered alerts based on tab and filters
  const getDisplayAlerts = () => {
    let filtered = [...alerts]
    
    // Tab filter
    if (activeTab === 'unread') {
      filtered = filtered.filter(a => !a.read)
    } else if (activeTab === 'system') {
      filtered = filtered.filter(a => a.category === ALERT_CATEGORIES.SYSTEM)
    } else if (activeTab === 'security') {
      filtered = filtered.filter(a => a.category === ALERT_CATEGORIES.SECURITY)
    } else if (activeTab === 'business') {
      filtered = filtered.filter(a => a.category === ALERT_CATEGORIES.BUSINESS)
    }
    
    // Type filter
    if (filterType) {
      filtered = filtered.filter(a => a.type === filterType)
    }
    
    // Priority filter
    if (filterPriority) {
      filtered = filtered.filter(a => a.priority === filterPriority)
    }
    
    return filtered
  }

  const displayAlerts = getDisplayAlerts()
  const stats = getAlertStats()

  // Simulate test alerts
  const simulateTestAlerts = () => {
    const testAlerts = [
      { type: ALERT_TYPES.SUCCESS, title: 'Test Success', message: 'Operation completed successfully', priority: 'low' },
      { type: ALERT_TYPES.ERROR, title: 'Test Error', message: 'Connection failed to backend', priority: 'high' },
      { type: ALERT_TYPES.WARNING, title: 'Test Warning', message: 'Cache size exceeding threshold', priority: 'medium' },
      { type: ALERT_TYPES.INFO, title: 'Test Info', message: 'New feature available in dashboard', priority: 'low' },
      { type: ALERT_TYPES.SECURITY, title: 'Security Alert', message: 'Unusual login activity detected', priority: 'high' },
      { type: ALERT_TYPES.SYSTEM, title: 'System Update', message: 'Database backup completed', priority: 'low' }
    ]
    
    testAlerts.forEach((alert, idx) => {
      setTimeout(() => addAlert(alert), idx * 500)
    })
  }

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return date.toLocaleDateString()
  }

  // Handle alert action
  const handleAction = (alert, action) => {
    if (action.action === 'view_referral') {
      window.location.href = `/referrals?id=${action.id}`
    } else if (action.action === 'approve_referral') {
      // Would call API to approve
      addAlert({
        type: ALERT_TYPES.SUCCESS,
        title: 'Referral Approved',
        message: 'Referral has been approved successfully',
        priority: 'low'
      })
    }
  }

  return (
    <div className="alert-center">
      {/* Header */}
      <div className="alert-header">
        <div className="header-title">
          <div className="bell-icon-container">
            <FiBell className="header-icon" />
            {unreadCount > 0 && <span className="unread-badge">{unreadCount}</span>}
          </div>
          <div>
            <h1>Alert Center</h1>
            <p>Manage notifications and system alerts</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-simulate" onClick={simulateTestAlerts}>
            <FiRefreshCw /> Simulate Alerts
          </button>
          <button className="btn-settings" onClick={() => setShowSettings(true)}>
            <FiSettings /> Settings
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="alert-stats">
        <div className="stat-card">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total Alerts</span>
        </div>
        <div className="stat-card unread">
          <span className="stat-value">{stats.unread}</span>
          <span className="stat-label">Unread</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.byType.security}</span>
          <span className="stat-label">Security</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.byType.error}</span>
          <span className="stat-label">Errors</span>
        </div>
      </div>

      {/* Filters & Tabs */}
      <div className="alert-controls">
        <div className="alert-tabs">
          <button className={activeTab === 'all' ? 'active' : ''} onClick={() => setActiveTab('all')}>
            All Alerts
          </button>
          <button className={activeTab === 'unread' ? 'active' : ''} onClick={() => setActiveTab('unread')}>
            Unread ({stats.unread})
          </button>
          <button className={activeTab === 'system' ? 'active' : ''} onClick={() => setActiveTab('system')}>
            System
          </button>
          <button className={activeTab === 'security' ? 'active' : ''} onClick={() => setActiveTab('security')}>
            Security
          </button>
          <button className={activeTab === 'business' ? 'active' : ''} onClick={() => setActiveTab('business')}>
            Business
          </button>
        </div>

        <div className="alert-filters">
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="">All Types</option>
            <option value={ALERT_TYPES.SUCCESS}>Success</option>
            <option value={ALERT_TYPES.ERROR}>Error</option>
            <option value={ALERT_TYPES.WARNING}>Warning</option>
            <option value={ALERT_TYPES.INFO}>Info</option>
            <option value={ALERT_TYPES.SECURITY}>Security</option>
            <option value={ALERT_TYPES.SYSTEM}>System</option>
          </select>
          <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}>
            <option value="">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <button className="btn-mark-read" onClick={markAllAsRead} disabled={stats.unread === 0}>
            <FiCheck /> Mark All Read
          </button>
          <button className="btn-clear" onClick={clearAllAlerts} disabled={stats.total === 0}>
            <FiTrash2 /> Clear All
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="alerts-container">
        {displayAlerts.length === 0 ? (
          <div className="no-alerts">
            <FiBell size={48} />
            <p>No alerts to display</p>
            <button onClick={simulateTestAlerts}>Generate Test Alerts</button>
          </div>
        ) : (
          <div className="alerts-list">
            {displayAlerts.map((alert) => {
              const config = ALERT_CONFIG[alert.type] || ALERT_CONFIG[ALERT_TYPES.INFO]
              const priority = PRIORITY_CONFIG[alert.priority]
              
              return (
                <div 
                  key={alert.id} 
                  className={`alert-item ${alert.read ? 'read' : 'unread'}`}
                  onClick={() => {
                    if (!alert.read) markAsRead(alert.id)
                    setSelectedAlert(alert)
                  }}
                >
                  <div className="alert-icon" style={{ color: config.color, background: config.bg }}>
                    {config.icon}
                  </div>
                  <div className="alert-content">
                    <div className="alert-header-row">
                      <span className="alert-title">{alert.title}</span>
                      <span className="alert-time">{formatTime(alert.timestamp)}</span>
                    </div>
                    <p className="alert-message">{alert.message}</p>
                    <div className="alert-meta">
                      <span className="alert-type" style={{ color: config.color }}>
                        {alert.type}
                      </span>
                      <span className="alert-priority" style={{ color: priority.color }}>
                        {priority.label}
                      </span>
                      {alert.category && (
                        <span className="alert-category">{alert.category}</span>
                      )}
                    </div>
                    {alert.actions && (
                      <div className="alert-actions">
                        {alert.actions.map((action, idx) => (
                          <button 
                            key={idx} 
                            className="btn-action"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(alert, action)
                            }}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="alert-controls">
                    {!alert.read && <div className="unread-dot" />}
                    <button 
                      className="btn-dismiss"
                      onClick={(e) => {
                        e.stopPropagation()
                        dismissAlert(alert.id)
                      }}
                    >
                      <FiX />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="modal-overlay" onClick={() => setSelectedAlert(null)}>
          <div className="modal-content alert-detail" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="detail-icon" style={{ 
                color: ALERT_CONFIG[selectedAlert.type]?.color,
                background: ALERT_CONFIG[selectedAlert.type]?.bg
              }}>
                {ALERT_CONFIG[selectedAlert.type]?.icon}
              </div>
              <div className="detail-title">
                <h3>{selectedAlert.title}</h3>
                <span className="detail-time">
                  <FiClock /> {new Date(selectedAlert.timestamp).toLocaleString()}
                </span>
              </div>
              <button className="btn-close" onClick={() => setSelectedAlert(null)}>
                <FiX />
              </button>
            </div>
            <div className="detail-body">
              <p className="detail-message">{selectedAlert.message}</p>
              {selectedAlert.data && (
                <div className="detail-data">
                  <h4>Additional Data</h4>
                  <pre>{JSON.stringify(selectedAlert.data, null, 2)}</pre>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                className="btn-mark-read"
                onClick={() => {
                  markAsRead(selectedAlert.id)
                  setSelectedAlert(null)
                }}
                disabled={selectedAlert.read}
              >
                <FiCheck /> Mark as Read
              </button>
              <button 
                className="btn-dismiss"
                onClick={() => {
                  dismissAlert(selectedAlert.id)
                  setSelectedAlert(null)
                }}
              >
                <FiTrash2 /> Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-content settings-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Alert Settings</h3>
            <div className="settings-list">
              <div className="setting-item">
                <div className="setting-info">
                  <FiVolume2 />
                  <div>
                    <span className="setting-name">Sound Notifications</span>
                    <span className="setting-desc">Play sound for high priority alerts</span>
                  </div>
                </div>
                <button 
                  className={`toggle ${isSoundEnabled ? 'on' : 'off'}`}
                  onClick={toggleSound}
                >
                  {isSoundEnabled ? <FiVolume2 /> : <FiVolumeX />}
                </button>
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <FiBell />
                  <div>
                    <span className="setting-name">Push Notifications</span>
                    <span className="setting-desc">Show browser notifications</span>
                  </div>
                </div>
                <button 
                  className={`toggle ${isNotificationsEnabled ? 'on' : 'off'}`}
                  onClick={toggleNotifications}
                >
                  {isNotificationsEnabled ? 'On' : 'Off'}
                </button>
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <FiRefreshCw />
                  <div>
                    <span className="setting-name">Real-time Alerts</span>
                    <span className="setting-desc">Receive live system updates</span>
                  </div>
                </div>
                <button 
                  className={`toggle ${isRealTimeEnabled ? 'on' : 'off'}`}
                  onClick={() => setIsRealTimeEnabled(!isRealTimeEnabled)}
                >
                  {isRealTimeEnabled ? 'On' : 'Off'}
                </button>
              </div>
            </div>
            <button className="btn-close-modal" onClick={() => setShowSettings(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Alert Toast Component for global notifications
export function AlertToast({ alert, onDismiss }) {
  const config = ALERT_CONFIG[alert.type] || ALERT_CONFIG[ALERT_TYPES.INFO]
  
  useEffect(() => {
    if (alert.autoDismiss) {
      const timer = setTimeout(() => onDismiss(alert.id), alert.dismissAfter || 5000)
      return () => clearTimeout(timer)
    }
  }, [alert, onDismiss])

  return (
    <div 
      className={`alert-toast ${alert.type}`}
      style={{ borderLeftColor: config.color }}
    >
      <div className="toast-icon" style={{ color: config.color }}>
        {config.icon}
      </div>
      <div className="toast-content">
        <h4>{alert.title}</h4>
        <p>{alert.message}</p>
      </div>
      <button className="toast-dismiss" onClick={() => onDismiss(alert.id)}>
        <FiX />
      </button>
    </div>
  )
}

// Global Alert Container
export function AlertContainer() {
  const { alerts, dismissAlert } = useAlertStore()
  const visibleAlerts = alerts.filter(a => !a.dismissed && (a.type === ALERT_TYPES.ERROR || a.type === ALERT_TYPES.WARNING || a.priority === 'high')).slice(0, 5)

  return (
    <div className="alert-container">
      {visibleAlerts.map((alert) => (
        <AlertToast key={alert.id} alert={alert} onDismiss={dismissAlert} />
      ))}
    </div>
  )
}

export default AlertCenter
