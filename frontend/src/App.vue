<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { startSessionMonitor } from '@/services/sessionMonitor'

const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  // Charger l'utilisateur depuis localStorage
  await userStore.loadUser()
  
  // Démarrer le monitoring de session si connecté
  if (userStore.isAuthenticated) {
    startSessionMonitor(() => {
      alert('Votre session a expiré après 5 minutes d\'inactivité.')
      userStore.logout()
      router.push('/login')
    })
  }
})
</script>

<style>
@import './styles/main.scss';
</style>
