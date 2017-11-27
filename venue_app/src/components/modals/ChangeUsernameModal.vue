<template>
  <!-- Login Modal -->
  <b-modal id="change-username-modal" :title="$i18n.t('change_username_form')" ref="changeUsernameModal" centered hide-footer>
    <b-form @submit="changeUsername($event)">
      <b-form-group :label="$i18n.t('username')">
        <b-form-input v-model.trim="newUsername" v-validate="{ required: true }" name="username" :placeholder="$store.state.userName"></b-form-input>
        <span v-show="errors.has('username')" class="help is-danger">
          {{ errors.first('username') }}
        </span>
      </b-form-group>
      <b-form-group>
        <b-button type="submit" variant="primary" :disabled="disableSubmit">{{ $t('submit') }}</b-button>
        <img v-show="formSubmitted" src="../../assets/animated_spinner.gif" height="50">
      </b-form-group>
    </b-form>
  </b-modal>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ChangeUsernameModal',
  data () {
    return {
      newUsername: null,
      formSubmitted: false
    }
  },
  methods: {
    changeUsername (event) {
      event.preventDefault()
      this.formSubmitted = true
      var payload = {
        username: this.newUsername,
        apiToken: this.$store.state.apiToken
      }
      axios.post('/change-username/', payload).then(response => {
        if (response.data.success) {
          var data = response.data
          this.$store.commit('updateUserName', data.username)
          this.$store.commit('updateUserEmail', data.email)
          this.$refs.changeUsernameModal.hide()
          this.$swal({
            title: 'Updated Username!',
            text: 'Your username has been successfully updated.',
            icon: 'success'
          }).then(() => {
            Object.assign(this.$data, this.$options.data.call(this))
            this.$validator.clean()
          })
        } else {
          this.$swal({
            title: 'Update Error!',
            text: response.data.message,
            icon: 'error'
          }).then(() => {
            this.formSubmitted = false
          })
        }
      })
    }
  },
  computed: {
    disableSubmit () {
      return this.errors.any() || this.formSubmitted || this.isFormPristine
    },
    isFormPristine () {
      return Object.keys(this.fields).some(key => this.fields[key].pristine)
    }
  }
}
</script>