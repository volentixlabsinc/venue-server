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
        
          <b-nav-item-dropdown right v-if="$store.state.apiToken">
            <!-- Using button-content slot -->
            <template slot="button-content">
              <em>{{ $store.state.user.userName }}</em>
            </template>
            <b-dropdown-item href="#">Profile</b-dropdown-item>
            <b-dropdown-item href="#" @click="logout()">{{ $t('logout') }}</b-dropdown-item>
          </b-nav-item-dropdown>
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
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .topnav {
    margin-bottom: 20px;
  }
</style>
