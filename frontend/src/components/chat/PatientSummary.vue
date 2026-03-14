<template>
  <div class="patient-summary">
    <div class="summary-header">
      <h3>Resume du patient</h3>
      <button @click="refreshSummary" class="btn-refresh" :disabled="loading">
        {{ loading ? '...' : 'Actualiser' }}
      </button>
    </div>

    <div v-if="!summary" class="summary-empty">
      <p>Le resume se remplira au fur et a mesure de la conversation.</p>
    </div>

    <div v-else class="summary-content">
      <!-- Symptoms section -->
      <div class="summary-section" v-if="summary.symptoms && summary.symptoms.length">
        <h4>Symptomes rapportes</h4>
        <ul>
          <li v-for="(s, i) in summary.symptoms" :key="i" class="symptom-item">
            <span class="symptom-name">{{ s.name || s }}</span>
            <span v-if="s.severity" :class="['severity-badge', s.severity]">{{ s.severity }}</span>
          </li>
        </ul>
      </div>

      <!-- Medical history -->
      <div class="summary-section" v-if="summary.medical_history && summary.medical_history.length">
        <h4>Antecedents medicaux</h4>
        <ul>
          <li v-for="(h, i) in summary.medical_history" :key="i">{{ h.condition || h }}</li>
        </ul>
      </div>

      <!-- Current treatments -->
      <div class="summary-section" v-if="summary.current_treatments && summary.current_treatments.length">
        <h4>Traitements en cours</h4>
        <ul>
          <li v-for="(t, i) in summary.current_treatments" :key="i">
            {{ t.name || t }} <span v-if="t.dosage" class="dosage">- {{ t.dosage }}</span>
          </li>
        </ul>
      </div>

      <!-- Allergies -->
      <div class="summary-section" v-if="summary.allergies && summary.allergies.length">
        <h4>Allergies</h4>
        <div class="tags">
          <span v-for="(a, i) in summary.allergies" :key="i" class="tag allergy">{{ a }}</span>
        </div>
      </div>

      <!-- Clinical scores -->
      <div class="summary-section" v-if="summary.clinical_scores && Object.keys(summary.clinical_scores).length">
        <h4>Scores cliniques</h4>
        <div class="scores-grid">
          <div v-for="(val, key) in summary.clinical_scores" :key="key" class="score-item">
            <span class="score-name">{{ key }}</span>
            <span class="score-value">{{ val }}</span>
          </div>
        </div>
      </div>

      <!-- Free text summary -->
      <div class="summary-section" v-if="summary.text">
        <h4>Resume general</h4>
        <p class="summary-text">{{ summary.text }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '@/services/api'

const props = defineProps({
  conversationId: { type: String, default: null },
  messages: { type: Array, default: () => [] }
})

const summary = ref(null)
const loading = ref(false)

const refreshSummary = async () => {
  if (!props.conversationId || props.messages.length < 2) return

  loading.value = true
  try {
    const { data } = await api.post('/chat/summary', {
      conversation_id: props.conversationId
    })
    summary.value = data.summary || data
  } catch (err) {
    console.error('Failed to load summary:', err)
  } finally {
    loading.value = false
  }
}

// Auto-refresh when new messages arrive (every 2 assistant messages)
watch(() => props.messages.length, (newLen, oldLen) => {
  if (newLen > oldLen && newLen >= 4 && newLen % 2 === 0) {
    refreshSummary()
  }
})
</script>

<style scoped>
.patient-summary {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 1.5rem;
  height: 100%;
  overflow-y: auto;
  font-size: 0.95rem;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e8ecf1;
}

.summary-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #2c3e50;
  font-weight: 700;
}

.btn-refresh {
  padding: 0.35rem 0.85rem;
  background: #eef2ff;
  color: #4a5eb5;
  border: 1px solid #c7d2fe;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  background: #4a5eb5;
  color: #ffffff;
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.summary-empty {
  text-align: center;
  padding: 2rem 1rem;
  color: #8c9bab;
}

.summary-empty p {
  margin: 0;
  font-style: italic;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.summary-section {
  padding-left: 0.75rem;
  border-left: 3px solid #667eea;
}

.summary-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #4a5568;
  font-weight: 700;
}

.summary-section ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.summary-section ul li {
  padding: 0.3rem 0;
  color: #2d3748;
  line-height: 1.4;
}

.symptom-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.symptom-name {
  flex: 1;
}

.severity-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.severity-badge.leger,
.severity-badge.mild,
.severity-badge.low {
  background: #d4edda;
  color: #155724;
}

.severity-badge.modere,
.severity-badge.moderate,
.severity-badge.medium {
  background: #fff3cd;
  color: #856404;
}

.severity-badge.severe,
.severity-badge.high,
.severity-badge.critique {
  background: #f8d7da;
  color: #721c24;
}

.dosage {
  color: #718096;
  font-style: italic;
  font-size: 0.9em;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.tag {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.tag.allergy {
  background: #fde8e8;
  color: #c53030;
  border: 1px solid #feb2b2;
}

.scores-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.6rem;
  background: #f7fafc;
  border-radius: 6px;
}

.score-name {
  font-size: 0.85rem;
  color: #4a5568;
}

.score-value {
  font-weight: 700;
  color: #2d3748;
}

.summary-text {
  margin: 0;
  color: #2d3748;
  line-height: 1.6;
}

/* Alternate border colors for sections */
.summary-section:nth-child(2) {
  border-left-color: #48bb78;
}

.summary-section:nth-child(3) {
  border-left-color: #ed8936;
}

.summary-section:nth-child(4) {
  border-left-color: #e53e3e;
}

.summary-section:nth-child(5) {
  border-left-color: #9f7aea;
}

.summary-section:nth-child(6) {
  border-left-color: #38b2ac;
}

@media (max-width: 1024px) {
  .patient-summary {
    border-radius: 8px;
    padding: 1rem;
  }

  .scores-grid {
    grid-template-columns: 1fr;
  }
}
</style>
