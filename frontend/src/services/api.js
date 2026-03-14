import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Intercepteur de requêtes - Ajouter le token JWT
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Intercepteur de réponses - Gérer les erreurs d'authentification
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    // Si 401 et pas déjà en train de rafraîchir
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      
      if (refreshToken) {
        try {
          const { data } = await axios.post(
            `${api.defaults.baseURL}/refresh-token`,
            { refresh_token: refreshToken }
          )
          
          localStorage.setItem('access_token', data.access_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          
          return api(originalRequest)
        } catch (refreshError) {
          // Échec du refresh, déconnecter
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          router.push('/login')
          return Promise.reject(refreshError)
        }
      } else {
        // Pas de refresh token, rediriger vers login
        localStorage.clear()
        router.push('/login')
        return Promise.reject(error)
      }
    }

    // Session expirée (timeout 5 minutes)
    if (error.response?.status === 401 && error.response?.data?.error?.includes('Session expired')) {
      alert('Votre session a expiré après 5 minutes d\'inactivité. Veuillez vous reconnecter.')
      localStorage.clear()
      router.push('/login')
    }

    return Promise.reject(error)
  }
)

export default api
