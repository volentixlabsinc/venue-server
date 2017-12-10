<template>
  <!-- Sign Up Modal -->
  <b-modal id='signup-modal' :title="$i18n.t('sign_up_form')" v-if="!$store.state.apiToken" ref="signUpModal" centered hide-footer>
    <b-form @submit="register($event)" @click="clearSignUpError()">
      <b-form-group :label="$i18n.t('email')">
        <b-form-input v-model.trim="email" v-validate="{ required: true, email: true }" name="email" :placeholder="$i18n.t('enter_email')"></b-form-input>
        <span v-show="errors.has('email')" class="help is-danger">
          {{ errors.first('email') }}
        </span>
      </b-form-group>
      <b-form-group label="Username">
        <b-form-input v-model.trim="username" v-validate="{ required: true }" name="email" placeholder="Assign a username"></b-form-input>
        <span v-show="errors.has('username')" class="help is-danger">
          {{ errors.first('username') }}
        </span>
      </b-form-group>
      <b-form-group :label="$i18n.t('password')">
        <b-form-input type="password" v-model.trim="password1" v-validate="{ required: true, min: 6 }" name="password1" data-vv-as="password" :placeholder="$i18n.t('enter_password')"></b-form-input>
        <span v-show="errors.has('password1')" class="help is-danger">
          {{ errors.first('password1') }}
        </span>
      </b-form-group>
      <b-form-group label="Retype Password">
        <b-form-input type="password" v-model.trim="password2" v-validate="{ required: true, confirmed: 'password1' }" name="password2" data-vv-as="retyped password" placeholder="Retype password"></b-form-input>
        <span v-show="errors.has('password2')" class="help is-danger">
          {{ errors.first('password2') }}
        </span>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableSignUpSubmit">
          {{ $t('submit') }}
        </b-button>
        <span v-show="signUpError" class="help is-danger" style="margin-top: 15px;">
          Sign up failed: A problem was encountered!
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
  watch: {
    email: function (newEmail) {
      this.username = newEmail.split('@')[0]
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
      console.log(payload)
      axios.post('/create-user/', payload).then(response => {
        if (response.data.status === 'error') {
          this.signUpError = true
        } else {
          this.$swal({
            title: 'Email Confirmation Required!',
            text: 'Please click on the link in the confirmation email we sent.',
            icon: 'info',
            button: {
              text: 'OK',
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
  }
}
</script>