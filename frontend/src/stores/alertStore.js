import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const ALERT_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  SECURITY: 'security',
  SYSTEM: 'system',
  REFERRAL: 'referral',
  PRICING: 'pricing',
  SEO: 'seo'
}

export const ALERT_CATEGORIES = {
  SYSTEM: 'system',
  SECURITY: 'security',
  BUSINESS: 'business',
  USER: 'user'
}

export const useAlertStore = create(
  persist(
    (set, get) => ({
      // Alerts state
      alerts: [],
      unreadCount: 0,
      isSoundEnabled: true,
      isNotificationsEnabled: true,
      
      // Alert history
      alertHistory: [],
      
      // System health alerts
      systemAlerts: [],
      
      // Security alerts
      securityAlerts: [],
      
      // Add new alert
      addAlert: (alert) => {
        const newAlert = {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          read: false,
          dismissed: false,
          ...alert
        }
        
        set((state) => ({
          alerts: [newAlert, ...state.alerts].slice(0, 100), // Keep last 100
          unreadCount: state.unreadCount + 1,
          alertHistory: [newAlert, ...state.alertHistory].slice(0, 500)
        }))
        
        // Play sound if enabled
        if (get().isSoundEnabled && alert.priority === 'high') {
          get().playAlertSound()
        }
        
        return newAlert
      },
      
      // Mark alert as read
      markAsRead: (alertId) => {
        set((state) => ({
          alerts: state.alerts.map(a => 
            a.id === alertId ? { ...a, read: true } : a
          ),
          unreadCount: Math.max(0, state.unreadCount - 1)
        }))
      },
      
      // Mark all as read
      markAllAsRead: () => {
        set((state) => ({
          alerts: state.alerts.map(a => ({ ...a, read: true })),
          unreadCount: 0
        }))
      },
      
      // Dismiss alert
      dismissAlert: (alertId) => {
        set((state) => ({
          alerts: state.alerts.filter(a => a.id !== alertId),
          unreadCount: state.alerts.find(a => a.id === alertId && !a.read) 
            ? Math.max(0, state.unreadCount - 1) 
            : state.unreadCount
        }))
      },
      
      // Clear all alerts
      clearAllAlerts: () => {
        set({ alerts: [], unreadCount: 0 })
      },
      
      // Play alert sound
      playAlertSound: () => {
        try {
          const audio = new Audio('/alert-sound.mp3')
          audio.volume = 0.5
          audio.play().catch(() => {})
        } catch (e) {
          console.log('Audio play failed')
        }
      },
      
      // Toggle sound
      toggleSound: () => {
        set((state) => ({ isSoundEnabled: !state.isSoundEnabled }))
      },
      
      // Toggle notifications
      toggleNotifications: () => {
        set((state) => ({ isNotificationsEnabled: !state.isNotificationsEnabled }))
      },
      
      // System alert helpers
      addSystemAlert: (message, details = {}) => {
        return get().addAlert({
          type: ALERT_TYPES.SYSTEM,
          category: ALERT_CATEGORIES.SYSTEM,
          title: 'System Alert',
          message,
          priority: details.priority || 'medium',
          ...details
        })
      },
      
      // Security alert helpers
      addSecurityAlert: (message, details = {}) => {
        return get().addAlert({
          type: ALERT_TYPES.SECURITY,
          category: ALERT_CATEGORIES.SECURITY,
          title: 'Security Alert',
          message,
          priority: details.priority || 'high',
          ...details
        })
      },
      
      // Success alert helpers
      addSuccessAlert: (message, details = {}) => {
        return get().addAlert({
          type: ALERT_TYPES.SUCCESS,
          category: ALERT_CATEGORIES.USER,
          title: 'Success',
          message,
          priority: 'low',
          autoDismiss: true,
          dismissAfter: 5000,
          ...details
        })
      },
      
      // Error alert helpers
      addErrorAlert: (message, details = {}) => {
        return get().addAlert({
          type: ALERT_TYPES.ERROR,
          category: ALERT_CATEGORIES.USER,
          title: 'Error',
          message,
          priority: 'high',
          ...details
        })
      },
      
      // Warning alert helpers
      addWarningAlert: (message, details = {}) => {
        return get().addAlert({
          type: ALERT_TYPES.WARNING,
          category: ALERT_CATEGORIES.USER,
          title: 'Warning',
          message,
          priority: 'medium',
          ...details
        })
      },
      
      // Info alert helpers
      addInfoAlert: (message, details = {}) => {
        return get().addAlert({
          type: ALERT_TYPES.INFO,
          category: ALERT_CATEGORIES.USER,
          title: 'Information',
          message,
          priority: 'low',
          autoDismiss: true,
          dismissAfter: 8000,
          ...details
        })
      },
      
      // Referral alert
      addReferralAlert: (referralData) => {
        return get().addAlert({
          type: ALERT_TYPES.REFERRAL,
          category: ALERT_CATEGORIES.BUSINESS,
          title: 'New Referral',
          message: `${referralData.referrerName} submitted a referral for ${referralData.propertyTitle}`,
          priority: 'medium',
          data: referralData,
          actions: [
            { label: 'View', action: 'view_referral', id: referralData.id },
            { label: 'Approve', action: 'approve_referral', id: referralData.id }
          ]
        })
      },
      
      // Pricing alert
      addPricingAlert: (pricingData) => {
        return get().addAlert({
          type: ALERT_TYPES.PRICING,
          category: ALERT_CATEGORIES.BUSINESS,
          title: 'Price Change',
          message: `${pricingData.name} price updated to $${pricingData.base_price}`,
          priority: 'medium',
          data: pricingData
        })
      },
      
      // SEO alert
      addSEOAlert: (seoData) => {
        return get().addAlert({
          type: ALERT_TYPES.SEO,
          category: ALERT_CATEGORIES.BUSINESS,
          title: 'SEO Update',
          message: seoData.message,
          priority: seoData.priority || 'low',
          data: seoData
        })
      },
      
      // Get filtered alerts
      getFilteredAlerts: (filters = {}) => {
        const { type, category, priority, read, timeRange } = filters
        let filtered = [...get().alerts]
        
        if (type) filtered = filtered.filter(a => a.type === type)
        if (category) filtered = filtered.filter(a => a.category === category)
        if (priority) filtered = filtered.filter(a => a.priority === priority)
        if (read !== undefined) filtered = filtered.filter(a => a.read === read)
        if (timeRange) {
          const cutoff = new Date(Date.now() - timeRange).toISOString()
          filtered = filtered.filter(a => a.timestamp > cutoff)
        }
        
        return filtered
      },
      
      // Get alert statistics
      getAlertStats: () => {
        const state = get()
        return {
          total: state.alerts.length,
          unread: state.unreadCount,
          byType: {
            success: state.alerts.filter(a => a.type === ALERT_TYPES.SUCCESS).length,
            error: state.alerts.filter(a => a.type === ALERT_TYPES.ERROR).length,
            warning: state.alerts.filter(a => a.type === ALERT_TYPES.WARNING).length,
            info: state.alerts.filter(a => a.type === ALERT_TYPES.INFO).length,
            security: state.alerts.filter(a => a.type === ALERT_TYPES.SECURITY).length,
            system: state.alerts.filter(a => a.type === ALERT_TYPES.SYSTEM).length
          },
          byPriority: {
            high: state.alerts.filter(a => a.priority === 'high').length,
            medium: state.alerts.filter(a => a.priority === 'medium').length,
            low: state.alerts.filter(a => a.priority === 'low').length
          }
        }
      },
      
      // Simulate real-time alerts
      simulateRealTimeAlerts: () => {
        const scenarios = [
          { type: 'system', fn: () => get().addSystemAlert('High CPU usage detected', { priority: 'medium' }) },
          { type: 'security', fn: () => get().addSecurityAlert('Failed login attempt blocked', { priority: 'high' }) },
          { type: 'success', fn: () => get().addSuccessAlert('Cache cleared successfully') },
          { type: 'info', fn: () => get().addInfoAlert('Daily backup completed') }
        ]
        
        // Random alert every 30-60 seconds
        const scheduleNext = () => {
          const delay = Math.floor(Math.random() * 30000) + 30000
          setTimeout(() => {
            const scenario = scenarios[Math.floor(Math.random() * scenarios.length)]
            scenario.fn()
            scheduleNext()
          }, delay)
        }
        
        scheduleNext()
      }
    }),
    {
      name: 'alert-storage',
      partialize: (state) => ({
        isSoundEnabled: state.isSoundEnabled,
        isNotificationsEnabled: state.isNotificationsEnabled,
        alertHistory: state.alertHistory
      })
    }
  )
)
