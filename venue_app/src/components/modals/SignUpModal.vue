<template>
  <!-- Sign Up Modal -->
  <b-modal id='signup-modal' title="Sign Up Form" v-if="!$store.state.apiToken" ref="signUpModal" hide-footer>
    <b-form @submit="register($event)" @click="clearSignUpError()">
      <b-form-group label="Email">
        <b-form-input v-model.trim="email" v-validate="{ required: true, email: true }" name="email" placeholder="Enter email address"></b-form-input>
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
      <b-form-group label="Password">
        <b-form-input type="password" v-model.trim="password1" v-validate="{ required: true }" name="password1" placeholder="Enter password"></b-form-input>
        <span v-show="errors.has('password1')" class="help is-danger">
          {{ errors.first('password1') }}
        </span>
      </b-form-group>
      <b-form-group label="Retype Password">
        <b-form-input type="password" v-model.trim="password2" v-validate="{ required: true, confirmed: 'password1' }" name="password2" placeholder="Retype password"></b-form-input>
        <span v-show="errors.has('password2')" class="help is-danger">
          {{ errors.first('password2') }}
        </span>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableSignUpSubmit">Submit</b-button>
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
      return this.errors.any()
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
      axios.post('/create-user/', {
        email: this.email,
        username: this.username,
        password: this.password1
      }).then(response => {
        if (response.data.status === 'error') {
          this.signUpError = true
        } else {
          this.setUser(response.data.user)
          this.$router.push('/dashboard')
        }
      }).catch(e => {
        this.signUpError = true
      })
    }
  }
}
</script>