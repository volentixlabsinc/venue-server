<template>
  <!-- Login Modal -->
  <b-modal id="change-username-modal" :title="$i18n.t('change_username_form')" ref="changeUsernameModal" centered hide-footer>
    <b-form @submit="changeUsername($event)">
      <b-form-group :label="$i18n.t('username')">
        <b-form-input v-model.trim="newUsername" v-validate="{ required: true }" name="username" :placeholder="$i18n.t('enter_new_username')"></b-form-input>
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
export default {
  name: 'ChangeUsernameModal',
  data () {
    return {
      newUsername: '',
      formSubmitted: false
    }
  },
  methods: {
    changeUsername (event) {
      event.preventDefault()
      this.formSubmitted = true
      console.log('Change username')
    }
  },
  computed: {
    disableSubmit () {
      return this.errors.any() || this.formSubmitted
    }
  }
}
</script>