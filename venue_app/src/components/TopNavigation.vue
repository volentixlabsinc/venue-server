<template>
  <div class="topnav">
    <b-navbar toggleable="md" type="dark" variant="dark" class="bg-dark">
      
      <b-nav-toggle target="nav_collapse"></b-nav-toggle>
      
      <b-navbar-brand style="font-size: 26px;" href="/">
        VENUE
      </b-navbar-brand>
      
      <b-collapse is-nav id="nav_collapse">
        
        <b-navbar-nav class="ml-auto">
          
          <b-nav-item-dropdown v-if="!$store.state.apiToken" :text="$t('language')" right>
            <b-dropdown-item  
              v-for="lang in languages" :key="lang.value"
              @click="setLanguage(lang.value)">
              {{ lang.text }}
            </b-dropdown-item>
          </b-nav-item-dropdown>

          <b-nav-item v-if="$store.state.apiToken" to="/dashboard" exact>
            {{ $t('dashboard') }}
          </b-nav-item>
          
          <b-nav-item to="/leaderboard">
            {{ $t('leaderboard') }}
          </b-nav-item>

          <b-nav-form>
            <b-button size="sm" 
              class="my-2 my-sm-0" 
              v-b-modal.login-modal v-if="!$store.state.apiToken">
              {{ $t('login') }}
            </b-button>
          </b-nav-form>
          
          <b-nav-item v-if="$store.state.apiToken" to="/signatures">
            {{ $t('signatures') }}
          </b-nav-item>

          <b-nav-item-dropdown right v-if="$store.state.apiToken">
            <template slot="button-content">
              {{ username }}
            </template>
            <b-dropdown-item to="/settings">{{ $t('settings') }}</b-dropdown-item>
            <b-dropdown-item @click="logout()" href="#">{{ $t('logout') }}</b-dropdown-item>
          </b-nav-item-dropdown>
        </b-navbar-nav>
      </b-collapse>
    </b-navbar>
    
    <login-modal></login-modal>
    <reset-password-modal ref="resetPassword"></reset-password-modal>
    
  </div>
</template>

<script>
import LoginModal from '@/components/modals/LoginModal'
import ResetPasswordModal from '@/components/modals/ResetPasswordModal'
import axios from 'axios'

export default {
  name: 'TopNavigation',
  components: { LoginModal, ResetPasswordModal },
  data () {
    return {
      languages: this.$store.state.languages
    }
  },
  methods: {
    logout () {
      this.$store.commit('updateApiToken', '')
      this.$store.commit('updateUserEmail', null)
      this.$store.commit('updateUserName', null)
      delete axios.defaults.headers.common['Authorization']
      this.$router.push('/')
    },
    setLanguage (lang) {
      this.$i18n.locale = lang
      this.$validator.localize(lang)
    },
    setUser (data) {
      this.$store.commit('updateApiToken', data.token)
      this.$store.commit('updateUserName', data.username)
      this.$store.commit('updateUserEmail', data.email)
    }
  },
  computed: {
    username () {
      return this.$store.state.userName
    }
  },
  created () {
    // Get langauge options
    axios.get('/get-languages/').then(response => {
      this.$store.commit('setLanguageOptions', response.data)
    })
    // Get user details
    if (this.$store.state.apiToken) {
      axios.post('/get-user/', {
        token: this.$store.state.apiToken
      }).then(response => {
        if (response.data.found === true) {
          this.setUser(response.data)
          // Localize to selected language
          this.$i18n.locale = this.$store.state.language
        }
      })
    }
    if (this.$route.query.email_confirmed === '1') {
      this.$swal({
        title: this.$t('email_confirmed'),
        text: this.$t('email_confirmed_msg'),
        icon: 'success',
        button: {
          text: this.$t('ok'),
          className: 'btn-primary',
          closeModal: true
        }
      })
    }
    if (this.$route.query.account_deleted === '1') {
      this.$swal({
        title: this.$t('account_deleted'),
        text: this.$t('account_deleted_msg'),
        icon: 'success',
        button: {
          text: this.$t('ok'),
          className: 'btn-primary',
          closeModal: true
        }
      }).then(() => {
        this.logout()
      })
    }
    if (this.$route.query.updated_email === '1') {
      this.$swal({
        title: this.$t('updated_email'),
        text: this.$t('updated_email_msg'),
        icon: 'success',
        button: {
          text: this.$t('ok'),
          className: 'btn-primary',
          closeModal: true
        }
      })
    }
  },
  mounted () {
    if (this.$route.query.reset_password === '1') {
      this.$refs.resetPassword.$refs.resetPasswordModal.show()
      this.$refs.resetPassword.setCode(this.$route.query.code)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .topnav {
    margin-bottom: 60px;
  }
  .bg-dark {
    background-color: #232c3b !important;
  }
</style>
