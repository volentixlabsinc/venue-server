import Vue from 'vue'
import Router from 'vue-router'
import Home from '@/components/Home'
import Dashboard from '@/components/Dashboard'
import Leaderboard from '@/components/Leaderboard'
import Signatures from '@/components/Signatures'
import Settings from '@/components/Settings'
import store from '@/store'
import axios from 'axios'

Vue.use(Router)

const router = new Router({
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/leaderboard',
      name: 'Leaderboard',
      component: Leaderboard
    },
    {
      path: '/signatures',
      name: 'Signatures',
      component: Signatures,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: Settings,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  // Always hide the footer before switching to a new route
  store.commit('updateShowFooter', false)
  // if (to.path !== '/') {
  // Fix the authorization header for all HTTP requests
  if (store.state.apiToken) {
    var authHeader = 'Token ' + store.state.apiToken
    axios.defaults.headers.common['Authorization'] = authHeader
  } else {
    delete axios.defaults.headers.common['Authorization']
  }
  // }
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // this route requires auth, check if logged in
    // if not, redirect to login page.
    if (!store.state.apiToken) {
      window.location.href = '/'
    } else {
      next()
    }
  } else {
    next() // make sure to always call next()!
  }
})

export default router
