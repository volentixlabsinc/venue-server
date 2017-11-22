<template>
  <div class="topnav">
    <b-navbar toggleable="md" type="dark" variant="dark">
      
      <b-nav-toggle target="nav_collapse"></b-nav-toggle>
      
      <b-navbar-brand href="/">
        <img src="../assets/logo.png" alt="BV">
      </b-navbar-brand>
      
      <b-collapse is-nav id="nav_collapse">
        
        <b-nav is-nav-bar class="ml-auto">
        
          <b-nav-item-dropdown :text="$i18n.t('language')" right>
            <b-dropdown-item @click="setLanguage('en')">English</b-dropdown-item>
            <b-dropdown-item @click="setLanguage('fr')">French</b-dropdown-item>
          </b-nav-item-dropdown>
          
          <b-nav-form>
            <b-button size="sm" 
              class="my-2 my-sm-0" 
              v-b-modal.login-modal v-if="!$store.state.apiToken">
              {{ $t('login') }}
            </b-button>
          </b-nav-form>
          
          <b-nav-item v-if="$store.state.apiToken" to="/dashboard">
            {{ $t('dashboard') }}
          </b-nav-item>
          
          <b-nav-item v-if="$store.state.apiToken" to="/signatures">
            {{ $t('signatures') }}
          </b-nav-item>
          
          <b-nav-item v-if="$store.state.apiToken" to="/settings">
            {{ $t('settings') }}
          </b-nav-item>
          
          <b-nav-item v-if="$store.state.apiToken" @click="logout()">
            {{ $t('logout') }}
          </b-nav-item>
        </b-nav>
        
      </b-collapse>
    </b-navbar>
    
    <login-modal></login-modal>
    
  </div>
</template>

<script>
import LoginModal from '@/components/modals/LoginModal'
import axios from 'axios'

export default {
  name: 'TopNavigation',
  components: { LoginModal },
  methods: {
    logout () {
      this.$store.commit('updateApiToken', '')
      this.$store.commit('updateUser', null)
      axios.defaults.headers.common['Authorization'] = ''
      this.$router.push('/')
    },
    setLanguage (lang) {
      this.$i18n.locale = lang
    }
  },
  created () {
    if (this.$route.query.email_confirmed === '1') {
      this.$swal({
        title: 'Email Confirmed!',
        text: 'Thank you! You may login now.',
        icon: 'success',
        button: {
          text: 'OK',
          className: 'btn-primary',
          closeModal: true
        }
      })
    }
    if (this.$route.query.account_deleted === '1') {
      this.$swal({
        title: 'Account Deleted!',
        text: 'Your account has been successfully deleted.',
        icon: 'success',
        button: {
          text: 'OK',
          className: 'btn-primary',
          closeModal: true
        }
      }).then(() => {
        this.logout()
      })
    }
    if (this.$route.query.updated_email === '1') {
      this.$swal({
        title: 'Updated Email!',
        text: 'You have successfully changed the email in your account.',
        icon: 'success',
        button: {
          text: 'OK',
          className: 'btn-primary',
          closeModal: true
        }
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .topnav {
    margin-bottom: 20px;
  }
</style>
