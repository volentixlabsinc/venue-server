<template>
  <div class="page-container">
    <b-row>
      <b-col>
        <h2>{{ $t('settings') }}</h2>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-card-group deck style="margin-top: 16px;">
          <b-card 
            header="VTX Wallet Address"
            header-tag="header">
            <p class="card-text">VTX address where to send payouts</p>
            <b-button disabled>
              Set VTX Address &nbsp;
              <b-badge variant="warning">Coming Soon</b-badge>
            </b-button>
          </b-card>
          <b-card 
            header="Email Address"
            header-tag="header">
            <p class="card-text">Change your registered email address</p>
            <b-button 
              variant="primary"
              v-b-modal.change-email-modal>
              Change Email
            </b-button>
          </b-card>
          <b-card 
            header="Account Username"
            header-tag="header">
            <p class="card-text">Change your username</p>
            <b-button 
              variant="primary" 
              v-b-modal.change-username-modal>
              Change Username
            </b-button>
          </b-card>
        </b-card-group>
        <b-card-group deck style="margin-top: 20px;">
          <b-card 
            header="Account Password"
            header-tag="header">
            <p class="card-text">Change your password</p>
            <b-button 
              variant="primary"
              v-b-modal.change-password-modal>
              Change Password
            </b-button>
          </b-card>
          <b-card 
            header="Language"
            header-tag="header">
            <p class="card-text">Set the site language</p>
            <b-form-group>
              <b-form-select v-model="language" :options="languages" class="mb-3"></b-form-select>
            </b-form-group>
          </b-card>
          <b-card 
            header="Two-Factor Authentication"
            header-tag="header">
            <p class="card-text">Enable two-factor authentication</p>
            <b-button disabled>
              Enable &nbsp;
              <b-badge variant="warning">Coming Soon</b-badge>
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
      language: this.$store.state.language,
      languages: [
        {value: 'en', text: 'English'},
        {value: 'fr', text: 'French'}
      ]
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
        title: 'First Confirmation',
        text: 'Are you sure you want to delete your account?',
        icon: 'warning',
        buttons: ['Cancel', 'Delete']
      }).then((value) => {
        if (value) {
          this.$swal({
            title: 'Second Confirmation',
            text: 'Please click on the link sent to your email to complete the deletion process.',
            icon: 'warning',
            buttons: ['Cancel', 'Ok']
          }).then((value) => {
            if (value) {
              var payload = { apiToken: this.$store.state.apiToken }
              axios.post('/delete-account/', payload)
            }
          })
        }
      })
    }
  }
}
</script>

<style scoped>

</style>