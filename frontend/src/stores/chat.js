import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useChatStore = defineStore('chat', () => {
  // State
  const conversations = ref([])
  const currentConversation = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const sending = ref(false)
  const error = ref(null)

  // Actions
  const fetchConversations = async () => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.get('/conversations')
      conversations.value = data.conversations
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement'
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadConversation = async (conversationId) => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.get(`/conversations/${conversationId}`)
      currentConversation.value = data
      messages.value = data.messages || []
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement'
      throw err
    } finally {
      loading.value = false
    }
  }

  const sendMessage = async (message, conversationId = null) => {
    sending.value = true
    error.value = null
    
    try {
      const { data } = await api.post('/chat', {
        message,
        conversationId
      })
      
      // Ajouter les messages à la conversation actuelle
      messages.value.push(data.userMessage)
      messages.value.push(data.botResponse)
      
      // Mettre à jour l'ID de conversation
      if (!currentConversation.value) {
        currentConversation.value = { conversationId: data.conversationId }
      }
      
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors de l\'envoi'
      throw err
    } finally {
      sending.value = false
    }
  }

  const startNewConversation = () => {
    currentConversation.value = null
    messages.value = []
  }

  const deleteConversation = async (conversationId) => {
    try {
      await api.delete(`/conversations/${conversationId}`)
      conversations.value = conversations.value.filter(
        c => c.conversationId !== conversationId
      )
      
      if (currentConversation.value?.conversationId === conversationId) {
        startNewConversation()
      }
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors de la suppression'
      throw err
    }
  }

  return {
    // State
    conversations,
    currentConversation,
    messages,
    loading,
    sending,
    error,
    
    // Actions
    fetchConversations,
    loadConversation,
    sendMessage,
    startNewConversation,
    deleteConversation
  }
})
