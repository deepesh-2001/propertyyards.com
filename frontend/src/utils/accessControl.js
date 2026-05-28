// Role-Based Access Control (RBAC) Utilities

// Role hierarchy and permissions
export const ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  AGENT: 'agent',
  BUYER: 'buyer',
  SELLER: 'seller',
  EXTERNAL: 'external' // For referral partners
}

// Permission definitions
export const PERMISSIONS = {
  // Referral permissions
  REFERRAL_CREATE: 'referral:create',
  REFERRAL_VIEW: 'referral:view',
  REFERRAL_VIEW_ALL: 'referral:view_all',
  REFERRAL_EDIT: 'referral:edit',
  REFERRAL_EDIT_ALL: 'referral:edit_all',
  REFERRAL_DELETE: 'referral:delete',
  REFERRAL_ASSIGN: 'referral:assign',
  REFERRAL_APPROVE: 'referral:approve',
  REFERRAL_EXPORT: 'referral:export',

  // Analytics permissions
  ANALYTICS_VIEW: 'analytics:view',
  ANALYTICS_VIEW_ALL: 'analytics:view_all',
  ANALYTICS_EXPORT: 'analytics:export',

  // User management
  USER_MANAGE: 'user:manage',
  USER_VIEW: 'user:view'
}

// Role-based permission mapping
export const ROLE_PERMISSIONS = {
  [ROLES.ADMIN]: [
    PERMISSIONS.REFERRAL_CREATE,
    PERMISSIONS.REFERRAL_VIEW,
    PERMISSIONS.REFERRAL_VIEW_ALL,
    PERMISSIONS.REFERRAL_EDIT,
    PERMISSIONS.REFERRAL_EDIT_ALL,
    PERMISSIONS.REFERRAL_DELETE,
    PERMISSIONS.REFERRAL_ASSIGN,
    PERMISSIONS.REFERRAL_APPROVE,
    PERMISSIONS.REFERRAL_EXPORT,
    PERMISSIONS.ANALYTICS_VIEW,
    PERMISSIONS.ANALYTICS_VIEW_ALL,
    PERMISSIONS.ANALYTICS_EXPORT,
    PERMISSIONS.USER_MANAGE,
    PERMISSIONS.USER_VIEW
  ],
  [ROLES.MANAGER]: [
    PERMISSIONS.REFERRAL_CREATE,
    PERMISSIONS.REFERRAL_VIEW,
    PERMISSIONS.REFERRAL_VIEW_ALL,
    PERMISSIONS.REFERRAL_EDIT,
    PERMISSIONS.REFERRAL_ASSIGN,
    PERMISSIONS.REFERRAL_APPROVE,
    PERMISSIONS.REFERRAL_EXPORT,
    PERMISSIONS.ANALYTICS_VIEW,
    PERMISSIONS.ANALYTICS_VIEW_ALL,
    PERMISSIONS.ANALYTICS_EXPORT,
    PERMISSIONS.USER_VIEW
  ],
  [ROLES.AGENT]: [
    PERMISSIONS.REFERRAL_CREATE,
    PERMISSIONS.REFERRAL_VIEW,
    PERMISSIONS.REFERRAL_EDIT,
    PERMISSIONS.ANALYTICS_VIEW
  ],
  [ROLES.BUYER]: [
    PERMISSIONS.REFERRAL_CREATE,
    PERMISSIONS.REFERRAL_VIEW
  ],
  [ROLES.SELLER]: [
    PERMISSIONS.REFERRAL_CREATE,
    PERMISSIONS.REFERRAL_VIEW
  ],
  [ROLES.EXTERNAL]: [
    PERMISSIONS.REFERRAL_CREATE,
    PERMISSIONS.REFERRAL_VIEW
  ]
}

// Check if user has permission
export const hasPermission = (userRole, permission) => {
  if (!userRole || !permission) return false
  const permissions = ROLE_PERMISSIONS[userRole] || []
  return permissions.includes(permission)
}

// Check if user has any of the given permissions
export const hasAnyPermission = (userRole, permissions) => {
  return permissions.some(permission => hasPermission(userRole, permission))
}

// Check if user has all of the given permissions
export const hasAllPermissions = (userRole, permissions) => {
  return permissions.every(permission => hasPermission(userRole, permission))
}

// Check if user can edit referral
export const canEditReferral = (userRole, userId, referral) => {
  // Admin can edit all
  if (userRole === ROLES.ADMIN) return true

  // Manager can edit if referral is not assigned or assigned to someone in their team
  if (userRole === ROLES.MANAGER) return true

  // Agent can only edit if assigned to them
  if (userRole === ROLES.AGENT && referral.assignedTo?.id === userId) {
    return true
  }

  // External users cannot edit
  return false
}

// Check if user can delete referral
export const canDeleteReferral = (userRole) => {
  return userRole === ROLES.ADMIN
}

// Check if user can assign referral
export const canAssignReferral = (userRole) => {
  return [ROLES.ADMIN, ROLES.MANAGER].includes(userRole)
}

// Check if user can approve/reject referral
export const canApproveReferral = (userRole, userId, referral) => {
  if (userRole === ROLES.ADMIN) return true
  if (userRole === ROLES.MANAGER) return true
  if (userRole === ROLES.AGENT && referral.assignedTo?.id === userId) return true
  return false
}

// Check if user can view all referrals
export const canViewAllReferrals = (userRole) => {
  return [ROLES.ADMIN, ROLES.MANAGER].includes(userRole)
}

// Check if user can view analytics
export const canViewAnalytics = (userRole) => {
  return [ROLES.ADMIN, ROLES.MANAGER, ROLES.AGENT].includes(userRole)
}

// Check if user can export data
export const canExportData = (userRole) => {
  return [ROLES.ADMIN, ROLES.MANAGER].includes(userRole)
}

// Get edit restrictions message
export const getEditRestrictionMessage = (userRole) => {
  switch (userRole) {
    case ROLES.ADMIN:
      return 'You have full edit access'
    case ROLES.MANAGER:
      return 'You can edit all referrals and notes'
    case ROLES.AGENT:
      return 'You can only edit referrals assigned to you and add notes'
    default:
      return 'View only - Contact admin for changes'
  }
}

// Hook for checking permissions in components
export const useAccessControl = (userRole) => {
  return {
    hasPermission: (permission) => hasPermission(userRole, permission),
    hasAnyPermission: (permissions) => hasAnyPermission(userRole, permissions),
    hasAllPermissions: (permissions) => hasAllPermissions(userRole, permissions),
    canEditReferral: (userId, referral) => canEditReferral(userRole, userId, referral),
    canDeleteReferral: () => canDeleteReferral(userRole),
    canAssignReferral: () => canAssignReferral(userRole),
    canApproveReferral: (userId, referral) => canApproveReferral(userRole, userId, referral),
    canViewAllReferrals: () => canViewAllReferrals(userRole),
    canViewAnalytics: () => canViewAnalytics(userRole),
    canExportData: () => canExportData(userRole),
    getEditRestrictionMessage: () => getEditRestrictionMessage(userRole)
  }
}

export default {
  ROLES,
  PERMISSIONS,
  ROLE_PERMISSIONS,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  canEditReferral,
  canDeleteReferral,
  canAssignReferral,
  canApproveReferral,
  canViewAllReferrals,
  canViewAnalytics,
  canExportData,
  getEditRestrictionMessage,
  useAccessControl
}
