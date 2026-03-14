<template>
  <div class="home-container">
    <nav class="navbar">
      <div class="nav-content">
        <div class="logo">
          <img src="/assets/HEGP_LOGO.jpg" alt="HEGP Logo" />
          <span>HEGP Medical Chatbot</span>
        </div>
        <div class="nav-links">
          <router-link to="/login" class="btn-secondary">Connexion</router-link>
          <router-link to="/signup" class="btn-primary">Inscription</router-link>
        </div>
      </div>
    </nav>

    <section class="hero">
      <div class="hero-content">
        <h1>Assistant Médical Intelligent</h1>
        <p class="hero-subtitle">
          Plateforme sécurisée de recueil d'informations médicales avec IA
        </p>
        <div class="hero-features">
          <div class="feature">
            <span class="icon">🔒</span>
            <h3>Sécurité Maximale</h3>
            <p>Données chiffrées et conformité RGPD</p>
          </div>
          <div class="feature">
            <span class="icon">🤖</span>
            <h3>IA Médicale</h3>
            <p>Assistance intelligente Google Gemini</p>
          </div>
          <div class="feature">
            <span class="icon">⚡</span>
            <h3>Session Sécurisée</h3>
            <p>Timeout automatique 5 minutes</p>
          </div>
        </div>
        <router-link to="/signup" class="btn-hero">Commencer maintenant</router-link>
      </div>
    </section>

    <section class="info">
      <div class="info-content">
        <h2>À propos du projet</h2>
        <p>
          Ce projet de recherche de l'Hôpital Européen Georges-Pompidou vise à développer
          un assistant conversationnel pour faciliter le recueil d'informations médicales
          tout en garantissant la confidentialité et la sécurité des données de santé.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  // Rediriger vers dashboard si déjà connecté
  const token = localStorage.getItem('access_token')
  if (token) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.navbar {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1rem 0;
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
}

.logo img {
  height: 50px;
  border-radius: 8px;
}

.nav-links {
  display: flex;
  gap: 1rem;
}

.hero {
  padding: 4rem 2rem;
  text-align: center;
}

.hero-content {
  max-width: 1000px;
  margin: 0 auto;
  color: white;
}

.hero h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  font-weight: 700;
}

.hero-subtitle {
  font-size: 1.25rem;
  margin-bottom: 3rem;
  opacity: 0.9;
}

.hero-features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.feature {
  background: rgba(255, 255, 255, 0.1);
  padding: 2rem;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.feature h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.btn-primary, .btn-secondary, .btn-hero {
  padding: 0.75rem 2rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
  display: inline-block;
}

.btn-primary {
  background: white;
  color: #667eea;
}

.btn-secondary {
  background: transparent;
  color: white;
  border: 2px solid white;
}

.btn-hero {
  background: white;
  color: #667eea;
  font-size: 1.1rem;
  padding: 1rem 3rem;
}

.btn-primary:hover, .btn-hero:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.info {
  background: white;
  padding: 4rem 2rem;
}

.info-content {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.info h2 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: #333;
}

.info p {
  font-size: 1.1rem;
  line-height: 1.8;
  color: #666;
}

@media (max-width: 768px) {
  .hero h1 {
    font-size: 2rem;
  }
  
  .hero-features {
    grid-template-columns: 1fr;
  }
}
</style>
