import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Generate unique referral code
const generateReferralCode = () => {
  return 'REF-' + Math.random().toString(36).substring(2, 8).toUpperCase()
}

// Calculate earnings based on property value
const calculateEarnings = (propertyValue, commissionRate = 0.02) => {
  return Math.round(propertyValue * commissionRate)
}

export const useReferralStore = create(
  persist(
    (set, get) => ({
      // Referrals storage
      referrals: [],
      analytics: {
        totalReferrals: 0,
        totalEarnings: 0,
        conversionRate: 0,
        pendingReferrals: 0,
        approvedReferrals: 0,
        rejectedReferrals: 0,
        monthlyData: []
      },
      userPermissions: {},

      // Create new referral (for external users)
      createReferral: (referralData) => {
        const newReferral = {
          id: `ref-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          code: generateReferralCode(),
          referrerName: referralData.referrerName,
          referrerEmail: referralData.referrerEmail,
          referrerPhone: referralData.referrerPhone,
          propertyId: referralData.propertyId,
          propertyTitle: referralData.propertyTitle,
          propertyValue: referralData.propertyValue || 0,
          potentialEarnings: calculateEarnings(referralData.propertyValue || 0),
          buyerName: referralData.buyerName,
          buyerEmail: referralData.buyerEmail,
          buyerPhone: referralData.buyerPhone,
          status: 'pending', // pending, approved, rejected, converted
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          convertedAt: null,
          notes: referralData.notes || '',
          assignedTo: null,
          source: referralData.source || 'external',
          ipAddress: referralData.ipAddress || null,
          trackingData: {
            userAgent: referralData.userAgent || null,
            referrer: referralData.referrer || null,
            landingPage: referralData.landingPage || null
          }
        }

        set((state) => ({
          referrals: [newReferral, ...state.referrals],
          analytics: {
            ...state.analytics,
            totalReferrals: state.analytics.totalReferrals + 1,
            pendingReferrals: state.analytics.pendingReferrals + 1
          }
        }))

        return newReferral
      },

      // Update referral status
      updateReferralStatus: (referralId, status, userRole) => {
        // Check permissions
        if (!['admin', 'agent', 'manager'].includes(userRole)) {
          throw new Error('Insufficient permissions to update referral status')
        }

        set((state) => {
          const referral = state.referrals.find(r => r.id === referralId)
          if (!referral) return state

          const oldStatus = referral.status
          let analytics = { ...state.analytics }

          // Update analytics counts
          if (oldStatus !== status) {
            analytics[oldStatus + 'Referrals'] = Math.max(0, analytics[oldStatus + 'Referrals'] - 1)
            analytics[status + 'Referrals'] = (analytics[status + 'Referrals'] || 0) + 1

            if (status === 'converted') {
              analytics.totalEarnings += referral.potentialEarnings
              analytics.conversionRate = Math.round((analytics.approvedReferrals / analytics.totalReferrals) * 100)
            }
          }

          return {
            referrals: state.referrals.map(r =>
              r.id === referralId
                ? {
                    ...r,
                    status,
                    updatedAt: new Date().toISOString(),
                    convertedAt: status === 'converted' ? new Date().toISOString() : r.convertedAt
                  }
                : r
            ),
            analytics
          }
        })
      },

      // Assign referral to agent
      assignReferral: (referralId, agentId, agentName, userRole) => {
        if (!['admin', 'manager'].includes(userRole)) {
          throw new Error('Insufficient permissions to assign referrals')
        }

        set((state) => ({
          referrals: state.referrals.map(r =>
            r.id === referralId
              ? { ...r, assignedTo: { id: agentId, name: agentName }, updatedAt: new Date().toISOString() }
              : r
          )
        }))
      },

      // Add notes to referral
      addReferralNote: (referralId, note, userRole) => {
        if (!['admin', 'agent', 'manager'].includes(userRole)) {
          throw new Error('Insufficient permissions to add notes')
        }

        set((state) => ({
          referrals: state.referrals.map(r =>
            r.id === referralId
              ? {
                  ...r,
                  notes: r.notes ? `${r.notes}\n[${new Date().toLocaleString()}] ${note}` : `[${new Date().toLocaleString()}] ${note}`,
                  updatedAt: new Date().toISOString()
                }
              : r
          )
        }))
      },

      // Edit referral (admin only for most fields)
      editReferral: (referralId, updates, userRole, userId) => {
        const referral = get().referrals.find(r => r.id === referralId)
        if (!referral) throw new Error('Referral not found')

        // Admin can edit everything
        if (userRole === 'admin') {
          set((state) => ({
            referrals: state.referrals.map(r =>
              r.id === referralId
                ? { ...r, ...updates, updatedAt: new Date().toISOString() }
                : r
            )
          }))
          return
        }

        // Agent/Manager can only edit certain fields if assigned
        if (['agent', 'manager'].includes(userRole)) {
          if (referral.assignedTo?.id !== userId) {
            throw new Error('You can only edit referrals assigned to you')
          }

          const allowedFields = ['notes', 'status']
          const filteredUpdates = Object.keys(updates)
            .filter(key => allowedFields.includes(key))
            .reduce((obj, key) => {
              obj[key] = updates[key]
              return obj
            }, {})

          set((state) => ({
            referrals: state.referrals.map(r =>
              r.id === referralId
                ? { ...r, ...filteredUpdates, updatedAt: new Date().toISOString() }
                : r
            )
          }))
          return
        }

        // External users cannot edit
        throw new Error('You do not have permission to edit this referral')
      },

      // Delete referral (admin only)
      deleteReferral: (referralId, userRole) => {
        if (userRole !== 'admin') {
          throw new Error('Only admin can delete referrals')
        }

        set((state) => {
          const referral = state.referrals.find(r => r.id === referralId)
          if (!referral) return state

          return {
            referrals: state.referrals.filter(r => r.id !== referralId),
            analytics: {
              ...state.analytics,
              totalReferrals: Math.max(0, state.analytics.totalReferrals - 1),
              [referral.status + 'Referrals']: Math.max(0, state.analytics[referral.status + 'Referrals'] - 1),
              totalEarnings: referral.status === 'converted'
                ? Math.max(0, state.analytics.totalEarnings - referral.potentialEarnings)
                : state.analytics.totalEarnings
            }
          }
        })
      },

      // Get referrals by status
      getReferralsByStatus: (status) => {
        return get().referrals.filter(r => r.status === status)
      },

      // Get referrals by referrer
      getReferralsByReferrer: (email) => {
        return get().referrals.filter(r => r.referrerEmail === email)
      },

      // Get referrals assigned to agent
      getReferralsByAssignee: (agentId) => {
        return get().referrals.filter(r => r.assignedTo?.id === agentId)
      },

      // Get referral by code
      getReferralByCode: (code) => {
        return get().referrals.find(r => r.code === code)
      },

      // Calculate analytics
      calculateAnalytics: (timeRange = 'all') => {
        const state = get()
        const now = new Date()
        let filteredReferrals = state.referrals

        if (timeRange !== 'all') {
          const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365
          const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000)
          filteredReferrals = state.referrals.filter(r => new Date(r.createdAt) >= cutoffDate)
        }

        const totalReferrals = filteredReferrals.length
        const approvedReferrals = filteredReferrals.filter(r => r.status === 'approved' || r.status === 'converted').length
        const convertedReferrals = filteredReferrals.filter(r => r.status === 'converted').length
        const pendingReferrals = filteredReferrals.filter(r => r.status === 'pending').length
        const rejectedReferrals = filteredReferrals.filter(r => r.status === 'rejected').length
        const totalEarnings = filteredReferrals
          .filter(r => r.status === 'converted')
          .reduce((sum, r) => sum + r.potentialEarnings, 0)

        // Calculate monthly data
        const monthlyData = []
        for (let i = 11; i >= 0; i--) {
          const monthDate = new Date(now.getFullYear(), now.getMonth() - i, 1)
          const monthReferrals = filteredReferrals.filter(r => {
            const rDate = new Date(r.createdAt)
            return rDate.getMonth() === monthDate.getMonth() && rDate.getFullYear() === monthDate.getFullYear()
          })

          monthlyData.push({
            month: monthDate.toLocaleString('default', { month: 'short', year: '2-digit' }),
            referrals: monthReferrals.length,
            converted: monthReferrals.filter(r => r.status === 'converted').length,
            earnings: monthReferrals
              .filter(r => r.status === 'converted')
              .reduce((sum, r) => sum + r.potentialEarnings, 0)
          })
        }

        // Top referrers
        const referrerStats = {}
        filteredReferrals.forEach(r => {
          if (!referrerStats[r.referrerEmail]) {
            referrerStats[r.referrerEmail] = {
              name: r.referrerName,
              email: r.referrerEmail,
              totalReferrals: 0,
              converted: 0,
              earnings: 0
            }
          }
          referrerStats[r.referrerEmail].totalReferrals++
          if (r.status === 'converted') {
            referrerStats[r.referrerEmail].converted++
            referrerStats[r.referrerEmail].earnings += r.potentialEarnings
          }
        })

        const topReferrers = Object.values(referrerStats)
          .sort((a, b) => b.earnings - a.earnings)
          .slice(0, 10)

        return {
          totalReferrals,
          approvedReferrals,
          convertedReferrals,
          pendingReferrals,
          rejectedReferrals,
          totalEarnings,
          conversionRate: totalReferrals > 0 ? Math.round((convertedReferrals / totalReferrals) * 100) : 0,
          averageEarnings: convertedReferrals > 0 ? Math.round(totalEarnings / convertedReferrals) : 0,
          monthlyData,
          topReferrers,
          recentReferrals: filteredReferrals.slice(0, 10)
        }
      },

      // Export data for PDF/Excel
      getExportData: (format = 'json', filters = {}) => {
        let data = get().referrals

        // Apply filters
        if (filters.status) {
          data = data.filter(r => r.status === filters.status)
        }
        if (filters.dateFrom) {
          data = data.filter(r => new Date(r.createdAt) >= new Date(filters.dateFrom))
        }
        if (filters.dateTo) {
          data = data.filter(r => new Date(r.createdAt) <= new Date(filters.dateTo))
        }

        // Format data based on export type
        if (format === 'csv' || format === 'excel') {
          return data.map(r => ({
            'Referral Code': r.code,
            'Referrer Name': r.referrerName,
            'Referrer Email': r.referrerEmail,
            'Referrer Phone': r.referrerPhone,
            'Property': r.propertyTitle,
            'Property Value': r.propertyValue,
            'Potential Earnings': r.potentialEarnings,
            'Buyer Name': r.buyerName,
            'Status': r.status,
            'Created Date': new Date(r.createdAt).toLocaleString(),
            'Assigned To': r.assignedTo?.name || 'Unassigned',
            'Notes': r.notes
          }))
        }

        return data
      },

      // Clear all data (admin only)
      clearAllData: (userRole) => {
        if (userRole !== 'admin') {
          throw new Error('Only admin can clear all data')
        }

        set({
          referrals: [],
          analytics: {
            totalReferrals: 0,
            totalEarnings: 0,
            conversionRate: 0,
            pendingReferrals: 0,
            approvedReferrals: 0,
            rejectedReferrals: 0,
            monthlyData: []
          }
        })
      },

      // Initialize with test data
      initializeTestData: () => {
        const testReferrals = [
          {
            id: 'ref-1',
            code: 'REF-ABC123',
            referrerName: 'John Smith',
            referrerEmail: 'john@example.com',
            referrerPhone: '+91-9876543210',
            propertyId: 1,
            propertyTitle: 'Modern 3BHK Apartment',
            propertyValue: 750000,
            potentialEarnings: 15000,
            buyerName: 'Alice Johnson',
            buyerEmail: 'alice@example.com',
            status: 'converted',
            createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            convertedAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
            assignedTo: { id: 'agent-1', name: 'Mike Agent' }
          },
          {
            id: 'ref-2',
            code: 'REF-DEF456',
            referrerName: 'Sarah Wilson',
            referrerEmail: 'sarah@example.com',
            referrerPhone: '+91-9876543211',
            propertyId: 2,
            propertyTitle: 'Luxury Villa with Garden',
            propertyValue: 2500000,
            potentialEarnings: 50000,
            buyerName: 'Bob Williams',
            buyerEmail: 'bob@example.com',
            status: 'approved',
            createdAt: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
            assignedTo: { id: 'agent-1', name: 'Mike Agent' }
          },
          {
            id: 'ref-3',
            code: 'REF-GHI789',
            referrerName: 'David Brown',
            referrerEmail: 'david@example.com',
            referrerPhone: '+91-9876543212',
            propertyId: 3,
            propertyTitle: 'Cozy Studio Apartment',
            propertyValue: 350000,
            potentialEarnings: 7000,
            buyerName: 'Carol Davis',
            buyerEmail: 'carol@example.com',
            status: 'pending',
            createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
          }
        ]

        set({
          referrals: testReferrals,
          analytics: {
            totalReferrals: 3,
            totalEarnings: 15000,
            conversionRate: 33,
            pendingReferrals: 1,
            approvedReferrals: 1,
            rejectedReferrals: 0,
            monthlyData: []
          }
        })
      }
    }),
    {
      name: 'referral-storage',
      partialize: (state) => ({
        referrals: state.referrals,
        analytics: state.analytics
      })
    }
  )
)
