<template>
  <div class="admin-users">
    <div class="page-header">
      <h1>👥 Gestion des utilisateurs</h1>
      <button @click="refreshUsers" class="btn-refresh">🔄 Actualiser</button>
    </div>

    <div class="filters-section">
      <input
        v-model="searchQuery"
        @input="handleSearch"
        type="text"
        placeholder="Rechercher par nom, email..."
        class="search-input"
      />
      <select v-model="roleFilter" @change="handleFilter" class="role-filter">
        <option value="">Tous les rôles</option>
        <option value="patient">Patients</option>
        <option value="medecin">Médecins</option>
        <option value="admin">Administrateurs</option>
      </select>
    </div>

    <div v-if="loading" class="loading">
      <SkeletonLoader />
    </div>

    <div v-else class="users-table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>Utilisateur</th>
            <th>Email</th>
            <th>Rôle</th>
            <th>Statut</th>
            <th>Créé le</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.userId">
            <td>
              <div class="user-cell">
                <div class="user-avatar">{{ user.prenom[0] }}{{ user.nom[0] }}</div>
                <div class="user-info">
                  <span class="user-name">{{ user.prenom }} {{ user.nom }}</span>
                  <span class="user-id">ID: {{ user.userId.substring(0, 8) }}...</span>
                </div>
              </div>
            </td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="['role-badge', user.role]">
                {{ getRoleLabel(user.role) }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                {{ user.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <div class="actions-cell">
                <button
                  @click="toggleUserStatus(user)"
                  :class="['btn-action', user.is_active ? 'deactivate' : 'activate']"
                >
                  {{ user.is_active ? '⏸️' : '▶️' }}
                </button>
                <button @click="viewUser(user)" class="btn-action view">
                  👁️
                </button>
                <button @click="deleteUser(user)" class="btn-action delete">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages"
        @page-change="handlePageChange"
      />
    </div>

    <!-- Modal de détails utilisateur -->
    <div v-if="selectedUser" class="modal-overlay" @click="selectedUser = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Détails de l'utilisateur</h2>
          <button @click="selectedUser = null" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <span class="label">Nom complet:</span>
            <span>{{ selectedUser.prenom }} {{ selectedUser.nom }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Email:</span>
            <span>{{ selectedUser.email }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Rôle:</span>
            <span>{{ getRoleLabel(selectedUser.role) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Date de naissance:</span>
            <span>{{ selectedUser.date_naissance || 'Non renseigné' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Créé le:</span>
            <span>{{ formatDateTime(selectedUser.created_at) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Email vérifié:</span>
            <span>{{ selectedUser.email_verified ? 'Oui ✓' : 'Non ✗' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de confirmation de suppression -->
    <ConfirmModal
      v-if="userToDelete"
      title="Supprimer cet utilisateur ?"
      :message="`Voulez-vous vraiment supprimer ${userToDelete.prenom} ${userToDelete.nom} ? Cette action est irréversible.`"
      confirm-text="Supprimer"
      @confirm="confirmDelete"
      @cancel="userToDelete = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const users = ref([])
const loading = ref(false)
const searchQuery = ref('')
const roleFilter = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const selectedUser = ref(null)
const userToDelete = ref(null)

onMounted(async () => {
  await loadUsers()
})

const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: 20,
      search: searchQuery.value,
      role: roleFilter.value
    }

    const { data } = await api.get('/admin/users', { params })
    users.value = data.users
    totalPages.value = Math.ceil(data.total / 20)
  } catch (error) {
    console.error('Error loading users:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadUsers()
}

const handleFilter = () => {
  currentPage.value = 1
  loadUsers()
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadUsers()
}

const refreshUsers = () => {
  loadUsers()
}

const toggleUserStatus = async (user) => {
  try {
    await api.patch(`/admin/users/${user.userId}/toggle-status`)
    user.is_active = !user.is_active
    alert(`Utilisateur ${user.is_active ? 'activé' : 'désactivé'}`)
  } catch (error) {
    alert('Erreur lors de la modification du statut')
  }
}

const viewUser = (user) => {
  selectedUser.value = user
}

const deleteUser = (user) => {
  userToDelete.value = user
}

const confirmDelete = async () => {
  try {
    await api.delete(`/admin/users/${userToDelete.value.userId}`)
    users.value = users.value.filter(u => u.userId !== userToDelete.value.userId)
    alert('Utilisateur supprimé avec succès')
    userToDelete.value = null
  } catch (error) {
    alert('Erreur lors de la suppression')
  }
}

const getRoleLabel = (role) => {
  const roles = {
    patient: 'Patient',
    medecin: 'Médecin',
    admin: 'Administrateur'
  }
  return roles[role] || role
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('fr-FR')
}

const formatDateTime = (dateString) => {
  return new Date(dateString).toLocaleString('fr-FR')
}
</script>

<style scoped>
.admin-users {
  max-width: 1400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

h1 {
  font-size: 2.5rem;
  color: #2c3e50;
}

.btn-refresh {
  padding: 0.75rem 1.5rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.filters-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.search-input, .role-filter {
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

.search-input {
  flex: 1;
}

.role-filter {
  min-width: 200px;
}

.users-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background: #f8f9fa;
}

.users-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #e0e0e0;
}

.users-table td {
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: #2c3e50;
}

.user-id {
  font-size: 0.85rem;
  color: #95a5a6;
  font-family: monospace;
}

.role-badge, .status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.role-badge.patient { background: #e3f2fd; color: #1976d2; }
.role-badge.medecin { background: #f3e5f5; color: #7b1fa2; }
.role-badge.admin { background: #fff3e0; color: #f57c00; }

.status-badge.active { background: #e8f5e9; color: #388e3c; }
.status-badge.inactive { background: #ffebee; color: #d32f2f; }

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: transform 0.2s;
}

.btn-action:hover {
  transform: scale(1.1);
}

.btn-action.activate { background: #e8f5e9; }
.btn-action.deactivate { background: #fff3e0; }
.btn-action.view { background: #e3f2fd; }
.btn-action.delete { background: #ffebee; }

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #95a5a6;
}

.modal-body {
  padding: 1.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 1rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row .label {
  font-weight: 600;
  color: #2c3e50;
}
</style>
