<template>
  <!-- Sign Up Modal -->
  <b-modal id='signup-modal' :title="$t('sign_up_form')" v-if="!$store.state.apiToken" ref="signUpModal" centered hide-footer>
    <b-form @submit="register($event)" @click="clearSignUpError()">
      <b-form-group :label="$t('email')">
        <b-form-input 
          v-model.trim="email" 
          v-validate="{ required: true, email: true, email_exists: true }" 
          :data-vv-as="$t('email')"
          name="email" :placeholder="$t('enter_email')">
        </b-form-input>
        <span v-show="errors.has('email')" class="help is-danger">
          {{ errors.first('email') }}
        </span>
      </b-form-group>
      <b-form-group :label="$t('username')">
        <b-form-input 
          v-model.trim="username" 
          :data-vv-as="$t('username')"
          v-validate="{ required: true, username_exists: true }" 
          name="username" :placeholder="$t('assign_username')"></b-form-input>
        <span v-show="errors.has('username')" class="help is-danger">
          {{ errors.first('username') }}
        </span>
      </b-form-group>
      <b-form-group :label="$t('password')">
        <b-form-input type="password" v-model.trim="password1" 
          v-validate="{ required: true, min: 6 }" 
          name="password1" 
          :data-vv-as="$t('password')" 
          :placeholder="$t('enter_password')">
        </b-form-input>
        <span v-show="errors.has('password1')" class="help is-danger">
          {{ errors.first('password1') }}
        </span>
      </b-form-group>
      <b-form-group :label="$t('retype_password')">
        <b-form-input type="password" 
          v-model.trim="password2" 
          v-validate="{ required: true, confirmed: 'password1' }" 
          name="password2" 
          :data-vv-as="$t('retyped_password')" 
          :placeholder="$t('retype_password')">
        </b-form-input>
        <span v-show="errors.has('password2')" class="help is-danger">
          {{ errors.first('password2') }}
        </span>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableSignUpSubmit">
          {{ $t('submit') }}
        </b-button>
        <span v-show="signUpError" class="help is-danger" style="margin-top: 15px;">
          {{ $t('signup_failed') }}
        </span>
      </b-form-group>
    </b-form>
  </b-modal>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SignUpModal',
  data () {
    return {
      username: '',
      email: '',
      password1: '',
      password2: '',
      signUpError: false
    }
  },
  computed: {
    disableSignUpSubmit () {
      return this.errors.any() || this.isFormPristine
    },
    isFormPristine () {
      return Object.keys(this.fields).some(key => this.fields[key].pristine)
    }
  },
  methods: {
    clearSignUpError () {
      this.signUpError = false
    },
    setUser (data) {
      this.$store.commit('updateApiToken', data.token)
      this.$store.commit('updateUser', data.username, data.email)
    },
    register (event) {
      event.preventDefault()
      let payload = {
        email: this.email,
        language: this.$i18n.locale,
        username: this.username,
        password: this.password1
      }
      axios.post('/create-user/', payload).then(response => {
        if (response.data.status === 'error') {
          this.signUpError = true
        } else {
          this.$swal({
            title: this.$t('email_confirmation'),
            text: this.$t('email_confirmation_msg'),
            icon: 'info',
            button: {
              text: this.$t('ok'),
              className: 'btn-primary'
            }
          }).then(() => {
            Object.assign(this.$data, this.$options.data.call(this))
            this.$validator.clean()
            this.$refs.signUpModal.hide()
          })
        }
      }).catch(e => {
        this.signUpError = true
      })
    }
  },
  created () {
    this.$validator.extend('email_exists', {
      getMessage: field => this.$t('email_exists'),
      validate: value => {
        let payload = {'email': value}
        return axios.post('/check-email-exists/', payload).then(response => {
          if (response.data.email_exists) {
            return false
          } else {
            return true
          }
        })
      }
    })
    this.$validator.extend('username_exists', {
      getMessage: field => this.$t('username_exists'),
      validate: value => {
        let payload = {'username': value}
        return axios.post('/check-username-exists/', payload).then(response => {
          if (response.data.username_exists) {
            return false
          } else {
            return true
          }
        })
      }
    })
  }
}
</script>