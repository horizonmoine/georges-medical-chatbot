<template>
  <div class="dashboard-container">
    <nav class="dashboard-nav">
      <div class="nav-content">
        <div class="logo">
          <img src="/assets/HEGP_LOGO.jpg" alt="HEGP" />
          <span>HEGP Medical</span>
        </div>
        <div class="nav-menu">
          <router-link to="/dashboard" class="nav-item active">📊 Tableau de bord</router-link>
          <router-link to="/chat" class="nav-item">💬 Chat</router-link>
          <router-link to="/profile" class="nav-item">👤 Profil</router-link>
          <router-link to="/consents" class="nav-item">🔒 RGPD</router-link>
          <button @click="handleLogout" class="btn-logout">Déconnexion</button>
        </div>
      </div>
    </nav>

    <div class="dashboard-content">
      <div class="welcome-section">
        <h1>Bienvenue, {{ user.prenom }} {{ user.nom }} 👋</h1>
        <p>Accédez à votre assistant médical et gérez vos conversations</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">💬</div>
          <div class="stat-info">
            <h3>{{ stats.totalConversations }}</h3>
            <p>Conversations</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-info">
            <h3>{{ stats.totalMessages }}</h3>
            <p>Messages envoyés</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div class="stat-info">
            <h3>{{ stats.lastActivity }}</h3>
            <p>Dernière activité</p>
          </div>
        </div>
      </div>

      <div class="actions-section">
        <div class="action-card primary">
          <h2>🤖 Démarrer une nouvelle conversation</h2>
          <p>Posez vos questions médicales à l'assistant intelligent</p>
          <router-link to="/chat" class="btn-action">Commencer →</router-link>
        </div>

        <div class="action-card">
          <h2>📋 Mes conversations récentes</h2>
          <div v-if="loading" class="loading">
            <SkeletonLoader />
          </div>
          <div v-else-if="conversations.length === 0" class="empty-state">
            Aucune conversation pour le moment
          </div>
          <div v-else class="conversations-list">
            <div
              v-for="conv in conversations"
              :key="conv.conversationId"
              class="conversation-item"
              @click="openConversation(conv.conversationId)"
            >
              <div class="conv-header">
                <span class="conv-date">{{ formatDate(conv.created_at) }}</span>
                <span class="conv-messages">{{ conv.message_count }} messages</span>
              </div>
              <div class="conv-preview">
                {{ conv.lastMessage || 'Conversation vide' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="info-cards">
        <div class="info-card">
          <h3>🔒 Confidentialité</h3>
          <p>Vos données sont chiffrées et conformes au RGPD</p>
          <router-link to="/consents">Gérer mes consentements →</router-link>
        </div>

        <div class="info-card">
          <h3>📥 Export de données</h3>
          <p>Téléchargez toutes vos données personnelles</p>
          <button @click="exportData" class="btn-link">Exporter →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

const router = useRouter()

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const conversations = ref([])
const stats = ref({
  totalConversations: 0,
  totalMessages: 0,
  lastActivity: 'Aujourd\'hui'
})
const loading = ref(false)

onMounted(async () => {
  await loadConversations()
})

const loadConversations = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/conversations?limit=5')
    conversations.value = data.conversations
    
    stats.value.totalConversations = data.total
    stats.value.totalMessages = data.conversations.reduce(
      (sum, conv) => sum + (conv.message_count || 0), 0
    )
  } catch (error) {
    console.error('Error loading conversations:', error)
  } finally {
    loading.value = false
  }
}

const openConversation = (conversationId) => {
  router.push(`/chat/${conversationId}`)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Aujourd\'hui'
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `Il y a ${diffDays} jours`
  
  return date.toLocaleDateString('fr-FR')
}

const exportData = async () => {
  try {
    const { data } = await api.get('/user/data-export')
    
    // Créer un fichier JSON téléchargeable
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `hegp-data-export-${new Date().toISOString()}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    
    alert('Vos données ont été exportées avec succès !')
  } catch (error) {
    alert('Erreur lors de l\'export des données')
  }
}

const handleLogout = async () => {
  try {
    await api.post('/logout')
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    localStorage.clear()
    router.push('/login')
  }
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.dashboard-nav {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.nav-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.25rem;
  font-weight: bold;
  color: #333;
}

.logo img {
  height: 40px;
  border-radius: 8px;
}

.nav-menu {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.nav-item {
  padding: 0.5rem 1rem;
  text-decoration: none;
  color: #666;
  border-radius: 6px;
  transition: all 0.3s;
}

.nav-item:hover, .nav-item.active {
  background: #f0f0f0;
  color: #333;
}

.btn-logout {
  padding: 0.5rem 1rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.welcome-section {
  margin-bottom: 2rem;
}

.welcome-section h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.welcome-section p {
  font-size: 1.1rem;
  color: #666;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.stat-icon {
  font-size: 3rem;
}

.stat-info h3 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
  color: #333;
}

.stat-info p {
  color: #666;
  font-size: 0.9rem;
}

.actions-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.action-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.action-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-card h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.btn-action {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: white;
  color: #667eea;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn-action:hover {
  transform: translateY(-2px);
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.conversation-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.conversation-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
}

.conv-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: #666;
}

.conv-preview {
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.info-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.info-card h3 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.info-card p {
  color: #666;
  margin-bottom: 1rem;
}

.info-card a, .btn-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #999;
}

@media (max-width: 768px) {
  .actions-section {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
