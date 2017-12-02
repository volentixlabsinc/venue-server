<template>
  <!-- Reset Password Modal -->
  <b-modal 
    id="signature-code-modal" 
    :title="$i18n.t('signature_code')" 
    ref="signatureCodeModal" centered hide-footer>
    <p>Signature code goes here</p>
  </b-modal>
</template>

<script>
export default {
  name: 'SignatureCodeModal',
  data () {
    return {
      verificationCode: ''
    }
  },
  created () {
    console.log('signature code modal shown: ' + this.verificationCode)
  }
}
</script>