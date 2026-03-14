<template>
  <div class="chatbot-layout">
    <!-- Left: Conversation sidebar -->
    <ConversationSidebar
      ref="sidebarRef"
      :active-id="conversationId"
      @select="selectConversation"
      @delete="deleteConversation"
      @new-conversation="startNewConversation"
    />

    <!-- Center: Chat area -->
    <div class="chat-center">
      <!-- Consent banner -->
      <ConsentBanner :project-name="projectName || 'Georges'" />

      <div class="chat-header">
        <div class="header-left">
          <button @click="goBack" class="btn-back">&#x2190; Retour</button>
          <h1>Assistant Medical HEGP</h1>
        </div>
        <div class="session-indicator">
          <span class="status-dot"></span>
          Session active (expire dans {{ sessionTime }})
        </div>
      </div>

      <div class="chat-messages" ref="messagesContainer">
        <div v-if="loading && messages.length === 0" class="loading-skeleton">
          <SkeletonLoader />
        </div>

        <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
          <div class="message-avatar">
            <span v-if="message.role === 'user'">&#x1F464;</span>
            <span v-else>&#x1F916;</span>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>

        <div v-if="aiTyping" class="message assistant typing">
          <div class="message-avatar">&#x1F916;</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-container">
        <div v-if="error" class="error-banner">
          {{ error }}
          <button @click="error = ''" class="btn-close">&#x2715;</button>
        </div>

        <form @submit.prevent="sendMessage" class="chat-input-form">
          <textarea
            v-model="currentMessage"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="Decrivez vos symptomes ou posez une question medicale..."
            rows="3"
            :disabled="loading"
            ref="inputField"
          ></textarea>
          <button type="submit" class="btn-send" :disabled="loading || !currentMessage.trim()">
            <span v-if="!loading">Envoyer &#x27A4;</span>
            <span v-else>...</span>
          </button>
        </form>

        <div class="chat-disclaimer">
          <span class="icon">&#x26A0;&#xFE0F;</span>
          <p>
            Cet assistant fournit des informations generales et ne remplace pas un avis medical
            professionnel. Consultez un medecin pour un diagnostic.
          </p>
        </div>
      </div>
    </div>

    <!-- Right: Patient summary -->
    <div class="chat-right">
      <PatientSummary
        :conversation-id="conversationId"
        :messages="messages"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import { resetSessionTimer } from '@/services/sessionMonitor'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ConversationSidebar from '@/components/chat/ConversationSidebar.vue'
import ConsentBanner from '@/components/chat/ConsentBanner.vue'
import PatientSummary from '@/components/chat/PatientSummary.vue'

const props = defineProps({
  projectSlug: { type: String, default: null },
  projectName: { type: String, default: null }
})

const router = useRouter()
const route = useRoute()

const messages = ref([])
const currentMessage = ref('')
const conversationId = ref(null)
const loading = ref(false)
const aiTyping = ref(false)
const error = ref('')
const messagesContainer = ref(null)
const inputField = ref(null)
const sessionTime = ref('5:00')
const sidebarRef = ref(null)

let sessionInterval = null

onMounted(async () => {
  // Charger la conversation si ID dans l'URL
  if (route.params.conversationId) {
    conversationId.value = route.params.conversationId
    await loadConversation()
  } else {
    // Message de bienvenue
    messages.value.push({
      role: 'assistant',
      content: 'Bonjour ! Je suis votre assistant medical. Comment puis-je vous aider aujourd\'hui ?',
      timestamp: new Date()
    })
  }

  // Demarrer le compteur de session
  startSessionTimer()

  // Focus sur l'input
  inputField.value?.focus()
})

onUnmounted(() => {
  if (sessionInterval) {
    clearInterval(sessionInterval)
  }
})

const startSessionTimer = () => {
  let seconds = 300 // 5 minutes

  sessionInterval = setInterval(() => {
    seconds--
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    sessionTime.value = `${mins}:${secs.toString().padStart(2, '0')}`

    if (seconds <= 0) {
      clearInterval(sessionInterval)
      alert('Votre session a expire.')
      localStorage.clear()
      router.push('/login')
    }
  }, 1000)
}

const loadConversation = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/conversations/${conversationId.value}`)
    messages.value = data.conversation.messages.map(msg => ({
      ...msg,
      timestamp: new Date(msg.timestamp)
    }))
    scrollToBottom()
  } catch (err) {
    error.value = 'Erreur lors du chargement de la conversation'
  } finally {
    loading.value = false
  }
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || loading.value) return

  const userMessage = {
    role: 'user',
    content: currentMessage.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const messageToSend = currentMessage.value
  currentMessage.value = ''

  await nextTick()
  scrollToBottom()

  // Reinitialiser le timer de session
  resetSessionTimer(() => {
    alert('Session expiree')
    localStorage.clear()
    router.push('/login')
  })

  // Afficher l'indicateur de frappe
  aiTyping.value = true
  loading.value = true

  try {
    const payload = {
      conversation_id: conversationId.value,
      message: messageToSend
    }
    if (props.projectSlug) {
      payload.project_slug = props.projectSlug
    }

    const { data } = await api.post('/chat', payload)

    conversationId.value = data.conversation_id

    const aiMessage = {
      role: 'assistant',
      content: data.response,
      timestamp: new Date()
    }

    messages.value.push(aiMessage)

    await nextTick()
    scrollToBottom()

    // Refresh sidebar to update conversation list
    sidebarRef.value?.loadConversations()
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur lors de l\'envoi du message'
  } finally {
    aiTyping.value = false
    loading.value = false
  }
}

const selectConversation = async (id) => {
  conversationId.value = id
  messages.value = []
  await loadConversation()
}

const deleteConversation = async (id) => {
  try {
    await api.delete(`/conversations/${id}`)
    if (conversationId.value === id) {
      startNewConversation()
    }
    sidebarRef.value?.loadConversations()
  } catch (err) {
    error.value = 'Erreur lors de la suppression'
  }
}

const startNewConversation = () => {
  conversationId.value = null
  messages.value = [{
    role: 'assistant',
    content: 'Bonjour ! Je suis votre assistant medical. Comment puis-je vous aider aujourd\'hui ?',
    timestamp: new Date()
  }]
  inputField.value?.focus()
}

const formatMessage = (text) => {
  return text.replace(/\n/g, '<br>')
}

const formatTime = (date) => {
  return new Date(date).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const goBack = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.chatbot-layout {
  display: grid;
  grid-template-columns: auto 1fr 380px;
  height: 100vh;
  background: #f5f7fa;
}

.chat-center {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  min-width: 0;
}

.chat-right {
  padding: 1rem;
  overflow-y: auto;
  border-left: 1px solid #e0e0e0;
  background: #fafbfc;
}

.chat-header {
  background: white;
  padding: 1rem 2rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h1 {
  font-size: 1.25rem;
  margin: 0;
  color: #2c3e50;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.session-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #4caf50;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message {
  display: flex;
  gap: 1rem;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 2rem;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 50%;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 0.5rem;
}

.typing-indicator {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

.chat-input-container {
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 1.5rem 2rem;
  flex-shrink: 0;
}

.error-banner {
  background: #fee;
  color: #c33;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #c33;
}

.chat-input-form {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

textarea {
  flex: 1;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  transition: border-color 0.3s;
}

textarea:focus {
  outline: none;
  border-color: #667eea;
}

.btn-send {
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-send:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-disclaimer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: #fff3cd;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #856404;
}

.chat-disclaimer .icon {
  font-size: 1.25rem;
}

/* Tablet and below: stacked layout */
@media (max-width: 1024px) {
  .chatbot-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }

  .chat-right {
    border-left: none;
    border-top: 1px solid #e0e0e0;
    max-height: 300px;
  }
}

@media (max-width: 768px) {
  .chat-messages {
    padding: 1rem;
  }

  .message-content {
    max-width: 85%;
  }

  .chat-input-form {
    flex-direction: column;
  }

  .chat-right {
    display: none;
  }

  .header-left h1 {
    font-size: 1rem;
  }
}
</style>
