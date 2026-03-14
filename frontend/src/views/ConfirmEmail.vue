<template>
  <div class="confirm-email">
    <div class="confirm-card">
      <!-- Loading -->
      <div v-if="loading" class="confirm-loading">
        <div class="spinner"></div>
        <p>Verification en cours...</p>
      </div>

      <!-- Success -->
      <div v-else-if="success" class="confirm-success">
        <div class="icon-circle success">&#x2713;</div>
        <h2>Email confirme</h2>
        <p>Votre adresse email a ete verifiee avec succes. Vous pouvez maintenant vous connecter.</p>
        <router-link to="/login" class="btn btn-primary">Se connecter</router-link>
      </div>

      <!-- Error -->
      <div v-else class="confirm-error">
        <div class="icon-circle error">&#x2717;</div>
        <h2>Erreur de confirmation</h2>
        <p>{{ errorMessage }}</p>
        <div class="btn-group">
          <router-link to="/" class="btn btn-secondary">Retour a l'accueil</router-link>
          <router-link to="/login" class="btn btn-primary">Se connecter</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()

const loading = ref(true)
const success = ref(false)
const errorMessage = ref('')

const confirmEmail = async () => {
  const token = route.params.token
  if (!token) {
    loading.value = false
    errorMessage.value = 'Lien de confirmation invalide.'
    return
  }

  try {
    await api.get(`/confirm-email/${token}`)
    success.value = true
  } catch (err) {
    if (err.response?.status === 400) {
      errorMessage.value = 'Ce lien de confirmation a expire ou est invalide.'
    } else if (err.response?.status === 409) {
      errorMessage.value = 'Cet email a deja ete confirme.'
      success.value = true
    } else {
      errorMessage.value = err.response?.data?.error || 'Une erreur est survenue lors de la confirmation.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(confirmEmail)
</script>

<style scoped>
.confirm-email {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;
  padding: 2rem;
}

.confirm-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  padding: 3rem;
  max-width: 480px;
  width: 100%;
  text-align: center;
}

.confirm-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
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

.icon-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  margin: 0 auto 1rem;
}

.icon-circle.success {
  background: #d4edda;
  color: #28a745;
}

.icon-circle.error {
  background: #f8d7da;
  color: #dc3545;
}

.confirm-card h2 {
  margin: 0 0 0.75rem;
  color: #2c3e50;
}

.confirm-card p {
  color: #6c757d;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.btn-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.btn-primary:hover {
  transform: translateY(-1px);
}

.btn-secondary {
  background: #e9ecef;
  color: #495057;
}

.btn-secondary:hover {
  background: #dee2e6;
}
</style>
