<template>
  <b-modal 
    id="signature-code-modal" 
    :title="$i18n.t('signature_code')" 
    ref="signatureCodeModal" centered hide-footer>
    <b-row>
      <b-col>
        <b-form-group id="signature-code">
          <b-form-textarea 
            id="signature-code-textarea"
            v-model.trim="signatureCode" 
            disabled
            :rows="3">
          </b-form-textarea>
        </b-form-group>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-button 
          v-clipboard="signatureCode" 
          @success="signatureCopySuccess">
          {{ $t('copy') }}
        </b-button>
      </b-col>
    </b-row>
  </b-modal>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SignatureCodeModal',
  data () {
    return {
      signatureCode: ''
    }
  },
  methods: {
    getSignatureCode (verificationCode) {
      let payload = {
        verificationCode: verificationCode,
        apiToken: this.$store.state.apiToken
      }
      axios.post('/get-signature-code/', payload).then(response => {
        if (response.data.success) {
          this.signatureCode = response.data.signature_code
        }
      })
    },
    signatureCopySuccess () {
      this.$swal({
        title: this.$t('copied_to_clipboard'),
        icon: 'success',
        button: {
          text: this.$t('ok'),
          className: 'btn-primary',
          closeModal: true
        }
      })
    }
  }
}
</script>