/**
 * Application constants
 */

export const ROLES = {
  PATIENT: 'patient',
  MEDECIN: 'medecin',
  ADMIN: 'admin'
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
