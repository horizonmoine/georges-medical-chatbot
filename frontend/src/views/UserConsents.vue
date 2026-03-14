<template>
  <div class="consents-container">
    <div class="consents-header">
      <button @click="goBack" class="btn-back">← Retour</button>
      <h1>🔒 Gestion RGPD & Consentements</h1>
    </div>

    <div class="consents-content">
      <div class="info-section">
        <h2>Vos droits RGPD</h2>
        <p>
          Conformément au Règlement Général sur la Protection des Données (RGPD),
          vous disposez de droits sur vos données personnelles.
        </p>
      </div>

      <div class="consents-card">
        <h3>Mes consentements</h3>
        
        <div v-if="loading" class="loading">
          <SkeletonLoader />
        </div>

        <div v-else class="consents-list">
          <div class="consent-item">
            <div class="consent-info">
              <h4>Traitement des données de santé</h4>
              <p>Autorisation de traiter vos données pour le service médical</p>
              <span class="consent-date">
                Accordé le {{ formatDate(requiredConsent.timestamp) }}
              </span>
            </div>
            <div class="consent-status required">
              <span class="status-badge">Obligatoire</span>
              <span class="status-icon">✓</span>
            </div>
          </div>

          <div class="consent-item">
            <div class="consent-info">
              <h4>Utilisation pour la recherche</h4>
              <p>Autoriser l'utilisation anonymisée de vos données pour la recherche médicale</p>
              <span v-if="researchConsent.granted" class="consent-date">
                Accordé le {{ formatDate(researchConsent.timestamp) }}
              </span>
            </div>
            <div class="consent-status">
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  v-model="researchConsent.granted"
                  @change="updateConsent('research', researchConsent.granted)"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>

          <div class="consent-item">
            <div class="consent-info">
              <h4>Communications par email</h4>
              <p>Recevoir des informations sur les nouveautés du service</p>
              <span v-if="emailConsent.granted" class="consent-date">
                Accordé le {{ formatDate(emailConsent.timestamp) }}
              </span>
            </div>
            <div class="consent-status">
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  v-model="emailConsent.granted"
                  @change="updateConsent('email', emailConsent.granted)"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="actions-card">
        <h3>Actions RGPD</h3>
        
        <div class="action-item">
          <div class="action-info">
            <h4>📥 Droit à la portabilité</h4>
            <p>Téléchargez toutes vos données au format JSON</p>
          </div>
          <button @click="exportData" class="btn-action">
            Exporter mes données
          </button>
        </div>

        <div class="action-item">
          <div class="action-info">
            <h4>👁️ Droit d'accès</h4>
            <p>Consultez l'historique de vos activités</p>
          </div>
          <button @click="viewAuditTrail" class="btn-action">
            Voir l'historique
          </button>
        </div>

        <div class="action-item danger">
          <div class="action-info">
            <h4>🗑️ Droit à l'effacement</h4>
            <p>Supprimer définitivement votre compte et vos données</p>
          </div>
          <button @click="$router.push('/profile')" class="btn-action-danger">
            Gérer la suppression
          </button>
        </div>
      </div>

      <div class="audit-section" v-if="showAudit">
        <h3>Historique d'audit</h3>
        <div class="audit-list">
          <div v-for="log in auditLogs" :key="log.timestamp" class="audit-item">
            <span class="audit-date">{{ formatDateTime(log.timestamp) }}</span>
            <span class="audit-action">{{ log.action }}</span>
            <span class="audit-ip">IP: {{ log.ip_address }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

const router = useRouter()

const loading = ref(false)
const showAudit = ref(false)
const auditLogs = ref([])

const requiredConsent = ref({
  granted: true,
  timestamp: new Date()
})

const researchConsent = ref({
  granted: false,
  timestamp: null
})

const emailConsent = ref({
  granted: false,
  timestamp: null
})

onMounted(async () => {
  await loadConsents()
})

const loadConsents = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/user/consents')
    
    // Parser les consentements
    data.consents.forEach(consent => {
      if (consent.consent_type === 'data_processing') {
        requiredConsent.value = consent
      } else if (consent.consent_type === 'research') {
        researchConsent.value = consent
      } else if (consent.consent_type === 'email') {
        emailConsent.value = consent
      }
    })
  } catch (error) {
    console.error('Error loading consents:', error)
  } finally {
    loading.value = false
  }
}

const updateConsent = async (type, granted) => {
  try {
    await api.post('/user/consents', {
      consent_type: type,
      granted: granted
    })
    
    alert('Consentement mis à jour avec succès')
  } catch (error) {
    alert('Erreur lors de la mise à jour du consentement')
  }
}

const exportData = async () => {
  try {
    const { data } = await api.get('/user/data-export')
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `hegp-export-${new Date().toISOString()}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    
    alert('Export réussi !')
  } catch (error) {
    alert('Erreur lors de l\'export')
  }
}

const viewAuditTrail = () => {
  showAudit.value = !showAudit.value
  if (showAudit.value && auditLogs.value.length === 0) {
    // Charger les logs d'audit (simulé ici)
    auditLogs.value = [
      { timestamp: new Date(), action: 'login', ip_address: '192.168.1.1' },
      { timestamp: new Date(Date.now() - 86400000), action: 'profile_updated', ip_address: '192.168.1.1' }
    ]
  }
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('fr-FR')
}

const formatDateTime = (date) => {
  return new Date(date).toLocaleString('fr-FR')
}

const goBack = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.consents-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 2rem;
}

.consents-header {
  max-width: 1000px;
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

.consents-content {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.info-section {
  background: #fff3cd;
  padding: 1.5rem;
  border-radius: 12px;
  border-left: 4px solid #ffc107;
}

.consents-card, .actions-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.consents-card h3, .actions-card h3 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
}

.consents-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.consent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.consent-info h4 {
  margin-bottom: 0.5rem;
  color: #333;
}

.consent-info p {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.consent-date {
  font-size: 0.85rem;
  color: #999;
}

.consent-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  background: #28a745;
  color: white;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-icon {
  font-size: 1.5rem;
  color: #28a745;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #667eea;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.action-item:last-child {
  border-bottom: none;
}

.action-item.danger {
  background: #fff5f5;
  border-radius: 8px;
  border: 1px solid #fee;
}

.action-info h4 {
  margin-bottom: 0.5rem;
}

.action-info p {
  color: #666;
  font-size: 0.9rem;
}

.btn-action, .btn-action-danger {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-action {
  background: #667eea;
  color: white;
}

.btn-action-danger {
  background: #dc3545;
  color: white;
}

.btn-action:hover, .btn-action-danger:hover {
  transform: translateY(-2px);
}

.audit-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.audit-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.audit-item {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
}

.audit-date {
  color: #666;
}

.audit-action {
  font-weight: 600;
  color: #333;
}

.audit-ip {
  color: #999;
  font-family: monospace;
}
</style>
