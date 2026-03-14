<template>
  <div class="pagination" v-if="totalPages > 1">
    <button
      @click="goToPage(1)"
      :disabled="currentPage === 1"
      class="pagination-btn"
    >
      ⏮️
    </button>

    <button
      @click="goToPage(currentPage - 1)"
      :disabled="currentPage === 1"
      class="pagination-btn"
    >
      ◀️
    </button>

    <div class="pagination-pages">
      <button
        v-for="page in visiblePages"
        :key="page"
        @click="goToPage(page)"
        :class="['pagination-page', { active: page === currentPage }]"
      >
        {{ page }}
      </button>
    </div>

    <button
      @click="goToPage(currentPage + 1)"
      :disabled="currentPage === totalPages"
      class="pagination-btn"
    >
      ▶️
    </button>

    <button
      @click="goToPage(totalPages)"
      :disabled="currentPage === totalPages"
      class="pagination-btn"
    >
      ⏭️
    </button>

    <div class="pagination-info">
      Page {{ currentPage }} / {{ totalPages }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: {
    type: Number,
    required: true
  },
  totalPages: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['page-change'])

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, props.currentPage - Math.floor(maxVisible / 2))
  let end = Math.min(props.totalPages, start + maxVisible - 1)

  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

const goToPage = (page) => {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    emit('page-change', page)
  }
}
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem 0;
  flex-wrap: wrap;
}

.pagination-btn, .pagination-page {
  padding: 0.5rem 0.75rem;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
}

.pagination-btn:hover:not(:disabled), .pagination-page:hover {
  background: #f0f0f0;
  border-color: #667eea;
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination-pages {
  display: flex;
  gap: 0.25rem;
}

.pagination-page.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.pagination-info {
  margin-left: 1rem;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #666;
}

@media (max-width: 600px) {
  .pagination {
    font-size: 0.85rem;
  }

  .pagination-btn, .pagination-page {
    padding: 0.4rem 0.6rem;
  }
}
</style>
