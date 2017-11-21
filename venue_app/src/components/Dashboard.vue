<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col>
        <h2>{{ $t('dashboard') }}</h2>
      </b-col>
    </b-row>
    <b-row style="margin-top: 16px;">
      <b-col>
        <b-table v-if="stats.length > 0" bordered hover :items="stats" :fields="statsFields"></b-table>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Dashboard',
  data () {
    return {
      showPage: false,
      statsFields: [
        {key: 'forumSite', sortable: true},
        {key: 'User_ID', sortable: true},
        {key: 'postPoints', sortable: true},
        {key: 'postDaysPoints', sortable: true},
        {key: 'influencePoints', sortable: true},
        {key: 'totalPoints', sortable: true},
        {key: 'VTX_Tokens', sortable: true}
      ],
      stats: []
    }
  },
  created () {
    var payload = { apiToken: this.$store.state.apiToken }
    axios.post('/get-stats/', payload).then(response => {
      this.stats = response.data.stats
      if (this.stats.length === 0) {
        this.$router.push({
          path: '/signatures',
          query: { initial: true }
        })
      } else {
        this.showPage = true
      }
    })
  }
}
</script>

<style scoped>

</style>