<template>
  <div class="page-container">
    <b-row>
      <b-col>
        <h2>{{ $t('signatures') }}</h2>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-row v-for="site in forumSites" key="site.name">
          <b-col>
            <p>{{ site.name }}</p>
            <p>Verification Code: 861539273</p>
            <p>
              UserID: <input type="text" :name="site.name + 'userId'">
              <b-button variant="primary">Verify</b-button>
            </p>
          </b-col>
        </b-row>
      </b-col>
      <b-col>
        <b-row>
          <b-col>
            <p>Step 1: Place "Verfication Code" in your forum signature</p>
            <p>Step 2: Enter your forum UserID (found in the URL of your forum profile)</p>
            <p>Step 3: Click "Verify"</p>
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
      forumSites: []
    }
  },
  created () {
    axios.get('/api/forum-sites/').then(response => {
      console.log(response.data)
      this.forumSites = response.data
    })
  }
}
</script>

<style scoped>

</style>