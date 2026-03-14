<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <img src="/assets/HEGP_LOGO.jpg" alt="HEGP" />
        <h2>Admin Panel</h2>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/admin" class="nav-item" exact-active-class="active">
          <span class="icon">📊</span>
          <span>Vue d'ensemble</span>
        </router-link>

        <router-link to="/admin/users" class="nav-item" active-class="active">
          <span class="icon">👥</span>
          <span>Utilisateurs</span>
        </router-link>

        <router-link to="/admin/conversations" class="nav-item" active-class="active">
          <span class="icon">💬</span>
          <span>Conversations</span>
        </router-link>

        <router-link to="/admin/analytics" class="nav-item" active-class="active">
          <span class="icon">📈</span>
          <span>Analytics</span>
        </router-link>

        <router-link to="/admin/requests" class="nav-item" active-class="active">
          <span class="icon">📋</span>
          <span>Demandes</span>
        </router-link>

        <router-link to="/admin/projects" class="nav-item" active-class="active">
          <span class="icon">📁</span>
          <span>Projets</span>
        </router-link>

        <div class="nav-divider"></div>

        <router-link to="/dashboard" class="nav-item">
          <span class="icon">🏠</span>
          <span>Retour Dashboard</span>
        </router-link>

        <button @click="handleLogout" class="nav-item logout">
          <span class="icon">🚪</span>
          <span>Déconnexion</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <p class="admin-name">{{ user.prenom }} {{ user.nom }}</p>
        <p class="admin-role">Administrateur</p>
      </div>
    </aside>

    <main class="admin-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

const handleLogout = async () => {
  try {
    await api.post('/logout')
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    localStorage.clear()
    router.push('/login')
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}

.admin-sidebar {
  width: 280px;
  background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header img {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.sidebar-header h2 {
  font-size: 1.5rem;
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.3s;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font-size: 1rem;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border-left: 4px solid #3498db;
}

.nav-item .icon {
  font-size: 1.5rem;
}

.nav-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 1rem 0;
}

.nav-item.logout {
  color: #e74c3c;
}

.sidebar-footer {
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
}

.admin-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.admin-role {
  font-size: 0.85rem;
  opacity: 0.7;
}

.admin-content {
  margin-left: 280px;
  flex: 1;
  padding: 2rem;
  min-height: 100vh;
}

@media (max-width: 768px) {
  .admin-sidebar {
    width: 100%;
    position: relative;
    height: auto;
  }

  .admin-content {
    margin-left: 0;
  }
}
</style>
