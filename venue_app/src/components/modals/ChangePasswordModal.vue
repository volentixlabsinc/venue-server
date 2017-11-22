<template>
  <!-- Login Modal -->
  <b-modal 
    id="change-password-modal" 
    :title="$i18n.t('change_password_form')" 
    ref="changePasswordModal" centered hide-footer>
    <b-form @submit="changePassword($event)">
      <b-form-group :label="$i18n.t('password')">
        <b-form-input v-model.trim="newPassword1" type="password" v-validate="{ required: true }" name="password1" :placeholder="$i18n.t('enter_new_password')"></b-form-input>
        <span v-show="errors.has('password1')" class="help is-danger">
          {{ errors.first('password1') }}
        </span>
      </b-form-group>
      <b-form-group :label="$i18n.t('retype_password')">
        <b-form-input v-model.trim="newPassword2" type="password" v-validate="{ required: true }" name="password2" :placeholder="$i18n.t('retype_password')"></b-form-input>
        <span v-show="errors.has('password2')" class="help is-danger">
          {{ errors.first('password2') }}
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
      newPassword1: '',
      newPassword2: '',
      formSubmitted: false
    }
  },
  methods: {
    changePassword (event) {
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