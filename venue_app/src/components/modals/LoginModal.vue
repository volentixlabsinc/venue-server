<template>
  <!-- Login Modal -->
  <b-modal id="login-modal" :title="$i18n.t('login_form')" v-if="!$store.state.apiToken" ref="loginModal" centered>
    <b-form @submit="login($event)" @click="clearLoginError()">
      <b-form-group :label="$i18n.t('username_or_email')">
        <b-form-input v-model.trim="username"
          :data-vv-as="$t('username') + '/' + $t('email')" 
          v-validate="{ required: true }" 
          name="username" 
          :placeholder="$i18n.t('enter_username_or_email')">
        </b-form-input>
        <span v-show="errors.has('username')" class="help is-danger">
          {{ errors.first('username') }}
        </span>
      </b-form-group>
      <b-form-group :label="$i18n.t('password')">
        <b-form-input type="password" 
          v-model.trim="password" 
          v-validate="{ required: true }" 
          :data-vv-as="$t('password')" 
          name="password" 
          :placeholder="$i18n.t('enter_password')">
        </b-form-input>
        <span v-show="errors.has('password')" class="help is-danger">
          {{ errors.first('password') }}
        </span>
      </b-form-group>
      <b-form-group v-if="showOtpInput" 
        :label="$i18n.t('two_factor_otp_code')">
        <b-form-input v-model.trim="otpCode"
          :placeholder="$i18n.t('otp_code')">
        </b-form-input>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableLoginSubmit">{{ $t('submit') }}</b-button>
        <img v-show="formSubmitted" src="../../assets/animated_spinner.gif" height="50">
        <span v-show="loginError" class="help is-danger" style="margin-top: 15px;">
          {{ localizedLoginError }}
        </span>
      </b-form-group>
    </b-form>
    <div slot="modal-footer" class="w-100">
      <p class="float-left" v-if="!resetPassswordMessage">
        <a @click="togglePasswordResetForm()" href="#">{{ $t('forgot_password') }}</a>
      </p>
      <b-alert v-if="resetPassswordMessage" show>{{ resetPassswordMessage }}</b-alert>
      <b-input-group v-if="showPasswordResetForm">
        <b-form-input type="email" v-model.trim="resetPasswordEmail" name="resetPasswordEmail" :placeholder="$i18n.t('enter_email')"></b-form-input>
        <b-input-group-button>
          <b-btn @click="resetPassword()" :disabled="!resetPasswordEmail.length">
            {{ $t('send_reset_link') }}
          </b-btn>
        </b-input-group-button>
      </b-input-group>
    </div>
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
      otpCode: '',
      showOtpInput: false,
      loginError: false,
      loginErrorCode: '',
      formSubmitted: false,
      showPasswordResetForm: false,
      resetPasswordEmail: '',
      resetPassswordMessage: ''
    }
  },
  computed: {
    disableLoginSubmit () {
      return this.errors.any() || this.formSubmitted || this.isFormPristine
    },
    isFormPristine () {
      return Object.keys(this.fields).some(key => this.fields[key].pristine)
    },
    localizedLoginError () {
      return this.$i18n.t(this.loginErrorCode)
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
      this.$store.commit('updateLanguage', data.language)
      this.$store.commit('updatedTwoFactorStatus', data.enabled_2fa)
    },
    login (event) {
      event.preventDefault()
      this.formSubmitted = true
      var payload = { username: this.username, password: this.password, otpCode: this.otpCode }
      axios.post('/authenticate/', payload).then(response => {
        if (response.data.success) {
          if (response.data.email_confirmed === true) {
            // Set user data
            this.password = ''
            this.setUser(response.data)
            // Fix the authorization header for all HTTP requests
            var authHeader = 'Token ' + this.$store.state.apiToken
            axios.defaults.headers.common['Authorization'] = authHeader
            // Set the localization
            this.$i18n.locale = response.data.language
            this.$validator.localize(response.data.language)
            // Refresh the login form
            Object.assign(this.$data, this.$options.data.call(this))
            this.$validator.clean()
            this.$refs.loginModal.hide()
            // Redirect to dashboard
            this.$router.push('/dashboard')
            // Load notifications by triggering an event in App.vue
            this.$parent.$parent.$emit('load-notifications')
          } else {
            this.$swal({
              title: this.$i18n.t('email_not_confirmed'),
              text: this.$i18n.t('confirm_email_notif'),
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
        } else {
          this.loginError = true
          this.formSubmitted = false
          this.loginErrorCode = response.data.error_code
          if (this.loginErrorCode === 'otp_required') {
            this.showOtpInput = true
          }
        }
      }, error => {
        console.log(error)
        this.loginError = true
        this.formSubmitted = false
        this.loginErrorCode = 'wrong_credentials'
      })
    },
    togglePasswordResetForm () {
      this.showPasswordResetForm = !this.showPasswordResetForm
    },
    resetPassword () {
      if (this.resetPasswordEmail) {
        var payload = {
          'email': this.resetPasswordEmail,
          'action': 'trigger'
        }
        axios.post('/reset-password/', payload).then(response => {
          if (response.data.success) {
            this.showPasswordResetForm = false
            this.resetPassswordMessage = this.$i18n.t('reset_password_notif')
          }
        })
      }
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
  }
}
</script>