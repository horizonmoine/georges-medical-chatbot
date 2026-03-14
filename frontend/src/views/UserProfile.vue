<template>
  <div class="profile-container">
    <div class="profile-header">
      <button @click="goBack" class="btn-back">← Retour</button>
      <h1>Mon Profil</h1>
    </div>

    <div class="profile-content">
      <div class="profile-card">
        <div class="avatar-section">
          <div class="avatar">{{ initials }}</div>
          <h2>{{ user.prenom }} {{ user.nom }}</h2>
          <p class="role-badge">{{ getRoleLabel(user.role) }}</p>
        </div>

        <form @submit.prevent="updateProfile" class="profile-form">
          <div class="form-group">
            <label>Nom</label>
            <input
              v-model="form.nom"
              type="text"
              required
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label>Prénom</label>
            <input
              v-model="form.prenom"
              type="text"
              required
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label>Email</label>
            <input
              v-model="user.email"
              type="email"
              disabled
              class="disabled-field"
            />
            <small>L'email ne peut pas être modifié</small>
          </div>

          <div class="form-group">
            <label>Date de naissance</label>
            <input
              v-model="form.date_naissance"
              type="date"
              :disabled="loading"
            />
          </div>

          <div v-if="error" class="error-message">{{ error }}</div>
          <div v-if="success" class="success-message">{{ success }}</div>

          <button type="submit" class="btn-primary" :disabled="loading">
            <span v-if="!loading">Enregistrer les modifications</span>
            <span v-else>Enregistrement...</span>
          </button>
        </form>
      </div>

      <div class="danger-zone">
        <h3>Zone dangereuse</h3>
        <p>La suppression de votre compte est irréversible</p>
        <button @click="showDeleteModal = true" class="btn-danger">
          Supprimer mon compte
        </button>
      </div>
    </div>

    <!-- Modal de confirmation de suppression -->
    <ConfirmModal
      v-if="showDeleteModal"
      title="Supprimer votre compte ?"
      message="Cette action est irréversible. Toutes vos données seront anonymisées conformément au RGPD."
      confirm-text="Supprimer définitivement"
      @confirm="deleteAccount"
      @cancel="showDeleteModal = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const router = useRouter()

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const form = reactive({
  nom: user.value.nom || '',
  prenom: user.value.prenom || '',
  date_naissance: user.value.date_naissance || ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')
const showDeleteModal = ref(false)

const initials = computed(() => {
  return `${form.prenom.charAt(0)}${form.nom.charAt(0)}`.toUpperCase()
})

const getRoleLabel = (role) => {
  const roles = {
    patient: 'Patient',
    medecin: 'Médecin',
    admin: 'Administrateur'
  }
  return roles[role] || role
}

const updateProfile = async () => {
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    await api.put('/user/profile', form)
    
    // Mettre à jour le localStorage
    const updatedUser = { ...user.value, ...form }
    localStorage.setItem('user', JSON.stringify(updatedUser))
    user.value = updatedUser

    success.value = 'Profil mis à jour avec succès !'
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur lors de la mise à jour'
  } finally {
    loading.value = false
  }
}

const deleteAccount = async () => {
  try {
    await api.delete('/user/delete-account', {
      data: { confirm_delete: true }
    })

    alert('Votre compte a été supprimé.')
    localStorage.clear()
    router.push('/')
  } catch (err) {
    error.value = 'Erreur lors de la suppression du compte'
    showDeleteModal.value = false
  }
}

const goBack = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 2rem;
}

.profile-header {
  max-width: 800px;
  margin: 0 auto 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
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

.profile-content {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 2rem;
}

.avatar-section {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e0e0e0;
}

.avatar {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: bold;
  margin: 0 auto 1rem;
}

.role-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #f0f0f0;
  border-radius: 20px;
  font-size: 0.9rem;
  color: #666;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.disabled-field {
  background: #f5f5f5;
  cursor: not-allowed;
}

.form-group small {
  display: block;
  margin-top: 0.25rem;
  color: #999;
  font-size: 0.85rem;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.75rem;
  border-radius: 8px;
}

.success-message {
  background: #efe;
  color: #3c3;
  padding: 0.75rem;
  border-radius: 8px;
}

.btn-primary {
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  transition: transform 0.2s;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.danger-zone {
  background: white;
  border: 2px solid #dc3545;
  border-radius: 12px;
  padding: 2rem;
}

.danger-zone h3 {
  color: #dc3545;
  margin-bottom: 0.5rem;
}

.danger-zone p {
  color: #666;
  margin-bottom: 1.5rem;
}

.btn-danger {
  padding: 0.75rem 2rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.btn-danger:hover {
  background: #c82333;
}
</style>
