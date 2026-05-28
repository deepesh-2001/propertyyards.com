import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Pricing Service API URL
const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || 'http://localhost:8009'

export const PRICING_TYPES = {
  PROPERTY: 'property',
  SUBSCRIPTION: 'subscription',
  COMMISSION: 'commission',
  SERVICE_FEE: 'service_fee',
  REFERRAL_BONUS: 'referral_bonus'
}

export const PRICING_TIERS = {
  BASIC: 'basic',
  STANDARD: 'standard',
  PREMIUM: 'premium',
  ENTERPRISE: 'enterprise'
}

export const usePricingStore = create(
  persist(
    (set, get) => ({
      // Pricing rules cache
      pricingRules: [],
      subscriptionPlans: [],
      commissionRates: [],
      currentPricing: {},
      priceHistory: {},

      // Loading states
      isLoading: false,
      error: null,

      // Fetch all pricing rules
      fetchPricingRules: async (filters = {}) => {
        set({ isLoading: true, error: null })
        try {
          const params = new URLSearchParams(filters)
          const response = await fetch(`${PRICING_API_URL}/rules?${params}`)

          if (!response.ok) throw new Error('Failed to fetch pricing rules')

          const rules = await response.json()
          set({ pricingRules: rules, isLoading: false })
          return rules
        } catch (error) {
          set({ error: error.message, isLoading: false })
          return []
        }
      },

      // Create new pricing rule
      createPricingRule: async (ruleData, userId) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${PRICING_API_URL}/rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...ruleData,
              created_by: userId,
              valid_from: new Date().toISOString()
            })
          })

          if (!response.ok) throw new Error('Failed to create pricing rule')

          const newRule = await response.json()

          set((state) => ({
            pricingRules: [newRule, ...state.pricingRules],
            isLoading: false
          }))

          return newRule
        } catch (error) {
          set({ error: error.message, isLoading: false })
          throw error
        }
      },

      // Update pricing rule
      updatePricingRule: async (ruleId, updates, userId) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${PRICING_API_URL}/rules/${ruleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...updates,
              updated_by: userId,
              updated_at: new Date().toISOString()
            })
          })

          if (!response.ok) throw new Error('Failed to update pricing rule')

          const updatedRule = await response.json()

          set((state) => ({
            pricingRules: state.pricingRules.map(r =>
              r.id === ruleId ? updatedRule : r
            ),
            isLoading: false
          }))

          return updatedRule
        } catch (error) {
          set({ error: error.message, isLoading: false })
          throw error
        }
      },

      // Delete pricing rule
      deletePricingRule: async (ruleId) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${PRICING_API_URL}/rules/${ruleId}`, {
            method: 'DELETE'
          })

          if (!response.ok) throw new Error('Failed to delete pricing rule')

          set((state) => ({
            pricingRules: state.pricingRules.filter(r => r.id !== ruleId),
            isLoading: false
          }))

          return true
        } catch (error) {
          set({ error: error.message, isLoading: false })
          throw error
        }
      },

      // Bulk update prices
      bulkUpdatePrices: async (updates, userId) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${PRICING_API_URL}/bulk-update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              updates,
              changed_by: userId
            })
          })

          if (!response.ok) throw new Error('Failed to bulk update prices')

          const result = await response.json()

          // Refresh pricing rules
          await get().fetchPricingRules()

          set({ isLoading: false })
          return result
        } catch (error) {
          set({ error: error.message, isLoading: false })
          throw error
        }
      },

      // Calculate price dynamically
      calculatePrice: async (calculationData) => {
        try {
          const response = await fetch(`${PRICING_API_URL}/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(calculationData)
          })

          if (!response.ok) throw new Error('Failed to calculate price')

          return await response.json()
        } catch (error) {
          console.error('Price calculation error:', error)
          return null
        }
      },

      // Get current pricing for type
      getCurrentPricing: async (type) => {
        try {
          const response = await fetch(`${PRICING_API_URL}/current/${type}`)

          if (!response.ok) throw new Error('Failed to fetch current pricing')

          const data = await response.json()

          set((state) => ({
            currentPricing: {
              ...state.currentPricing,
              [type]: data
            }
          }))

          return data
        } catch (error) {
          console.error('Get current pricing error:', error)
          return null
        }
      },

      // Get price history
      getPriceHistory: async (ruleId) => {
        try {
          const response = await fetch(`${PRICING_API_URL}/history/${ruleId}`)

          if (!response.ok) throw new Error('Failed to fetch price history')

          const data = await response.json()

          set((state) => ({
            priceHistory: {
              ...state.priceHistory,
              [ruleId]: data
            }
          }))

          return data
        } catch (error) {
          console.error('Get price history error:', error)
          return null
        }
      },

      // Fetch subscription plans
      fetchSubscriptionPlans: async () => {
        try {
          const response = await fetch(`${PRICING_API_URL}/subscription-plans`)

          if (!response.ok) throw new Error('Failed to fetch subscription plans')

          const data = await response.json()
          set({ subscriptionPlans: data.plans })
          return data.plans
        } catch (error) {
          console.error('Fetch subscription plans error:', error)
          return []
        }
      },

      // Fetch commission rates
      fetchCommissionRates: async () => {
        try {
          const response = await fetch(`${PRICING_API_URL}/commission-rates`)

          if (!response.ok) throw new Error('Failed to fetch commission rates')

          const data = await response.json()
          set({ commissionRates: data.rates })
          return data.rates
        } catch (error) {
          console.error('Fetch commission rates error:', error)
          return []
        }
      },

      // Update commission rate (shortcut)
      updateCommissionRate: async (rateId, newPercentage, userId) => {
        return get().updatePricingRule(rateId, {
          base_price: newPercentage,
          name: `Updated commission rate to ${newPercentage}%`
        }, userId)
      },

      // Update subscription price (shortcut)
      updateSubscriptionPrice: async (planId, newPrice, userId) => {
        return get().updatePricingRule(planId, {
          base_price: newPrice
        }, userId)
      },

      // Apply discount to pricing rule
      applyDiscount: async (ruleId, discountPercent, userId) => {
        const rule = get().pricingRules.find(r => r.id === ruleId)
        if (!rule) throw new Error('Rule not found')

        return get().updatePricingRule(ruleId, {
          discount_percent: discountPercent,
          name: `${rule.name} (${discountPercent}% off)`
        }, userId)
      },

      // Set dynamic multiplier
      setDynamicMultiplier: async (ruleId, multiplier, userId) => {
        return get().updatePricingRule(ruleId, {
          dynamic_multiplier: multiplier
        }, userId)
      },

      // Clear error
      clearError: () => set({ error: null }),

      // Get pricing stats
      getPricingStats: () => {
        const state = get()
        const activeRules = state.pricingRules.filter(r => r.is_active)

        return {
          totalRules: state.pricingRules.length,
          activeRules: activeRules.length,
          byType: {
            property: activeRules.filter(r => r.type === PRICING_TYPES.PROPERTY).length,
            subscription: activeRules.filter(r => r.type === PRICING_TYPES.SUBSCRIPTION).length,
            commission: activeRules.filter(r => r.type === PRICING_TYPES.COMMISSION).length,
            service_fee: activeRules.filter(r => r.type === PRICING_TYPES.SERVICE_FEE).length,
            referral_bonus: activeRules.filter(r => r.type === PRICING_TYPES.REFERRAL_BONUS).length
          },
          subscriptionPlans: state.subscriptionPlans.length,
          commissionRates: state.commissionRates.length
        }
      },

      // Initialize with default pricing data
      initializeDefaultPricing: async (userId) => {
        const defaultRules = [
          // Subscription Plans
          {
            name: 'Free Plan',
            type: PRICING_TYPES.SUBSCRIPTION,
            tier: PRICING_TIERS.BASIC,
            base_price: 0,
            currency: 'USD',
            metadata: {
              features: ['View properties', 'Basic search', 'Save favorites']
            }
          },
          {
            name: 'Basic Plan',
            type: PRICING_TYPES.SUBSCRIPTION,
            tier: PRICING_TIERS.STANDARD,
            base_price: 9.99,
            currency: 'USD',
            metadata: {
              features: ['All free features', 'Contact agents', 'Property alerts', '3D tours']
            }
          },
          {
            name: 'Professional Plan',
            type: PRICING_TYPES.SUBSCRIPTION,
            tier: PRICING_TIERS.PREMIUM,
            base_price: 29.99,
            currency: 'USD',
            metadata: {
              features: ['All basic features', 'Priority support', 'AI recommendations', 'Market reports']
            }
          },
          {
            name: 'Enterprise Plan',
            type: PRICING_TYPES.SUBSCRIPTION,
            tier: PRICING_TIERS.ENTERPRISE,
            base_price: 99.99,
            currency: 'USD',
            metadata: {
              features: ['All pro features', 'Dedicated manager', 'API access', 'White-label options']
            }
          },
          // Commission Rates
          {
            name: 'Standard Referral Commission',
            type: PRICING_TYPES.COMMISSION,
            base_price: 2.0, // 2%
            currency: 'USD',
            conditions: {
              min_amount: 0,
              max_amount: 1000000
            }
          },
          {
            name: 'Premium Referral Commission',
            type: PRICING_TYPES.COMMISSION,
            base_price: 2.5, // 2.5%
            currency: 'USD',
            conditions: {
              min_amount: 1000000,
              max_amount: 5000000
            }
          }
        ]

        const created = []
        for (const rule of defaultRules) {
          try {
            const newRule = await get().createPricingRule(rule, userId)
            created.push(newRule)
          } catch (e) {
            console.error('Failed to create default rule:', e)
          }
        }

        return created
      }
    }),
    {
      name: 'pricing-storage',
      partialize: (state) => ({
        subscriptionPlans: state.subscriptionPlans,
        commissionRates: state.commissionRates
      })
    }
  )
)
