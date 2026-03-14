import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isMedecin = computed(() => user.value?.role === 'medecin')
  const fullName = computed(() => {
    if (!user.value) return ''
    return `${user.value.prenom} ${user.value.nom}`
  })
  const initials = computed(() => {
    if (!user.value) return ''
    return `${user.value.prenom[0]}${user.value.nom[0]}`.toUpperCase()
  })

  // Actions
  const loadUser = async () => {
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('access_token')
    
    if (storedUser && token) {
      user.value = JSON.parse(storedUser)
      isAuthenticated.value = true
    }
  }

  const login = async (credentials) => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.post('/login', credentials)
      
      user.value = data.user
      isAuthenticated.value = true
      
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      
      return data.user
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de connexion'
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await api.post('/logout')
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      user.value = null
      isAuthenticated.value = false
      localStorage.clear()
    }
  }

  const updateProfile = async (profileData) => {
    loading.value = true
    error.value = null
    
    try {
      await api.put('/user/profile', profileData)
      
      user.value = { ...user.value, ...profileData }
      localStorage.setItem('user', JSON.stringify(user.value))
      
      return user.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de mise à jour'
      throw err
    } finally {
      loading.value = false
    }
  }

  const refreshUser = async () => {
    try {
      const { data } = await api.get('/user/profile')
      user.value = data.user
      localStorage.setItem('user', JSON.stringify(data.user))
    } catch (err) {
      console.error('Error refreshing user:', err)
    }
  }

  return {
    // State
    user,
    isAuthenticated,
    loading,
    error,
    
    // Getters
    isAdmin,
    isMedecin,
    fullName,
    initials,
    
    // Actions
    loadUser,
    login,
    logout,
    updateProfile,
    refreshUser
  }
})
