<template>
  <b-modal 
    id="two-factor-modal" 
    :title="$i18n.t('two_factor_auth')" 
    ref="twoFactorModal" centered hide-footer>
    <b-form @submit="disable2FA($event)" v-if="enabled2FA">
      <p>Are you sure you want to disable two-factor authentication?</p>
      <b-form-group>
        <b-button type="submit" variant="primary">{{ $t('yes') }}</b-button>
        <b-button variant="default" @click="cancel()">{{ $t('cancel') }}</b-button>
      </b-form-group>
    </b-form>
    <b-form @submit="verifyOtpCode($event)" v-if="!enabled2FA">
      <b-row>
        <b-col>
          <p>{{ $t('scan_with_2fa_app') }}</p>
          <div style="margin-bottom: 20px;">
            <qr-code :text="details.uri" :size="220"></qr-code>
          </div>
          <p>Or enter these details manually:</p>
          <p>
            <span><strong>Service:</strong></span>
            {{ details.service }}<br>
            <span><strong>Account:</strong></span>
            {{ details.account }}<br>
            <span><strong>Key:</strong></span>
            {{ details.key }}
          </p>
        </b-col>
      </b-row>
      <b-row style="margin-top: 10px;">
        <b-col>
          <b-form-group :label="$i18n.t('enter_otp_code')">
            <b-form-input v-model.trim="otpCode" 
              v-validate="{ required: true }" 
              :placeholder="$i18n.t('otp_code')">
            </b-form-input>
            <span v-show="wrongOtpCode" class="help is-danger">
              {{ $t('wrong_otp_code') }}
            </span>
          </b-form-group>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <b-form-group>
            <b-button type="submit" variant="primary" :disabled="disableSubmit">{{ $t('submit') }}</b-button>
            <img v-show="formSubmitted" src="../../assets/animated_spinner.gif" height="50">
          </b-form-group>
        </b-col>
      </b-row>
    </b-form>
  </b-modal>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TwoFactorModal',
  data () {
    return {
      details: null,
      otpCode: '',
      formSubmitted: false,
      wrongOtpCode: false
    }
  },
  computed: {
    disableSubmit () {
      if (this.otpCode.length > 0) {
        if (this.formSubmitted) {
          return true
        } else {
          return false
        }
      } else {
        return true
      }
    },
    enabled2FA () {
      return this.$store.state.enabledTwoFactor
    }
  },
  methods: {
    requestUri () {
      let vm = this
      axios.post('/manage/enable-two-factor-auth/').then(response => {
        vm.details = response.data
      })
    },
    verifyOtpCode (event) {
      let vm = this
      event.preventDefault()
      this.formSubmitted = true
      let payload = {
        otpCode: vm.otpCode,
        enable_2fa: true
      }
      axios.post('/verify-otp-code/', payload).then(response => {
        if (response.data.verified) {
          vm.$store.commit('updatedTwoFactorStatus', true)
          vm.$refs.twoFactorModal.hide()
          // Flash a sweet alert
          this.$swal({
            title: this.$t('two_factor_auth'),
            text: this.$t('two_factor_enabled'),
            icon: 'success',
            button: {
              text: this.$t('ok'),
              className: 'btn-primary',
              closeModal: true
            }
          })
        } else {
          this.formSubmitted = false
          this.wrongOtpCode = true
        }
      })
    },
    disable2FA (event) {
      let vm = this
      event.preventDefault()
      axios.post('/manage/disable-two-factor-auth/').then(response => {
        if (response.data.success) {
          // Update the global store variable
          vm.$store.commit('updatedTwoFactorStatus', false)
          // Close the modal
          this.$refs.twoFactorModal.hide()
          // Flash a sweet alert
          this.$swal({
            title: this.$t('two_factor_auth'),
            text: this.$t('two_factor_disabled'),
            icon: 'success',
            button: {
              text: this.$t('ok'),
              className: 'btn-primary',
              closeModal: true
            }
          })
        }
      })
    },
    cancel () {
      this.$refs.twoFactorModal.hide()
    }
  }
}
</script>