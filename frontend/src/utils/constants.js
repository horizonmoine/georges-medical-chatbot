/**
 * Application constants
 */

// Niveaux de rôles définis dans la spec
// niv1: utilisateur/patient, niv2: médecin investigateur,
// niv3: testeur ou admin projet, niv99: super administrateur
export const ROLES = {
  USER: 'user',           // niv1
  MEDECIN: 'medecin',    // niv2
  TESTER: 'tester',      // niv3
  ADMIN: 'admin',        // niv3 - admin projet (détient la clé de chiffrement)
  SUPER_ADMIN: 'super_admin' // niv99
}

export const ROLE_LEVELS = {
  user: 1,
  medecin: 2,
  tester: 3,
  admin: 3,
  super_admin: 99
}

// Retourne true si le rôle a au moins le niveau requis
export const hasRoleLevel = (userRole, minLevel) => {
  return (ROLE_LEVELS[userRole] || 0) >= minLevel
}

export const SESSION_TIMEOUT = 5 * 60 * 1000 // 5 minutes

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/login',
    SIGNUP: '/signup',
    LOGOUT: '/logout',
    REFRESH: '/refresh'
  },
  USER: {
    PROFILE: '/user/profile',
    CONSENTS: '/user/consents',
    DATA_EXPORT: '/user/data-export',
    DELETE_ACCOUNT: '/user/delete-account'
  },
  CHAT: {
    SEND: '/chat',
    CONVERSATIONS: '/conversations'
  },
  ADMIN: {
    USERS: '/admin/users',
    CONVERSATIONS: '/admin/conversations',
    ANALYTICS: '/admin/analytics'
  }
}

export const CONSENT_TYPES = {
  DATA_PROCESSING: 'data_processing',
  RESEARCH: 'research',
  EMAIL: 'email'
}

export const MESSAGE_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
}

export const PAGINATION = {
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100
}
