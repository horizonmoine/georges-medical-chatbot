<template>
  <div class="signup-container">
    <div class="signup-card">
      <div class="logo-section">
        <img src="/assets/HEGP_LOGO.jpg" alt="HEGP Logo" />
        <h1>Créer un compte</h1>
        <p>Rejoignez la plateforme HEGP Medical Chatbot</p>
      </div>

      <form @submit.prevent="handleSignup" class="signup-form">
        <div class="form-row">
          <div class="form-group">
            <label for="nom">Nom *</label>
            <input
              id="nom"
              v-model="form.nom"
              type="text"
              required
              placeholder="Dupont"
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label for="prenom">Prénom *</label>
            <input
              id="prenom"
              v-model="form.prenom"
              type="text"
              required
              placeholder="Jean"
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="email">Email *</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
            placeholder="jean.dupont@exemple.fr"
            :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label for="password">Mot de passe *</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            placeholder="••••••••"
            :disabled="loading"
            @input="validatePassword"
          />
          <div v-if="passwordErrors.length" class="password-hints">
            <p v-for="error in passwordErrors" :key="error" class="hint-error">
              {{ error }}
            </p>
          </div>
        </div>

        <div class="form-group">
          <label for="date_naissance">Date de naissance</label>
          <input
            id="date_naissance"
            v-model="form.date_naissance"
            type="date"
            :disabled="loading"
          />
        </div>

        <div class="consent-section">
          <label class="checkbox-label">
            <input
              v-model="consents.dataProcessing"
              type="checkbox"
              required
            />
            <span>
              J'accepte le traitement de mes données conformément au RGPD *
            </span>
          </label>
          
          <label class="checkbox-label">
            <input v-model="consents.research" type="checkbox" />
            <span>
              J'accepte que mes données soient utilisées pour la recherche médicale
            </span>
          </label>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>

        <button type="submit" class="btn-signup" :disabled="loading">
          <span v-if="!loading">Créer mon compte</span>
          <span v-else">Création en cours...</span>
        </button>
      </form>

      <div class="footer-links">
        <p>Vous avez déjà un compte ?</p>
        <router-link to="/login">Se connecter</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { validatePassword as checkPassword } from '@/utils/validators'

const router = useRouter()

const form = reactive({
  nom: '',
  prenom: '',
  email: '',
  password: '',
  date_naissance: '',
  role: 'patient'
})

const consents = reactive({
  dataProcessing: false,
  research: false
})

const passwordErrors = ref([])
const error = ref('')
const success = ref('')
const loading = ref(false)

const validatePassword = () => {
  passwordErrors.value = []
  
  if (form.password.length < 8) {
    passwordErrors.value.push('Minimum 8 caractères')
  }
  if (!/[A-Z]/.test(form.password)) {
    passwordErrors.value.push('Au moins 1 majuscule')
  }
  if (!/[a-z]/.test(form.password)) {
    passwordErrors.value.push('Au moins 1 minuscule')
  }
  if (!/\d/.test(form.password)) {
    passwordErrors.value.push('Au moins 1 chiffre')
  }
  if (!/[@$!%*?&]/.test(form.password)) {
    passwordErrors.value.push('Au moins 1 caractère spécial (@$!%*?&)')
  }
}

const handleSignup = async () => {
  error.value = ''
  success.value = ''
  loading.value = true

  // Vérifier le consentement obligatoire
  if (!consents.dataProcessing) {
    error.value = 'Vous devez accepter le traitement des données'
    loading.value = false
    return
  }

  // Vérifier la force du mot de passe
  if (passwordErrors.value.length > 0) {
    error.value = 'Veuillez corriger les erreurs du mot de passe'
    loading.value = false
    return
  }

  try {
    const { data } = await api.post('/signup', form)

    success.value = 'Compte créé ! Vérifiez votre email pour confirmer votre inscription.'
    
    // Rediriger vers login après 3 secondes
    setTimeout(() => {
      router.push('/login')
    }, 3000)
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur lors de l\'inscription'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.signup-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.signup-card {
  background: white;
  border-radius: 16px;
  padding: 3rem;
  max-width: 600px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-height: 90vh;
  overflow-y: auto;
}

.logo-section {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-section img {
  height: 70px;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
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
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.password-hints {
  margin-top: 0.5rem;
  font-size: 0.85rem;
}

.hint-error {
  color: #c33;
  margin: 0.25rem 0;
}

.consent-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.checkbox-label {
  display: flex;
  align-items: start;
  gap: 0.75rem;
  margin-bottom: 1rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 0.25rem;
  width: auto;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.success-message {
  background: #efe;
  color: #3c3;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.btn-signup {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-signup:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-signup:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
