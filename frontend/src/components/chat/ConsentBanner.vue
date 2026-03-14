<template>
  <div v-if="visible" class="consent-banner">
    <div class="consent-content">
      <span class="consent-icon">&#x2139;</span>
      <p>
        <strong>Rappel :</strong> Vos donnees sont collectees dans le cadre du projet
        <strong>{{ projectName }}</strong>.
        Vous pouvez retirer votre consentement a tout moment depuis votre profil.
      </p>
    </div>
    <button @click="dismiss" class="btn-dismiss" title="Fermer">&times;</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  projectName: { type: String, default: 'Georges' }
})

const visible = ref(true)

const dismiss = () => {
  visible.value = false
  sessionStorage.setItem('consent_banner_dismissed', 'true')
}

// Check if already dismissed this session
if (sessionStorage.getItem('consent_banner_dismissed') === 'true') {
  visible.value = false
}
</script>

<style scoped>
.consent-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: #e8f4fd;
  border: 1px solid #b6d9f2;
  border-radius: 8px;
  position: relative;
  z-index: 10;
}

.consent-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  flex: 1;
}

.consent-icon {
  font-size: 1.3rem;
  color: #2b78a8;
  flex-shrink: 0;
  line-height: 1.4;
}

.consent-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #1a5276;
  line-height: 1.5;
}

.btn-dismiss {
  background: none;
  border: none;
  font-size: 1.4rem;
  color: #2b78a8;
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
  flex-shrink: 0;
  transition: color 0.2s;
}

.btn-dismiss:hover {
  color: #1a5276;
}
</style>
