<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-section">
        <img src="/assets/HEGP_LOGO.jpg" alt="HEGP Logo" />
        <h1>HEGP Medical Chatbot</h1>
        <p>Connexion sécurisée</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            placeholder="votre.email@exemple.fr"
            :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label for="password">Mot de passe</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="••••••••"
            :disabled="loading"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="btn-login" :disabled="loading">
          <span v-if="!loading">Se connecter</span>
          <span v-else>Connexion en cours...</span>
        </button>
      </form>

      <div class="footer-links">
        <p>Pas encore de compte ?</p>
        <router-link to="/signup">S'inscrire</router-link>
      </div>

      <div class="security-notice">
        <span class="icon">🔒</span>
        <p>Session sécurisée avec timeout automatique de 5 minutes</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { startSessionMonitor } from '@/services/sessionMonitor'

const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    const { data } = await api.post('/login', {
      email: email.value,
      password: password.value
    })

    // Stocker les tokens et les infos utilisateur
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))

    // Démarrer le monitoring de session (5 minutes)
    startSessionMonitor(() => {
      alert('Votre session a expiré après 5 minutes d\'inactivité.')
      localStorage.clear()
      router.push('/login')
    })

    // Rediriger selon le rôle
    if (data.user.role === 'admin') {
      router.push('/admin')
    } else {
      router.push('/dashboard')
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 3rem;
  max-width: 450px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.logo-section {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-section img {
  height: 80px;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.logo-section h1 {
  font-size: 1.75rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.logo-section p {
  color: #666;
}

.login-form {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
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
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  border-left: 4px solid #c33;
}

.btn-login {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-login:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.footer-links {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.footer-links p {
  margin-bottom: 0.5rem;
  color: #666;
}

.footer-links a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.security-notice {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f0f7ff;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #666;
}

.security-notice .icon {
  font-size: 1.25rem;
}
</style>
