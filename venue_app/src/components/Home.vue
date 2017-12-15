<template>
  <div>
    <b-jumbotron id="home-jumbotron" bg-variant="light" fluid>
      <template slot="header">
        VENUE
      </template>
      <template slot="lead">
        {{ $t('venue_title') }}
      </template>
      <hr class="my-4">
      <p>
        {{ $t('venue_description') }}
      </p>
      <b-btn variant="primary" :disabled="disableSignUp" 
        v-b-modal.signup-modal v-if="!$store.state.apiToken">
        {{ $t('signup') }}
      </b-btn>
      <b-btn variant="dark"
        v-b-modal.login-modal v-if="!$store.state.apiToken">
        {{ $t('login') }}
      </b-btn>
    </b-jumbotron>

    <sign-up-modal></sign-up-modal>
  </div>
</template>

<script>
import SignUpModal from '@/components/modals/SignUpModal'
import axios from 'axios'

export default {
  name: 'Home',
  components: { SignUpModal },
  data () {
    return {
      'disableSignUp': true
    }
  },
  created () {
    if (this.$store.state.apiToken.length > 0) {
      this.$router.push('/dashboard')
    } else {
      axios.post('/get-site-configs/').then(response => {
        this.disableSignUp = response.data.disable_sign_up
      })
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
#home-jumbotron {
  text-align: center;
}
h1, h2 {
  font-weight: normal;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}
</style>