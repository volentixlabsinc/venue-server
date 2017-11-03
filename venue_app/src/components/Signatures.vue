<template>
  <div class="page-container">
    <b-row>
      <b-col>
        <h2>{{ $t('signatures') }}</h2>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-form>
          <b-row>
            <b-col md="6" sm="12">
              <b-form-group 
                id="forum-site-select-group" 
                label="Forum site:" 
                label-for="forum-site-select">
                <b-form-select id="forum-site-select"
                  :options="forumSites" 
                  v-model="forumSite">
                </b-form-select>
              </b-form-group>
              <b-form-group 
                id="profile-url" 
                label="Profile URL:" label-for="profile-url-input">
                <b-form-input 
                  id="profile-url-input" 
                  name="profileUrl" 
                  type="text" v-model.trim="profileUrl" 
                  placeholder="Enter forum profile URL" 
                  data-vv-as="profile URL" 
                  :class="{'input': true, 'is-danger': errors.has('profileUrl') }" 
                  v-validate="{ required: true, url: true }"
                  @blur.native="$validator.validateAll()">
                </b-form-input>
                <span v-show="errors.has('profileUrl')" class="help is-danger">
                  {{ errors.first('profileUrl') }}
                </span>
              </b-form-group>
            </b-col>
            <b-col v-if="selectedSignature && !errors.has('profileUrl')">
              <b-row>
                <b-col>
                  <b-form-group 
                    id="signature-code" 
                    label="Signature Code:" label-for="signature-code-textarea">
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
                    Copy
                  </b-button>
                  <b-button variant="primary" @click="verify()">Verify</b-button>
                </b-col>
              </b-row>
            </b-col>
          </b-row>
        </b-form>
      </b-col>
    </b-row>
    <b-row>
      <b-col id="signatures-list">
        <b-row v-for="signature in signatures">
          <b-col>
            <h5>{{ signature.name }}</h5>
            <div class="sig-select-div">
              <input type="radio" 
                class="sig-select" 
                v-model="selectedSignature"
                :value="signature.id">
            </div>
            <div class="signature-banner">
              <img :src="signature.image">
            </div>
          </b-col>
        </b-row>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Signatures',
  data () {
    return {
      forumSite: 1,
      forumSites: [],
      signatures: [],
      selectedSignature: null,
      profileUrl: ''
    }
  },
  methods: {
    getSignatures (forumId) {
      // Get signatures for the default forum site
      axios.get('/api/signatures/?forum_site_id=' + forumId).then(response => {
        this.signatures = response.data
      })
    },
    signatureCopySuccess () {
      this.$swal({
        title: 'Copied to clipboard!',
        text: 'Paste the copied code to your profile signature.',
        icon: 'success',
        button: {
          text: 'OK',
          className: 'btn-primary',
          closeModal: true
        }
      })
    },
    verify () {
      var payload = {
        profile_url: this.profileUrl,
        signature_id: this.selectedSignature,
        forum_id: this.forumSite
      }
      axios.post('/api/forum-profiles/', payload).then(response => {
        if (response.status === 201) {
          this.$swal({
            title: 'Signature update verified!',
            text: 'Live stats are displayed on your dashboard.',
            icon: 'success',
            button: {
              text: 'OK',
              className: 'btn-primary',
              closeModal: true
            }
          })
        }
      }).catch(error => {
        var alreadyExists = error.response.data[0].includes('already contains')
        if (error.response.status === 400 && alreadyExists) {
          this.$swal({
            title: 'Already Onboard!',
            text: error.response.data[0],
            icon: 'info',
            button: {
              text: 'OK',
              className: 'btn-primary',
              closeModal: true
            }
          })
        }
        var signatureNotFound = error.response.data[0].includes('signature was not found')
        if (error.response.status === 400 && signatureNotFound) {
          this.$swal({
            title: 'Verification Failed!',
            text: error.response.data[0],
            icon: 'error',
            button: {
              text: 'OK',
              className: 'btn-primary',
              closeModal: true
            }
          })
        }
      })
    }
  },
  computed: {
    signatureCode () {
      var sigId = this.selectedSignature
      return this.signatures.filter(function (sig) {
        return sig.id === sigId
      })[0].code
    }
  },
  watch: {
    forumSite: function (newForumSite) {
      this.getSignatures(newForumSite)
      this.selectedSignature = null
    },
    selectedSignature: function (newSig) {
      if (newSig !== null) {
        this.$validator.validateAll()
      }
    }
  },
  created () {
    // Get forum sites
    axios.get('/api/forum-sites/').then(response => {
      for (var elem of response.data) {
        this.forumSites.push({value: elem.id, text: elem.name})
      }
    })
    this.getSignatures(this.forumSite)
  }
}
</script>

<style scoped>
  .signature-banner {
    padding-bottom: 10px;
    padding-left: 30px;
    margin-top: -20px;
  }
  input.sig-select {
    position: relative;
    top: 18px;
  }
  #signatures-list {
    padding-top: 10px;
  }
  input.is-danger {
    border:1px solid red;
  }
</style>