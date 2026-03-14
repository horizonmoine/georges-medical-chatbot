<template>
  <div class="project-chat">
    <!-- Loading state -->
    <div v-if="loading" class="project-loading">
      <div class="spinner"></div>
      <p>Chargement du projet...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="project-error">
      <h2>Erreur</h2>
      <p>{{ error }}</p>
      <router-link to="/dashboard" class="btn-back">Retour au tableau de bord</router-link>
    </div>

    <!-- Consent gate -->
    <div v-else-if="project && !hasConsented" class="consent-gate">
      <div class="consent-card">
        <h2>Consentement requis</h2>
        <p class="project-name">Projet : <strong>{{ project.name }}</strong></p>

        <div class="consent-description">
          <p>{{ project.description || 'Ce projet necessite votre consentement avant de pouvoir utiliser le chatbot medical.' }}</p>
        </div>

        <div class="consent-details" v-if="project.consent_text">
          <h4>Conditions de participation</h4>
          <div class="consent-text" v-html="project.consent_text"></div>
        </div>

        <div class="consent-actions">
          <label class="consent-checkbox">
            <input type="checkbox" v-model="consentAccepted" />
            <span>J'ai lu et j'accepte les conditions de participation a ce projet.</span>
          </label>

          <div class="btn-group">
            <router-link to="/dashboard" class="btn btn-secondary">Annuler</router-link>
            <button
              @click="submitConsent"
              class="btn btn-primary"
              :disabled="!consentAccepted || submitting"
            >
              {{ submitting ? 'Envoi...' : 'Donner mon consentement' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat view (consented) -->
    <div v-else-if="project && hasConsented" class="project-chat-active">
      <ChatBot :project-slug="projectSlug" :project-name="project.name" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import ChatBot from '@/views/ChatBot.vue'

const route = useRoute()
const router = useRouter()

const projectSlug = computed(() => route.params.projectSlug)

const project = ref(null)
const loading = ref(true)
const error = ref('')
const hasConsented = ref(false)
const consentAccepted = ref(false)
const submitting = ref(false)

const loadProject = async () => {
  loading.value = true
  error.value = ''

  try {
    const { data } = await api.get(`/projects/${projectSlug.value}`)
    project.value = data.project || data
    hasConsented.value = !!project.value.user_consented
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'Ce projet n\'existe pas.'
    } else {
      error.value = err.response?.data?.error || 'Impossible de charger le projet.'
    }
  } finally {
    loading.value = false
  }
}

const submitConsent = async () => {
  if (!consentAccepted.value || !project.value) return

  submitting.value = true
  try {
    await api.post(`/projects/${project.value._id || project.value.id}/consent`)
    hasConsented.value = true
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur lors de l\'enregistrement du consentement.'
  } finally {
    submitting.value = false
  }
}

onMounted(loadProject)
</script>

<style scoped>
.project-chat {
  min-height: 100vh;
  background: #f5f7fa;
}

.project-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 1rem;
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.project-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 2rem;
}

.project-error h2 {
  color: #e74c3c;
  margin-bottom: 0.5rem;
}

.project-error p {
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.btn-back {
  padding: 0.75rem 2rem;
  background: #667eea;
  color: #ffffff;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
}

.consent-gate {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
}

.consent-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  padding: 2.5rem;
  max-width: 640px;
  width: 100%;
}

.consent-card h2 {
  margin: 0 0 0.5rem;
  color: #2c3e50;
}

.project-name {
  color: #667eea;
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
}

.consent-description {
  margin-bottom: 1.5rem;
  color: #4a5568;
  line-height: 1.6;
}

.consent-details {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.consent-details h4 {
  margin: 0 0 0.75rem;
  color: #2c3e50;
}

.consent-text {
  color: #4a5568;
  line-height: 1.6;
  font-size: 0.95rem;
  max-height: 300px;
  overflow-y: auto;
}

.consent-actions {
  margin-top: 1.5rem;
}

.consent-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: #2c3e50;
}

.consent-checkbox input[type="checkbox"] {
  margin-top: 0.2rem;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.btn-group {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  text-decoration: none;
  transition: transform 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e9ecef;
  color: #495057;
}

.btn-secondary:hover {
  background: #dee2e6;
}

.project-chat-active {
  height: 100vh;
}
</style>
