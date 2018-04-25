<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col>
        <h2>{{ $t('signatures') }}</h2>
      </b-col>
      <b-col v-if="!showAddForm" style="text-align: right;">
        <b-button variant="primary" @click="addNewSignature(true)">
          {{ $t('add_new') }}
        </b-button>
      </b-col>
      <b-col v-if="showAddForm" v-show="mySignatures.length > 0" style="text-align: right;">
        <b-button @click="addNewSignature(false)">
          {{ $t('list_signatures') }}
        </b-button>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-form v-if="showAddForm">
          <h4>{{ $t('generate_signature') }}</h4>
          <b-row>
            <b-col md="7" sm="12">
              <b-form-group 
                id="forum-site-select-group" 
                :label="$t('forum_site') + ':'" 
                label-for="forum-site-select">
                <b-form-select id="forum-site-select"
                  :options="forumSites" 
                  v-model="forumSite">
                </b-form-select>
              </b-form-group>
              <b-form-group 
                id="profile-url" 
                :label="$t('url_or_userid') + ':'" label-for="profile-url-input">
                <b-form-input 
                  id="profile-url-input" 
                  name="profileUrl" 
                  type="text" v-model.trim="profileUrl" 
                  :data-vv-as="$t('enter_url_or_userid')"
                  :placeholder="$t('enter_url_or_userid')" 
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
                  {{ $t('check_profile') }}
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
                    {{ $t('copy') }}
                  </b-button>
                  <b-button 
                    :disabled="showVerifySpinner || signitureVerified" 
                    variant="primary" 
                    @click="verify()">
                    {{ $t('verify') }}
                  </b-button>
                  <img v-if="showVerifySpinner" src="../assets/animated_spinner.gif" height="50">
                </b-col>
              </b-row>
            </b-col>
          </b-row>
        </b-form>
      </b-col>
    </b-row>
    <b-row v-if='!showAddForm'>
      <b-col>
        <!-- List of current signatures -->
        <h4>{{ $t('your_current_signatures') }}</h4>
        <b-card-group class="card-group" v-for="signature in mySignatures" :key="signature.id">
          <b-card 
            :img-src="signature.image"
            img-alt="Signature"
            img-bottom>
            <b-row style="margin: 0; padding: 0;">
              <b-col sm="9" style="margin: 0; padding: 0;">
                <p class="card-text">
                  {{ $t('forum_site') }}: {{ signature.forum_site_name }} /
                  {{ $t('username') }}: {{ signature.forum_user_name }} /
                  {{ $t('user_id') }}: {{ signature.forum_userid }}
                </p>
              </b-col>
              <b-col sm="3" style="margin: 0; padding: 0;">
                <p style="text-align: right; cursor: pointer;">
                  <span @click="showSignatureCode(signature.verification_code)">
                    {{ $t('show_code') }}
                  </span>
                </p>
              </b-col>
            </b-row>
          </b-card>
        </b-card-group>
      </b-col>
    </b-row>
    <b-row v-show="profileChecked && showAddForm">
      <b-col id="signatures-list">
        <p>{{ $t('select_signature') }}:</p>
        <b-row v-for="signature in signatureOptions" :key="signature.id">
          <b-col>
            <h5>{{ signature.name }}</h5>
            <small>Usage count: {{ signature.usage_count }}</small>
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
    
    <signature-code-modal ref="signatureCode"></signature-code-modal>
  </div>
</template>

<script>
import SignatureCodeModal from '@/components/modals/SignatureCodeModal'
import axios from 'axios'

export default {
  name: 'Signatures',
  components: { SignatureCodeModal },
  data () {
    return {
      showPage: false,
      initial: false,
      showAddForm: false,
      forumSite: 1,
      forumSites: [],
      signatureOptions: [],
      mySignatures: [],
      selectedSignature: null,
      profileUrl: '',
      profileChecked: false,
      signitureVerified: false,
      forumUserPosition: '',
      showCheckSpinner: false,
      showVerifySpinner: false,
      forumProfileId: null,
      disableListButton: false
    }
  },
  methods: {
    // Gets signatures for the given forum site
    getSignatures (forumId, forumUserRank, forumProfileId) {
      var params = {
        'forum_site_id': forumId,
        'forum_user_rank': forumUserRank,
        'forum_profile_id': forumProfileId
      }
      axios.get('/retrieve/signatures/', {params: params}).then(response => {
        this.signatureOptions = response.data.signatures
      })
    },
    signatureCopySuccess () {
      this.$swal({
        title: this.$t('copied_to_clipboard'),
        text: this.$t('copied_to_clipboard_msg'),
        icon: 'success',
        button: {
          text: this.$t('verify'),
          className: 'btn-primary',
          closeModal: true
        }
      }).then(() => {
        this.verify()
      })
    },
    flashCheckProfileError (vueThis) {
      this.$swal({
        title: this.$t('checking_error'),
        text: this.$t('checking_error_msg'),
        icon: 'error',
        button: {
          text: this.$t('ok'),
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
        title: this.$t('profile_already_exists'),
        text: message,
        icon: 'error',
        button: {
          text: this.$t('ok'),
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
      var params = {
        forum: this.forumSite,
        profile_url: this.profileUrl
      }
      axios.get('/check/profile/', {params: params}).then(response => {
        var self = this // To refer to `this` that's bound to vue instance
        if (response.data.status_code === 200) {
          if (response.data.found === true) {
            this.forumUserPosition = response.data.position
            this.forumProfileId = response.data.forum_profile_id
            this.showCheckSpinner = false
            if (response.data.exists === true) {
              if (response.data.verified === true) {
                if (response.data.own === true) {
                  if (response.data.with_signature === true) {
                    if (response.data.active) {
                      this.flashAlreadyExistsNotice(self, this.$t('profile_already_exists_msg1'))
                    } else {
                      this.getSignatures(
                        this.forumSite,
                        this.forumUserPosition,
                        response.data.forum_profile_id
                      )
                      this.profileChecked = true
                    }
                  }
                } else {
                  this.flashAlreadyExistsNotice(self, this.$t('profile_already_exists_msg2'))
                }
              } else {
                // Create the forum profile
                var params = {
                  forum_id: response.data.forum_id,
                  forum_user_id: response.data.forum_user_id
                }
                let vm = self
                axios.get('/retrieve/forum-profiles/', {params: params}).then(response => {
                  if (response.data.success) {
                    vm.profileChecked = true
                    vm.forumProfileId = response.data.forum_profiles[0].id
                    vm.getSignatures(vm.forumSite, vm.forumUserPosition, vm.forumProfileId)
                  }
                })
              }
            } else {
              if (response.data.position_allowed) {
                this.profileChecked = true
                // Create the forum profile
                var payload = {
                  profile_url: this.profileUrl,
                  forum_id: this.forumSite
                }
                axios.post('/create/forum-profile/', payload).then(response => {
                  if (response.data.success) {
                    this.forumProfileId = response.data.id
                    this.getSignatures(this.forumSite, this.forumUserPosition, response.data.id)
                  }
                })
              } else {
                this.$swal({
                  title: this.$t('insufficient_rank'),
                  text: this.$t('insufficient_rank_msg'),
                  icon: 'error'
                })
              }
            }
          } else {
            this.$swal({
              title: this.$t('does_not_exist'),
              text: this.$t('does_not_exist_msg'),
              icon: 'error',
              button: {
                text: this.$t('ok'),
                className: 'btn-primary',
                closeModal: true
              }
            }).then(() => {
              self.showCheckSpinner = false
              self.$refs['check-button'].attr('disabled', false)
            })
          }
        } else {
          this.flashCheckProfileError(this)
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
      axios.post('/create/signature/', payload).then(response => {
        this.showVerifySpinner = false
        if (response.status === 200) {
          if (response.data.success === true) {
            this.$swal({
              title: this.$t('signature_placement_verified'),
              text: this.$t('signature_placement_verified_msg'),
              icon: 'success',
              button: {
                text: this.$t('ok'),
                className: 'btn-primary',
                closeModal: true
              }
            }).then(() => {
              window.location.href = '/#/dashboard'
            })
            this.signitureVerified = true
          } else {
            this.$swal({
              title: this.$t('signature_not_found'),
              text: this.$t('signature_not_found_msg'),
              icon: 'error',
              button: {
                text: 'OK',
                className: 'btn-primary',
                closeModal: true
              }
            })
          }
        }
      }).catch(error => {
        this.showVerifySpinner = false
        var alreadyExists = error.response.data[0].includes('already contains')
        if (error.response.status === 400 && alreadyExists) {
          this.$swal({
            title: this.$t('already_onboard'),
            text: this.$t('already_onboard_msg'),
            icon: 'info',
            button: {
              text: this.$t('ok'),
              className: 'btn-primary',
              closeModal: true
            }
          })
        }
        var signatureNotFound = error.response.data[0].includes('signature was not found')
        if (error.response.status === 400 && signatureNotFound) {
          this.$swal({
            title: this.$t('verification_failed'),
            text: error.response.data[0],
            icon: 'error',
            button: {
              text: this.$t('ok'),
              className: 'btn-primary',
              closeModal: true
            }
          })
        }
      })
    },
    addNewSignature (value) {
      this.showAddForm = value
    },
    showSignatureCode (verificationCode) {
      this.$refs.signatureCode.getSignatureCode(verificationCode)
      this.$refs.signatureCode.$refs.signatureCodeModal.show()
    }
  },
  computed: {
    signatureCode () {
      var sigId = this.selectedSignature
      return this.signatureOptions.filter(function (sig) {
        return sig.id === sigId
      })[0].code
    }
  },
  watch: {
    forumSite: function (newForumSite) {
      this.selectedSignature = null
      this.profileChecked = false
      this.profileUrl = ''
      this.$validator.clean()
    },
    selectedSignature: function (newSig) {
      if (newSig !== null) {
        this.$validator.validateAll()
      }
    }
  },
  created () {
    this.$Progress.start()
    // Check if it's the user first time to generate a signature
    this.initial = this.$route.query.initial
    this.showAddForm = this.$route.query.initial
    // Get forum sites
    let vm = this
    axios.get('/retrieve/forum-sites/').then(response => {
      for (var elem of response.data.forum_sites) {
        vm.forumSites.push({value: elem.id, text: elem.name})
      }
      vm.showPage = true
      vm.$Progress.finish()
    })
    // Get my signatures
    var params = { 'own_sigs': 1 }
    axios.get('/retrieve/signatures/', {params: params}).then(response => {
      this.mySignatures = response.data.signatures
      this.showPage = true
      this.$Progress.finish()
      console.log(this.mySignatures)
    })
  },
  beforeRouteLeave (to, from, next) {
    if (this.profileUrl && this.profileChecked && !this.signitureVerified) {
      this.$swal({
        title: this.$t('page_change_confirmation'),
        text: this.$t('page_change_confirmation_msg'),
        icon: 'warning',
        buttons: [this.$t('cancel'), this.$t('yes')]
      }).then((yes) => {
        if (yes) {
          next()
        }
      })
    } else {
      next()
    }
  },
  updated () {
    this.$nextTick(function () {
      if (document.body.offsetHeight <= window.innerHeight) {
        this.$store.commit('updateShowFooter', true)
      } else {
        this.$store.commit('updateShowFooter', false)
      }
    })
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
  .card-group {
    margin-top: 20px;
  }
</style>
