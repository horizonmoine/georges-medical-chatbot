import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useProjectStore = defineStore('project', () => {
  // State
  const currentProject = ref(null)
  const projects = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const currentProjectName = computed(() => currentProject.value?.name || '')

  // Actions
  const fetchProjects = async () => {
    loading.value = true
    error.value = null

    try {
      const { data } = await api.get('/projects')
      projects.value = data.projects || []
      return projects.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du chargement des projets'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchProjectBySlug = async (slug) => {
    loading.value = true
    error.value = null

    try {
      const { data } = await api.get(`/projects/${slug}`)
      currentProject.value = data.project || data
      return currentProject.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Projet introuvable'
      throw err
    } finally {
      loading.value = false
    }
  }

  const requestAccess = async (projectId) => {
    loading.value = true
    error.value = null

    try {
      const { data } = await api.post(`/projects/${projectId}/request-access`)
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors de la demande'
      throw err
    } finally {
      loading.value = false
    }
  }

  const giveConsent = async (projectId) => {
    loading.value = true
    error.value = null

    try {
      const { data } = await api.post(`/projects/${projectId}/consent`)
      if (currentProject.value && currentProject.value._id === projectId) {
        currentProject.value.user_consented = true
      }
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors du consentement'
      throw err
    } finally {
      loading.value = false
    }
  }

  const checkInclusion = async (projectId) => {
    try {
      const { data } = await api.get(`/projects/${projectId}/inclusion`)
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de verification'
      throw err
    }
  }

  return {
    // State
    currentProject,
    projects,
    loading,
    error,

    // Getters
    currentProjectName,

    // Actions
    fetchProjects,
    fetchProjectBySlug,
    requestAccess,
    giveConsent,
    checkInclusion
  }
})
