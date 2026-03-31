import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './styles/main.scss'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)

// Navigation guard global — utilise le store Pinia après son initialisation
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
  const requiresAdmin = to.matched.some(r => r.meta.requiresAdmin)

  // Lire directement depuis localStorage pour éviter le problème
  // d'initialisation du store avant le montage de l'app
  const token = localStorage.getItem('access_token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  const role = user?.role || null
  const isAdmin = role === 'admin' || role === 'super_admin'

  if (requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (requiresAdmin && !isAdmin) {
    next('/dashboard')
  } else {
    next()
  }
})

app.mount('#app')
