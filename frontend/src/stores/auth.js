import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ROLE_LEVELS } from '@/utils/constants'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || null)
  const roleLevel = computed(() => ROLE_LEVELS[userRole.value] || 0)

  // Rôles par niveau (spec: niv1-niv99)
  const isMedecin = computed(() => roleLevel.value >= 2)   // niv2+
  const isTester = computed(() => roleLevel.value >= 3)    // niv3+
  const isAdmin = computed(() => ['admin', 'super_admin'].includes(userRole.value))
  const isSuperAdmin = computed(() => userRole.value === 'super_admin') // niv99

  // Actions
  const setTokens = (accessToken, refreshTokenValue) => {
    token.value = accessToken
    refreshToken.value = refreshTokenValue
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshTokenValue)
  }

  const setUser = (userData) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const clearAuth = () => {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  const updateUser = (updates) => {
    if (user.value) {
      user.value = { ...user.value, ...updates }
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  return {
    // State
    token,
    refreshToken,
    user,

    // Getters
    isAuthenticated,
    userRole,
    roleLevel,
    isMedecin,
    isTester,
    isAdmin,
    isSuperAdmin,
    
    // Actions
    setTokens,
    setUser,
    clearAuth,
    updateUser
  }
})
