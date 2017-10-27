import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
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
