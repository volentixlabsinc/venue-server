<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col>
        <h2>{{ $t('settings') }}</h2>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-card-group deck style="margin-top: 16px;">
          <b-card 
            :header="$t('vtx_address')"
            header-tag="header">
            <p class="card-text">{{ $t('vtx_address_payout') }}</p>
            <b-button disabled>
              {{ $t('set_vtx_address')}} &nbsp;
              <b-badge variant="warning">{{ $t('coming_soon') }}</b-badge>
            </b-button>
          </b-card>
          <b-card 
            :header="$t('email_address')"
            header-tag="header">
            <p class="card-text">{{ $t('change_your_email') }}</p>
            <b-button 
              variant="primary"
              v-b-modal.change-email-modal>
              {{ $t('change_email') }}
            </b-button>
          </b-card>
          <b-card 
            :header="$t('account_username')"
            header-tag="header">
            <p class="card-text">{{ $t('change_your_username') }}</p>
            <b-button 
              variant="primary" 
              v-b-modal.change-username-modal>
              {{ $t('change_username') }}
            </b-button>
          </b-card>
        </b-card-group>
        <b-card-group deck style="margin-top: 20px;">
          <b-card 
            :header="$t('account_password')"
            header-tag="header">
            <p class="card-text">{{ $t('change_your_password') }}</p>
            <b-button 
              variant="primary"
              v-b-modal.change-password-modal>
              {{ $t('change_password') }}
            </b-button>
          </b-card>
          <b-card 
            :header="$t('language')"
            header-tag="header">
            <p class="card-text">{{ $t('set_language') }}</p>
            <b-form-group>
              <b-form-select v-model="language" :options="languages" class="mb-3"></b-form-select>
            </b-form-group>
          </b-card>
          <b-card 
            :header="$t('two_factor_auth')"
            header-tag="header">
            <p class="card-text">{{ $t('enable_2fa') }}</p>
            <b-button disabled>
              {{ $t('enable') }} &nbsp;
              <b-badge variant="warning">{{ $t('coming_soon') }}</b-badge>
            </b-button>
          </b-card>
          <!--
          <b-card 
            header="Delete Account"
            header-tag="header">
            <p class="card-text">Delete your account permanently</p>
            <b-button variant="danger" @click="deleteAccount()">Delete</b-button>
          </b-card>
          -->
        </b-card-group>
      </b-col>
    </b-row>
    
    <change-email-modal></change-email-modal>
    <change-username-modal></change-username-modal>
    <change-password-modal></change-password-modal>
    <delete-account-modal></delete-account-modal>
  </div>
</template>

<script>
import ChangeEmailModal from '@/components/modals/ChangeEmailModal'
import ChangeUsernameModal from '@/components/modals/ChangeUsernameModal'
import ChangePasswordModal from '@/components/modals/ChangePasswordModal'
import axios from 'axios'

export default {
  name: 'Settings',
  components: {
    ChangeEmailModal,
    ChangeUsernameModal,
    ChangePasswordModal
  },
  data () {
    return {
      showPage: false,
      language: this.$store.state.language,
      languages: this.$store.state.languages
    }
  },
  watch: {
    language: function (newLanguage) {
      this.$Progress.start()
      this.$store.commit('updateLanguage', newLanguage)
      let payload = {
        apiToken: this.$store.state.apiToken,
        language: this.language
      }
      axios.post('/change-language/', payload).then((response) => {
        if (response.data.success) {
          this.$i18n.locale = newLanguage
          this.$Progress.finish()
        }
      })
    }
  },
  methods: {
    deleteAccount () {
      this.$swal({
        title: this.$t('first_confirmation'),
        text: this.$t('first_confirmation_msg'),
        icon: 'warning',
        buttons: [this.$t('cancel'), this.$t('delete')]
      }).then((value) => {
        if (value) {
          this.$swal({
            title: this.$t('second_confirmation'),
            text: this.$t('second_confirmation_msg'),
            icon: 'warning',
            buttons: [this.$t('cancel'), this.$t('ok')]
          }).then((value) => {
            if (value) {
              var payload = { apiToken: this.$store.state.apiToken }
              axios.post('/delete-account/', payload)
            }
          })
        }
      })
    }
  },
  created () {
    this.$Progress.start()
    axios.post('/get-wallet-details/').then(response => {
      this.showPage = true
      this.$Progress.finish()
    })
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

</style>