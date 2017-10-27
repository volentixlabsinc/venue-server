<template>
  <!-- Login Modal -->
  <b-modal id="modal1" title="Login Form" v-if="!$store.state.apiToken" ref="login-modal" hide-footer>
    <b-form @submit="login($event)" @click="clearLoginError()">
      <b-form-group label="Username">
        <b-form-input v-model.trim="username" v-validate="{ required: true }" name="username" placeholder="Enter username"></b-form-input>
        <span v-show="errors.has('username')" class="help is-danger">
          {{ errors.first('username') }}
        </span>
      </b-form-group>
      <b-form-group label="Password">
        <b-form-input type="password" v-model.trim="password" v-validate="{ required: true }" name="password" placeholder="Enter password"></b-form-input>
        <span v-show="errors.has('password')" class="help is-danger">
          {{ errors.first('password') }}
        </span>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableLoginSubmit">Submit</b-button>
        <span v-show="loginError" class="help is-danger" style="margin-top: 15px;">
          The username or password you entered was incorrect!
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
      this.$cookies.set('apiToken', data.token)
    },
    login (event) {
      event.preventDefault()
      axios.post('/authenticate/', {
        username: this.username,
        password: this.password
      }).then(response => {
        this.password = ''
        this.setUser(response.data)
        this.$router.push('/dashboard')
      }).catch(e => {
        this.loginError = true
      })
    }
  },
  created () {
    var apiTokenCookie = this.$cookies.get('apiToken')
    axios.post('/get-user/', {
      token: apiTokenCookie
    }).then(response => {
      this.setUser(response.data)
    })
  }
}
</script>