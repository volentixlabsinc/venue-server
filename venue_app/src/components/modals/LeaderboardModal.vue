<template>
  <!-- Login Modal -->
  <b-modal 
    id="leaderboard-modal" 
    :title="$i18n.t('leaderboard')" 
    ref="leaderboardModal" hide-footer>
    <b-table hover :items="items" :fields="fields"></b-table>
  </b-modal>
</template>

<script>
import axios from 'axios'

export default {
  name: 'LeaderboardModal',
  data () {
    return {
      fields: ['username', 'tokens'],
      items: []
    }
  },
  created () {
    var payload = { token: this.$store.state.apiToken }
    axios.post('/get-leaderboard-data/', payload).then(response => {
      if (response.data.success) {
        this.items = response.data.data
      }
    })
  }
}
</script>