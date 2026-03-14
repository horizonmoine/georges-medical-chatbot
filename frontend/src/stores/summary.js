import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useSummaryStore = defineStore('summary', () => {
  // State
  const summary = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Actions
  const fetchSummary = async (conversationId) => {
    if (!conversationId) return

    loading.value = true
    error.value = null

    try {
      const { data } = await api.post('/chat/summary', {
        conversation_id: conversationId
      })
      summary.value = data.summary || data
      return summary.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement du resume'
      console.error('Failed to fetch summary:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearSummary = () => {
    summary.value = null
    error.value = null
  }

  return {
    // State
    summary,
    loading,
    error,

    // Actions
    fetchSummary,
    clearSummary
  }
})
