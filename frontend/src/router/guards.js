/**
 * Navigation Guards
 */
import { useUserStore } from '@/stores/user'

export const requireAuth = (to, from, next) => {
  const userStore = useUserStore()
  
  if (!userStore.isAuthenticated) {
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  } else {
    next()
  }
}

export const requireAdmin = (to, from, next) => {
  const userStore = useUserStore()
  
  if (!userStore.isAuthenticated) {
    next('/login')
  } else if (!userStore.isAdmin) {
    next('/dashboard')
  } else {
    next()
  }
}

export const guestOnly = (to, from, next) => {
  const userStore = useUserStore()
  
  if (userStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
}
