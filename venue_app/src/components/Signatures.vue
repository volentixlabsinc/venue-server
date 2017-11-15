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
                label="Profile URL or Forum User ID:" label-for="profile-url-input">
                <b-form-input 
                  id="profile-url-input" 
                  name="profileUrl" 
                  type="text" v-model.trim="profileUrl" 
                  placeholder="Enter forum profile URL or forum user ID" 
                  data-vv-as="profile URL" 
                  :disabled="showCheckSpinner || profileChecked" 
                  :class="{'input': true, 'is-danger': errors.has('profileUrl')}" 
                  v-validate="{ required: true }"
                  @blur.native="$validator.validateAll()">
                </b-form-input>
                <span id="profile-found-notice" v-if="profileChecked">Profile found!</span>
                <span v-show="errors.has('profileUrl')" class="help is-danger">
                  {{ errors.first('profileUrl') }}
                </span>
              </b-form-group>
              <b-form-group>
                <b-button 
                  ref="check-button" 
                  variant="primary" 
                  @click="checkProfile()" 
                  v-if="!profileChecked" 
                  :disabled="profileUrl.length == 0 || errors.has('profileUrl') || showCheckSpinner">
                  Check Profile
                </b-button>
                <img v-if="showCheckSpinner" src="../assets/animated_spinner.gif" height="50">
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
                  <b-button 
                    :disabled="showVerifySpinner || signitureVerified" 
                    variant="primary" 
                    @click="verify()">
                    Verify
                  </b-button>
                  <img v-if="showVerifySpinner" src="../assets/animated_spinner.gif" height="50">
                </b-col>
              </b-row>
            </b-col>
          </b-row>
        </b-form>
      </b-col>
    </b-row>
    <b-row v-if="profileChecked">
      <b-col id="signatures-list">
        <p>Select signature:</p>
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
      profileUrl: '',
      profileChecked: false,
      signitureVerified: false,
      forumUserPosition: '',
      showCheckSpinner: false,
      showVerifySpinner: false,
      forumProfileId: null
    }
  },
  methods: {
    // Gets signatures for the given forum site
    getSignatures (forumId) {
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
    flashCheckProfileError (vueThis) {
      this.$swal({
        title: 'Checking error!',
        text: 'The forum site is inaccessible or profile URL is wrong.',
        icon: 'error',
        button: {
          text: 'OK',
          className: 'btn-primary',
          closeModal: true
        }
      }).then(() => {
        vueThis.showCheckSpinner = false
        vueThis.$refs['check-button'].attr('disabled', false)
      })
    },
    flashAlreadyExistsNotice (vueThis, message) {
      this.$swal({
        title: 'Profile Already Exists!',
        text: message,
        icon: 'warning',
        button: {
          text: 'OK',
          className: 'btn-primary',
          closeModal: true
        }
      }).then(() => {
        vueThis.showCheckSpinner = false
        vueThis.$refs['check-button'].attr('disabled', false)
      })
    },
    checkProfile () {
      this.showCheckSpinner = true
      var payload = {
        forum: this.forumSite,
        profile_url: this.profileUrl
      }
      axios.post('/check-profile/', payload).then(response => {
        var self = this // To refer to `this` that's bound to vue instance
        console.log(response.data)
        if (response.data.status_code === 200) {
          if (response.data.found === true) {
            this.forumUserPosition = response.data.position
            this.forumProfileId = response.data.forum_profile_id
            this.showCheckSpinner = false
            if (response.data.exists === true) {
              if (response.data.own === true) {
                if (response.data.with_signature === true) {
                  this.flashAlreadyExistsNotice(self, 'You already placed a signature on that profile.')
                }
              } else {
                this.flashAlreadyExistsNotice(self, 'Somebody else already claimed that profile.')
              }
            } else {
              this.profileChecked = true
              // Create the forum profile
              var payload = {
                profile_url: this.profileUrl,
                forum_id: this.forumSite
              }
              axios.post('/api/forum-profiles/', payload).then(response => {
                this.forumProfileId = response.data.id
              })
            }
          } else {
            this.$swal({
              title: 'Does not exist!',
              text: 'The profile does not exist in the selected forum site.',
              icon: 'error',
              button: {
                text: 'OK',
                className: 'btn-primary',
                closeModal: true
              }
            }).then(() => {
              self.showCheckSpinner = false
              self.$refs['check-button'].attr('disabled', false)
            })
          }
        } else {
          this.flashCheckProfileError()
        }
      }).catch(error => {
        console.log(error.response.data)
        this.flashCheckProfileError(this)
      })
    },
    verify () {
      this.showVerifySpinner = true
      var payload = {
        signature_id: this.selectedSignature,
        forum_profile_id: this.forumProfileId
      }
      axios.post('/save-signature/', payload).then(response => {
        this.showVerifySpinner = false
        if (response.status === 200) {
          this.$swal({
            title: 'Signature placement verified!',
            text: 'Thank you for participating in our signature campaign.',
            icon: 'success',
            button: {
              text: 'OK',
              className: 'btn-primary',
              closeModal: true
            }
          }).then(() => {
            window.location.href = '/#/dashboard'
          })
          this.signitureVerified = true
        }
      }).catch(error => {
        this.showVerifySpinner = false
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
  #signatures-list p {
    font-size: 1rem;
  }
  #profile-found-notice {
    color: green;
  }
  input.is-danger {
    border:1px solid red;
  }
</style>