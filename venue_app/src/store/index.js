import Vue from 'vue'
import Vuex from 'vuex'
import createPersistedState from 'vuex-persistedstate'

Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [createPersistedState()],
  state: {
    apiToken: '',
    userName: null,
    userEmail: null,
    language: 'English',
    showLoginForm: false
  },
  mutations: {
    updateApiToken (state, token) {
      state.apiToken = token
    },
    updateUserName (state, username) {
      state.userName = username
    },
    updateUserEmail (state, email) {
      state.userEmail = email
    },
    updateShowLoginForm (state, value) {
      state.showLoginForm = value
    }
  }
})
