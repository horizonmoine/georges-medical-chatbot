import { createRouter, createWebHistory } from 'vue-router'

// Routes publiques
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'

// Routes utilisateur
import UserDashboard from '../views/UserDashboard.vue'
import UserProfile from '../views/UserProfile.vue'
import UserConsents from '../views/UserConsents.vue'
import ChatBot from '../views/ChatBot.vue'

// Routes admin
import AdminLayout from '../views/AdminLayout.vue'
import AdminOverview from '../views/AdminOverview.vue'
import AdminUsers from '../views/AdminUsers.vue'
import AdminAnalytics from '../views/AdminAnalytics.vue'
import AdminConversations from '../views/AdminConversations.vue'
import AdminConversationDetail from '../views/AdminConversationDetail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/signup',
      name: 'signup',
      component: Signup
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: UserDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: UserProfile,
      meta: { requiresAuth: true }
    },
    {
      path: '/consents',
      name: 'consents',
      component: UserConsents,
      meta: { requiresAuth: true }
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatBot,
      meta: { requiresAuth: true }
    },
    {
      path: '/chat/:conversationId',
      name: 'chat-conversation',
      component: ChatBot,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin-overview',
          component: AdminOverview
        },
        {
          path: 'users',
          name: 'admin-users',
          component: AdminUsers
        },
        {
          path: 'analytics',
          name: 'admin-analytics',
          component: AdminAnalytics
        },
        {
          path: 'conversations',
          name: 'admin-conversations',
          component: AdminConversations
        },
        {
          path: 'conversations/:conversationId',
          name: 'admin-conversation-detail',
          component: AdminConversationDetail
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

export default router
