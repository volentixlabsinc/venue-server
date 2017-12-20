import Vue from 'vue'
import Vuex from 'vuex'
import createPersistedState from 'vuex-persistedstate'

Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [createPersistedState({key: 'volentix_venue'})],
  state: {
    apiToken: '',
    userName: null,
    userEmail: null,
    language: 'en',
    languages: [],
    showLoginForm: false,
    showFooter: false
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
    },
    updateLanguage (state, value) {
      state.language = value
    },
    updateShowFooter (state, value) {
      state.showFooter = value
    },
    setLanguageOptions (state, value) {
      state.languages = value
    }
  }
})
