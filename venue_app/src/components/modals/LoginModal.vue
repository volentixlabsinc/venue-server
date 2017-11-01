<template>
  <!-- Login Modal -->
  <b-modal id="login-modal" :title="$i18n.t('login_form')" v-if="!$store.state.apiToken" ref="loginModal" hide-footer>
    <b-form @submit="login($event)" @click="clearLoginError()">
      <b-form-group :label="$i18n.t('username')">
        <b-form-input v-model.trim="username" v-validate="{ required: true }" name="username" :placeholder="$i18n.t('enter_username')"></b-form-input>
        <span v-show="errors.has('username')" class="help is-danger">
          {{ errors.first('username') }}
        </span>
      </b-form-group>
      <b-form-group :label="$i18n.t('password')">
        <b-form-input type="password" v-model.trim="password" v-validate="{ required: true }" name="password" :placeholder="$i18n.t('enter_password')"></b-form-input>
        <span v-show="errors.has('password')" class="help is-danger">
          {{ errors.first('password') }}
        </span>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableLoginSubmit">{{ $t('submit') }}</b-button>
        <span v-show="loginError" class="help is-danger" style="margin-top: 15px;">
          {{ $t('login_error') }}
        </span>
      </b-form-group>
    </b-form>
  </b-modal>
</template>

<script>
import axios from 'axios'

export default {
  name: 'LoginModal',
  data () {
    return {
      username: '',
      password: '',
      loginError: false
    }
  },
  computed: {
    disableLoginSubmit () {
      return this.errors.any()
    }
  },
  methods: {
    clearLoginError () {
      this.loginError = false
    },
    setUser (data) {
      this.$store.commit('updateApiToken', data.token)
      this.$store.commit('updateUser', data.username, data.email)
    },
    login (event) {
      event.preventDefault()
      axios.post('/authenticate/', {
        username: this.username,
        password: this.password
      }).then(response => {
        // Set user data
        this.password = ''
        this.setUser(response.data)
        // Fix the authorization header for all HTTP requests
        var authHeader = 'Token ' + this.$store.state.apiToken
        axios.defaults.headers.common['Authorization'] = authHeader
        // Redirect to dashboard
        this.$router.push('/dashboard')
      }).catch(e => {
        this.loginError = true
      })
    }
  },
  created () {
    axios.post('/get-user/', {
      token: this.$store.state.apiToken
    }).then(response => {
      if (response.data.found === true) {
        this.setUser(response.data)
      }
    })
  }
}
</script>