<template>
  <!-- Login Modal -->
  <b-modal id="login-modal" :title="$i18n.t('login_form')" v-if="!$store.state.apiToken" ref="loginModal" centered hide-footer>
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
        <img v-show="formSubmitted" src="../../assets/animated_spinner.gif" height="50">
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
      loginError: false,
      formSubmitted: false
    }
  },
  computed: {
    disableLoginSubmit () {
      return this.errors.any() || this.formSubmitted || this.isFormPristine
    },
    isFormPristine () {
      return Object.keys(this.fields).some(key => this.fields[key].pristine)
    }
  },
  methods: {
    clearLoginError () {
      this.loginError = false
    },
    setUser (data) {
      this.$store.commit('updateApiToken', data.token)
      this.$store.commit('updateUserName', data.username)
      this.$store.commit('updateUserEmail', data.email)
    },
    login (event) {
      event.preventDefault()
      this.formSubmitted = true
      axios.post('/authenticate/', {
        username: this.username,
        password: this.password
      }).then(response => {
        if (response.data.email_confirmed === true) {
          // Set user data
          this.password = ''
          this.setUser(response.data)
          // Fix the authorization header for all HTTP requests
          var authHeader = 'Token ' + this.$store.state.apiToken
          axios.defaults.headers.common['Authorization'] = authHeader
          // Redirect to dashboard
          this.$router.push('/dashboard')
        } else {
          this.$swal({
            title: 'Email Not Confirmed!',
            text: 'You need to confirm your email before you can login.',
            icon: 'info',
            button: {
              text: 'OK',
              className: 'btn-primary',
              closeModal: true
            }
          }).then((value) => {
            window.location.href = '/'
          })
        }
      }).catch(e => {
        this.loginError = true
        this.formSubmitted = false
      })
    }
  },
  watch: {
    password: function () {
      this.loginError = false
      this.formSubmitted = false
    },
    username: function () {
      this.loginError = false
      this.formSubmitted = false
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