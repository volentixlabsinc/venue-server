<template>
  <!-- Login Modal -->
  <b-modal 
    id="change-password-modal" 
    :title="$i18n.t('change_password_form')" 
    ref="changePasswordModal" centered hide-footer>
    <b-form @submit="changePassword($event)">
      <b-form-group :label="$i18n.t('password')">
        <b-form-input v-model.trim="newPassword1" type="password" v-validate="{ required: true, min: 6 }" name="password1" data-vv-as="password" :placeholder="$i18n.t('enter_new_password')"></b-form-input>
        <span v-show="errors.has('password1')" class="help is-danger">
          {{ errors.first('password1') }}
        </span>
      </b-form-group>
      <b-form-group :label="$i18n.t('retype_password')">
        <b-form-input v-model.trim="newPassword2" type="password" v-validate="{ required: true, confirmed: 'password1' }" name="password2" data-vv-as="retyped password" :placeholder="$i18n.t('retype_password')"></b-form-input>
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
import axios from 'axios'

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
      var payload = {
        apiToken: this.$store.state.apiToken,
        password: this.newPassword1
      }
      axios.post('/change-password/', payload).then(response => {
        if (response.data.success) {
          this.$refs.changePasswordModal.hide()
          this.$swal({
            title: 'Updated Password!',
            text: 'Your password has been successfully updated.',
            icon: 'success'
          }).then(() => {
            Object.assign(this.$data, this.$options.data.call(this))
            this.$validator.clean()
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