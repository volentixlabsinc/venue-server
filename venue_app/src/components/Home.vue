<template>
  <div class="home">
    <b-jumbotron>
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
      <b-btn variant="primary"
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

export default {
  name: 'Home',
  components: { SignUpModal }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
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