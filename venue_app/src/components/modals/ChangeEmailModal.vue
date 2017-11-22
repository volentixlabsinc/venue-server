<template>
  <!-- Login Modal -->
  <b-modal 
    id="change-email-modal" 
    :title="$i18n.t('change_email_form')" 
    ref="changeEmailModal" centered hide-footer>
    <b-form @submit="changeEmail($event)">
      <b-form-group :label="$i18n.t('email')">
        <b-form-input v-model.trim="newEmail" v-validate="{ required: true }" name="email" :placeholder="$i18n.t('enter_new_email')"></b-form-input>
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
      console.log('Change email')
    }
  },
  computed: {
    disableSubmit () {
      return this.errors.any() || this.formSubmitted
    }
  }
}
</script>