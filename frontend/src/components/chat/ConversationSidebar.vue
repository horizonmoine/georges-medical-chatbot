<template>
  <div class="conversation-sidebar" :class="{ collapsed: !expanded }">
    <div class="sidebar-header">
      <h3 v-if="expanded">Conversations</h3>
      <button @click="expanded = !expanded" class="btn-toggle">
        {{ expanded ? '&#x25C0;' : '&#x25B6;' }}
      </button>
    </div>

    <div v-if="expanded" class="sidebar-content">
      <button @click="$emit('new-conversation')" class="btn-new">
        + Nouvelle conversation
      </button>

      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.conversationId"
          :class="['conversation-item', { active: conv.conversationId === activeId }]"
          @click="$emit('select', conv.conversationId)"
        >
          <div class="conv-preview">
            <span class="conv-date">{{ formatDate(conv.created_at) }}</span>
            <span class="conv-messages">{{ conv.message_count || '0' }} messages</span>
          </div>
          <button @click.stop="$emit('delete', conv.conversationId)" class="btn-delete" title="Supprimer">
            &times;
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  activeId: { type: String, default: null }
})

defineEmits(['select', 'delete', 'new-conversation'])

const conversations = ref([])
const expanded = ref(true)

const loadConversations = async () => {
  try {
    const { data } = await api.get('/conversations')
    conversations.value = data.conversations || []
  } catch (err) {
    console.error('Failed to load conversations:', err)
  }
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}

onMounted(loadConversations)

defineExpose({ loadConversations })
</script>

<style scoped>
.conversation-sidebar {
  width: 280px;
  background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  transition: width 0.3s ease;
}

.conversation-sidebar.collapsed {
  width: 48px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  white-space: nowrap;
}

.btn-toggle {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #ffffff;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
  transition: background 0.2s;
}

.btn-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.btn-new {
  margin: 0.75rem;
  padding: 0.6rem 1rem;
  background: #667eea;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.btn-new:hover {
  background: #5a6fd6;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem;
}

.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  margin-bottom: 0.25rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.conversation-item.active {
  background: rgba(255, 255, 255, 0.15);
  border-left: 3px solid #667eea;
}

.conv-preview {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  overflow: hidden;
  flex: 1;
}

.conv-date {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-messages {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.btn-delete {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 1.3rem;
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
  flex-shrink: 0;
  transition: color 0.2s;
}

.btn-delete:hover {
  color: #e74c3c;
}

@media (max-width: 1024px) {
  .conversation-sidebar {
    width: 100%;
    height: auto;
    max-height: 200px;
  }

  .conversation-sidebar.collapsed {
    width: 100%;
    max-height: 48px;
  }
}
</style>
