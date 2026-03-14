<template>
  <div class="admin-projects">
    <div class="page-header">
      <h1>Gestion des projets</h1>
      <button @click="showCreateForm = true" class="btn btn-primary">
        + Nouveau projet
      </button>
    </div>

    <!-- Create / Edit form -->
    <div v-if="showCreateForm || editingProject" class="project-form-overlay">
      <div class="project-form-card">
        <h2>{{ editingProject ? 'Modifier le projet' : 'Creer un projet' }}</h2>

        <form @submit.prevent="editingProject ? updateProject() : createProject()">
          <div class="form-group">
            <label for="name">Nom du projet</label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              class="form-control"
              placeholder="Nom du projet"
              required
            />
          </div>

          <div class="form-group">
            <label for="slug">Slug (URL)</label>
            <input
              id="slug"
              v-model="form.slug"
              type="text"
              class="form-control"
              placeholder="mon-projet"
              required
            />
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <textarea
              id="description"
              v-model="form.description"
              class="form-control"
              rows="3"
              placeholder="Description du projet..."
            ></textarea>
          </div>

          <div class="form-group">
            <label for="consent_text">Texte de consentement</label>
            <textarea
              id="consent_text"
              v-model="form.consent_text"
              class="form-control"
              rows="5"
              placeholder="Texte affiche lors de la demande de consentement..."
            ></textarea>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.active" />
              <span>Projet actif</span>
            </label>
          </div>

          <div v-if="formError" class="alert alert-danger">{{ formError }}</div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="cancelForm">Annuler</button>
            <button type="submit" class="btn btn-primary" :disabled="formLoading">
              {{ formLoading ? 'Enregistrement...' : (editingProject ? 'Mettre a jour' : 'Creer') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Projects list -->
    <div v-if="loading" class="loading-state">
      <p>Chargement des projets...</p>
    </div>

    <div v-else-if="projects.length === 0" class="empty-state">
      <p>Aucun projet pour le moment.</p>
    </div>

    <div v-else class="projects-grid">
      <div v-for="project in projects" :key="project._id || project.id" class="project-card">
        <div class="project-card-header">
          <h3>{{ project.name }}</h3>
          <span :class="['status-badge', project.active ? 'active' : 'inactive']">
            {{ project.active ? 'Actif' : 'Inactif' }}
          </span>
        </div>

        <p class="project-slug">/project/{{ project.slug }}</p>
        <p class="project-description">{{ project.description || 'Pas de description.' }}</p>

        <div class="project-stats">
          <div class="stat">
            <span class="stat-value">{{ project.participant_count || 0 }}</span>
            <span class="stat-label">Participants</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ project.conversation_count || 0 }}</span>
            <span class="stat-label">Conversations</span>
          </div>
        </div>

        <div class="project-actions">
          <button @click="startEdit(project)" class="btn btn-sm btn-outline">Modifier</button>
          <button @click="confirmDelete(project)" class="btn btn-sm btn-danger">Supprimer</button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation -->
    <div v-if="deletingProject" class="project-form-overlay">
      <div class="project-form-card confirm-delete">
        <h2>Confirmer la suppression</h2>
        <p>Voulez-vous vraiment supprimer le projet <strong>{{ deletingProject.name }}</strong> ?</p>
        <p class="text-danger">Cette action est irreversible.</p>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="deletingProject = null">Annuler</button>
          <button class="btn btn-danger" @click="deleteProject" :disabled="formLoading">
            {{ formLoading ? 'Suppression...' : 'Supprimer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const projects = ref([])
const loading = ref(true)
const showCreateForm = ref(false)
const editingProject = ref(null)
const deletingProject = ref(null)
const formLoading = ref(false)
const formError = ref('')

const form = ref({
  name: '',
  slug: '',
  description: '',
  consent_text: '',
  active: true
})

const resetForm = () => {
  form.value = {
    name: '',
    slug: '',
    description: '',
    consent_text: '',
    active: true
  }
  formError.value = ''
}

const cancelForm = () => {
  showCreateForm.value = false
  editingProject.value = null
  resetForm()
}

const loadProjects = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/admin/projects')
    projects.value = data.projects || []
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  formLoading.value = true
  formError.value = ''

  try {
    const { data } = await api.post('/admin/projects', form.value)
    projects.value.push(data.project || data)
    cancelForm()
  } catch (err) {
    formError.value = err.response?.data?.error || 'Erreur lors de la creation du projet.'
  } finally {
    formLoading.value = false
  }
}

const startEdit = (project) => {
  editingProject.value = project
  form.value = {
    name: project.name || '',
    slug: project.slug || '',
    description: project.description || '',
    consent_text: project.consent_text || '',
    active: project.active !== false
  }
}

const updateProject = async () => {
  formLoading.value = true
  formError.value = ''
  const projectId = editingProject.value._id || editingProject.value.id

  try {
    const { data } = await api.put(`/admin/projects/${projectId}`, form.value)
    const idx = projects.value.findIndex(p => (p._id || p.id) === projectId)
    if (idx !== -1) {
      projects.value[idx] = data.project || { ...projects.value[idx], ...form.value }
    }
    cancelForm()
  } catch (err) {
    formError.value = err.response?.data?.error || 'Erreur lors de la mise a jour.'
  } finally {
    formLoading.value = false
  }
}

const confirmDelete = (project) => {
  deletingProject.value = project
}

const deleteProject = async () => {
  formLoading.value = true
  const projectId = deletingProject.value._id || deletingProject.value.id

  try {
    await api.delete(`/admin/projects/${projectId}`)
    projects.value = projects.value.filter(p => (p._id || p.id) !== projectId)
    deletingProject.value = null
  } catch (err) {
    formError.value = err.response?.data?.error || 'Erreur lors de la suppression.'
  } finally {
    formLoading.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.admin-projects {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  margin: 0;
  font-size: 1.75rem;
  color: #2c3e50;
}

.btn {
  padding: 0.6rem 1.25rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
  text-decoration: none;
  display: inline-block;
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

.btn-danger {
  background: #dc3545;
  color: #ffffff;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
}

.btn-outline {
  background: transparent;
  border: 1px solid #667eea;
  color: #667eea;
}

.btn-outline:hover {
  background: #667eea;
  color: #ffffff;
}

/* Form overlay */
.project-form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.project-form-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 2rem;
  max-width: 560px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.project-form-card h2 {
  margin: 0 0 1.5rem;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
  color: #4a5568;
  font-size: 0.9rem;
}

.form-control {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
}

textarea.form-control {
  resize: vertical;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  color: #4a5568;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.alert-danger {
  background: #f8d7da;
  color: #721c24;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.confirm-delete .text-danger {
  color: #dc3545;
  font-size: 0.9rem;
}

/* Loading / empty */
.loading-state,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

/* Projects grid */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.5rem;
}

.project-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 1.5rem;
  transition: box-shadow 0.2s;
}

.project-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.project-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.project-card-header h3 {
  margin: 0;
  font-size: 1.15rem;
  color: #2c3e50;
}

.status-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.project-slug {
  font-family: monospace;
  font-size: 0.85rem;
  color: #667eea;
  margin: 0 0 0.75rem;
}

.project-description {
  color: #6c757d;
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.project-stats {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem 0;
  border-top: 1px solid #e8ecf1;
  border-bottom: 1px solid #e8ecf1;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.8rem;
  color: #8c9bab;
}

.project-actions {
  display: flex;
  gap: 0.75rem;
}

@media (max-width: 768px) {
  .projects-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
}
</style>
