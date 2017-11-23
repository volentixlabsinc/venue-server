import Vue from 'vue'
import Vuex from 'vuex'
import createPersistedState from 'vuex-persistedstate'

Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [createPersistedState()],
  state: {
    apiToken: '',
    user: null,
    language: 'English',
    showLoginForm: false
  },
  mutations: {
    updateApiToken (state, token) {
      state.apiToken = token
    },
    updateUserName (state, username) {
      state.user.userName = username
    },
    updateUserEmail (state, email) {
      state.user.userEmail = email
    },
    updateShowLoginForm (state, value) {
      state.showLoginForm = value
    }
  }
})
