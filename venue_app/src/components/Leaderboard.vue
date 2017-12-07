<template>
    <div class="page-container">
        <b-row>
            <b-col>
                <h2>{{ $t('leaderboard') }}</h2>
            </b-col>
        </b-row>
        <b-row>
            <b-col sm="5">
                <b-table hover :items="items" :fields="fields"></b-table>
            </b-col>
        </b-row>
    </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Leaderboard',
  data () {
    return {
      fields: ['username', 'tokens'],
      items: []
    }
  },
  created () {
    this.$Progress.start()
    axios.post('/get-leaderboard-data/').then(response => {
      if (response.data.success) {
        this.items = response.data.data
        this.$Progress.finish()
      }
    })
  }
}
</script>