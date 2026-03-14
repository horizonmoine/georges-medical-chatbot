import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isMedecin = computed(() => user.value?.role === 'medecin')
  const userRole = computed(() => user.value?.role || null)

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
    isAdmin,
    isMedecin,
    userRole,
    
    // Actions
    setTokens,
    setUser,
    clearAuth,
    updateUser
  }
})
