import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useAdminStore = defineStore('admin', () => {
  // State
  const users = ref([])
  const conversations = ref([])
  const analytics = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Actions
  const fetchUsers = async (page = 1, limit = 20) => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.get('/admin/users', {
        params: { page, limit }
      })
      users.value = data.users
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchConversations = async (page = 1, limit = 20) => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.get('/admin/conversations', {
        params: { page, limit }
      })
      conversations.value = data.conversations
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAnalytics = async () => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.get('/admin/analytics')
      analytics.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteUser = async (userId) => {
    try {
      await api.delete(`/admin/users/${userId}`)
      users.value = users.value.filter(u => u.userId !== userId)
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors de la suppression'
      throw err
    }
  }

  const toggleUserStatus = async (userId, isActive) => {
    try {
      await api.patch(`/admin/users/${userId}`, { is_active: !isActive })
      const user = users.value.find(u => u.userId === userId)
      if (user) {
        user.is_active = !isActive
      }
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors de la modification'
      throw err
    }
  }

  return {
    // State
    users,
    conversations,
    analytics,
    loading,
    error,
    
    // Actions
    fetchUsers,
    fetchConversations,
    fetchAnalytics,
    deleteUser,
    toggleUserStatus
  }
})
