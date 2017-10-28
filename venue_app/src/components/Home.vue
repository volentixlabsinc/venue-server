<template>
  <div class="home">
    <b-jumbotron>
      <template slot="header">
        VENUE
      </template>
      <template slot="lead">
        Autonomous Signature Campaign Tracking
      </template>
      <hr class="my-4">
      <p>
        VENUE tracks and displays sophisticated user rankings and accurate payout information LIVE.
      </p>
      <b-btn variant="primary" v-if="!$store.state.apiToken">Sign Up</b-btn>
      <b-btn variant="dark"
        v-b-modal.modal1 v-if="!$store.state.apiToken">
        Login
      </b-btn>
    </b-jumbotron>
  </div>
</template>

<script>
export default {
  name: 'Home'
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
