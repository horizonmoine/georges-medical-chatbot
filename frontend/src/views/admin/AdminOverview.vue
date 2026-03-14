<template>
  <div class="admin-overview">
    <h1>📊 Vue d'ensemble</h1>
    <p class="subtitle">Statistiques générales de la plateforme HEGP</p>

    <div v-if="loading" class="loading">
      <SkeletonLoader />
    </div>

    <div v-else class="overview-content">
      <div class="stats-grid">
        <div class="stat-card users">
          <div class="stat-icon">👥</div>
          <div class="stat-info">
            <h3>{{ stats.total_users }}</h3>
            <p>Utilisateurs</p>
            <span class="stat-change positive">+{{ stats.new_users_today }} aujourd'hui</span>
          </div>
        </div>

        <div class="stat-card conversations">
          <div class="stat-icon">💬</div>
          <div class="stat-info">
            <h3>{{ stats.total_conversations }}</h3>
            <p>Conversations</p>
            <span class="stat-change positive">+{{ stats.conversations_today }} aujourd'hui</span>
          </div>
        </div>

        <div class="stat-card messages">
          <div class="stat-icon">📝</div>
          <div class="stat-info">
            <h3>{{ stats.total_messages }}</h3>
            <p>Messages</p>
            <span class="stat-change">{{ stats.avg_messages_per_conv }} moy/conv</span>
          </div>
        </div>

        <div class="stat-card active">
          <div class="stat-icon">⚡</div>
          <div class="stat-info">
            <h3>{{ stats.active_users }}</h3>
            <p>Utilisateurs actifs</p>
            <span class="stat-change">Dernières 24h</span>
          </div>
        </div>
      </div>

      <div class="charts-section">
        <div class="chart-card">
          <h3>Activité des 7 derniers jours</h3>
          <AnalyticsBarChart :data="activityData" />
        </div>

        <div class="chart-card">
          <h3>Répartition des utilisateurs</h3>
          <AnalyticsDoughnutChart :data="userDistribution" />
        </div>
      </div>

      <div class="recent-section">
        <div class="recent-card">
          <h3>Utilisateurs récents</h3>
          <div class="recent-list">
            <div v-for="user in recentUsers" :key="user.userId" class="recent-item">
              <div class="user-avatar">{{ user.prenom[0] }}{{ user.nom[0] }}</div>
              <div class="user-info">
                <p class="user-name">{{ user.prenom }} {{ user.nom }}</p>
                <p class="user-email">{{ user.email }}</p>
              </div>
              <span class="user-date">{{ formatDate(user.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="recent-card">
          <h3>Dernières conversations</h3>
          <div class="recent-list">
            <div v-for="conv in recentConversations" :key="conv.conversationId" class="recent-item">
              <span class="conv-icon">💬</span>
              <div class="conv-info">
                <p class="conv-user">User ID: {{ conv.userId.substring(0, 8) }}...</p>
                <p class="conv-messages">{{ conv.message_count }} messages</p>
              </div>
              <span class="conv-date">{{ formatDate(conv.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="system-status">
        <h3>État du système</h3>
        <div class="status-grid">
          <div class="status-item">
            <span class="status-indicator online"></span>
            <span>Elasticsearch</span>
            <span class="status-value">En ligne</span>
          </div>
          <div class="status-item">
            <span class="status-indicator online"></span>
            <span>Gemini AI</span>
            <span class="status-value">Opérationnel</span>
          </div>
          <div class="status-item">
            <span class="status-indicator online"></span>
            <span>Email Service</span>
            <span class="status-value">Actif</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import AnalyticsBarChart from '@/components/analytics/AnalyticsBarChart.vue'
import AnalyticsDoughnutChart from '@/components/analytics/AnalyticsDoughnutChart.vue'

const loading = ref(false)
const stats = ref({
  total_users: 0,
  new_users_today: 0,
  total_conversations: 0,
  conversations_today: 0,
  total_messages: 0,
  avg_messages_per_conv: 0,
  active_users: 0
})

const activityData = ref({
  labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
  datasets: [{
    label: 'Messages',
    data: [65, 59, 80, 81, 56, 55, 40],
    backgroundColor: 'rgba(102, 126, 234, 0.5)'
  }]
})

const userDistribution = ref({
  labels: ['Patients', 'Médecins', 'Admins'],
  datasets: [{
    data: [85, 12, 3],
    backgroundColor: ['#667eea', '#764ba2', '#f093fb']
  }]
})

const recentUsers = ref([])
const recentConversations = ref([])

onMounted(async () => {
  await loadOverviewData()
})

const loadOverviewData = async () => {
  loading.value = true
  try {
    const [analyticsRes, usersRes, convsRes] = await Promise.all([
      api.get('/admin/analytics'),
      api.get('/admin/users?limit=5'),
      api.get('/admin/conversations?limit=5')
    ])

    stats.value = {
      total_users: analyticsRes.data.total_users || 0,
      new_users_today: analyticsRes.data.new_users_today || 0,
      total_conversations: analyticsRes.data.total_conversations || 0,
      conversations_today: analyticsRes.data.conversations_today || 0,
      total_messages: analyticsRes.data.total_messages || 0,
      avg_messages_per_conv: Math.round(analyticsRes.data.avg_messages_per_conversation || 0),
      active_users: analyticsRes.data.active_users_24h || 0
    }

    recentUsers.value = usersRes.data.users
    recentConversations.value = convsRes.data.conversations
  } catch (error) {
    console.error('Error loading overview:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Aujourd\'hui'
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `Il y a ${diffDays}j`
  
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
}
</script>

<style scoped>
.admin-overview {
  max-width: 1400px;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.subtitle {
  color: #7f8c8d;
  margin-bottom: 2rem;
  font-size: 1.1rem;
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
  border-left: 4px solid;
}

.stat-card.users { border-left-color: #3498db; }
.stat-card.conversations { border-left-color: #9b59b6; }
.stat-card.messages { border-left-color: #e67e22; }
.stat-card.active { border-left-color: #2ecc71; }

.stat-icon {
  font-size: 3rem;
}

.stat-info h3 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
  color: #2c3e50;
}

.stat-info p {
  color: #7f8c8d;
  margin-bottom: 0.5rem;
}

.stat-change {
  font-size: 0.85rem;
  color: #95a5a6;
}

.stat-change.positive {
  color: #27ae60;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.chart-card h3 {
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.recent-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.recent-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.recent-card h3 {
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.user-avatar {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.1rem;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.user-date, .conv-date {
  font-size: 0.85rem;
  color: #95a5a6;
}

.conv-icon {
  font-size: 2rem;
}

.conv-info {
  flex: 1;
}

.conv-user {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.conv-messages {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.system-status {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.system-status h3 {
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-indicator.online {
  background: #27ae60;
}

.status-value {
  margin-left: auto;
  font-weight: 600;
  color: #27ae60;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
