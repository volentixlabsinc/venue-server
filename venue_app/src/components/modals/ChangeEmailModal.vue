<template>
  <!-- Login Modal -->
  <b-modal 
    id="change-email-modal" 
    :title="$i18n.t('change_email_form')" 
    ref="changeEmailModal" centered hide-footer>
    <b-form @submit="changeEmail($event)">
      <b-form-group :label="$i18n.t('email')">
        <b-form-input v-model.trim="newEmail" 
          v-validate="{ required: true }" 
          name="email" 
          :data-vv-as="$t('email')"
          :placeholder="$store.state.userEmail">
        </b-form-input>
        <span v-show="errors.has('email')" class="help is-danger">
          {{ errors.first('email') }}
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
  name: 'ChangeEmailModal',
  data () {
    return {
      newEmail: '',
      formSubmitted: false
    }
  },
  methods: {
    changeEmail (event) {
      event.preventDefault()
      this.formSubmitted = true
      var payload = {
        email: this.newEmail,
        apiToken: this.$store.state.apiToken
      }
      axios.post('/change-email/', payload).then(response => {
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