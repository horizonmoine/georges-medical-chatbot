<template>
  <div class="admin-conversations">
    <h1>💬 Conversations</h1>
    <p class="subtitle">Toutes les conversations de la plateforme</p>

    <div class="filters-section">
      <input
        v-model="searchQuery"
        @input="handleSearch"
        type="text"
        placeholder="Rechercher par ID utilisateur..."
        class="search-input"
      />
      <select v-model="sortBy" @change="handleSort" class="sort-select">
        <option value="recent">Plus récentes</option>
        <option value="oldest">Plus anciennes</option>
        <option value="messages">Plus de messages</option>
      </select>
    </div>

    <div v-if="loading" class="loading">
      <SkeletonLoader />
    </div>

    <div v-else class="conversations-grid">
      <div
        v-for="conv in conversations"
        :key="conv.conversationId"
        class="conversation-card"
        @click="viewConversation(conv.conversationId)"
      >
        <div class="card-header">
          <span class="conv-icon">💬</span>
          <span class="conv-date">{{ formatDate(conv.created_at) }}</span>
        </div>
        <div class="card-body">
          <p class="conv-user">User: {{ conv.userId.substring(0, 12) }}...</p>
          <p class="conv-messages">{{ conv.message_count }} messages</p>
          <p class="conv-preview">{{ conv.lastMessage || 'Aucun message' }}</p>
        </div>
        <div class="card-footer">
          <button class="btn-view">Voir détails →</button>
        </div>
      </div>
    </div>

    <Pagination
      :current-page="currentPage"
      :total-pages="totalPages"
      @page-change="handlePageChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import Pagination from '@/components/common/Pagination.vue'

const router = useRouter()

const conversations = ref([])
const loading = ref(false)
const searchQuery = ref('')
const sortBy = ref('recent')
const currentPage = ref(1)
const totalPages = ref(1)

onMounted(async () => {
  await loadConversations()
})

const loadConversations = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: 12,
      search: searchQuery.value,
      sort: sortBy.value
    }

    const { data } = await api.get('/admin/conversations', { params })
    conversations.value = data.conversations
    totalPages.value = Math.ceil(data.total / 12)
  } catch (error) {
    console.error('Error loading conversations:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadConversations()
}

const handleSort = () => {
  loadConversations()
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadConversations()
}

const viewConversation = (conversationId) => {
  router.push(`/admin/conversations/${conversationId}`)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('fr-FR')
}
</script>

<style scoped>
.admin-conversations {
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
}

.filters-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.search-input, .sort-select {
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

.search-input {
  flex: 1;
}

.conversations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.conversation-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s;
}

.conversation-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.conv-icon {
  font-size: 2rem;
}

.conv-date {
  font-size: 0.85rem;
  color: #95a5a6;
}

.card-body {
  padding: 1.5rem;
}

.conv-user {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-family: monospace;
}

.conv-messages {
  color: #7f8c8d;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.conv-preview {
  color: #95a5a6;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #f0f0f0;
}

.btn-view {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
</style>
