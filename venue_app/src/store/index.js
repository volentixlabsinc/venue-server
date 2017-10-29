import Vue from 'vue'
import Vuex from 'vuex'
import createPersistedState from 'vuex-persistedstate'

Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [createPersistedState()],
  state: {
    apiToken: '',
    user: null,
    language: 'English'
  },
  mutations: {
    updateApiToken (state, token) {
      state.apiToken = token
    },
    updateUser (state, userName, userEmail) {
      state.user = {userName: userName, userEmail: userEmail}
    }
  }
})
