<template>
  <div class="not-found">
    <div class="not-found-card">
      <h1 class="error-code">404</h1>
      <h2>Page introuvable</h2>
      <p>La page que vous recherchez n'existe pas ou a ete deplacee.</p>
      <router-link to="/" class="btn-home">Retour a l'accueil</router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;
  padding: 2rem;
}

.not-found-card {
  text-align: center;
  background: #ffffff;
  padding: 3rem 4rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  max-width: 480px;
  width: 100%;
}

.error-code {
  font-size: 6rem;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.not-found-card h2 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin: 1rem 0 0.5rem;
}

.not-found-card p {
  color: #6c757d;
  margin-bottom: 2rem;
  line-height: 1.5;
}

.btn-home {
  display: inline-block;
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-home:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
