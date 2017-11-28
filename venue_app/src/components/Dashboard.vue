<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col>
        <h2>{{ $t('dashboard') }}</h2>
      </b-col>
    </b-row>
    <b-row style="margin-top: 16px;">
      <b-col>
        <b-table v-if="stats.length > 0" bordered hover :items="stats" :fields="statsFields">
          <template slot="show_details" scope="row">
            <b-form-checkbox v-model="row.item._showDetails"></b-form-checkbox>
          </template>
          <template slot="row-details" scope="row">
            <b-card>
              <b-row>
                <b-col sm="4">
                  <b-row class="mb-2">
                    <b-col>
                      <b>Profile details</b>
                    </b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">Forum:</b-col>
                    <b-col>{{ row.item.forumSite }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">User ID:</b-col>
                    <b-col>{{ row.item.forumUserId }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">Rank:</b-col>
                    <b-col>{{ row.item.forumUserRank }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">Total posts:</b-col>
                    <b-col>{{ row.item.totalPosts }}</b-col>
                  </b-row>
                </b-col>
                <b-col>
                  <b-row class="mb-2">
                    <b-col>
                      <b>Credits for the current uptime batch</b>
                    </b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">Batch number:</b-col>
                    <b-col>{{ row.item.currentUptimeBatch }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">Posts since signature was found:</b-col>
                    <b-col>{{ row.item.totalPostsWithSig }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">Days since signature was found:</b-col>
                    <b-col>{{ row.item.totalPostDays }}</b-col>
                  </b-row>
                </b-col>
                <b-col>
                  <b-row v-if="row.item.hasPreviousBatches" class="mb-2">
                    <b-col>
                      <b>Credits from previous uptime batches</b>
                    </b-col>
                  </b-row>
                  <div v-for="batch in row.item.previousBatches">
                    <b-row>
                      <b-col sm="9">Batch number:</b-col>
                      <b-col>{{ batch.batch }}</b-col>
                    </b-row>
                    <b-row>
                      <b-col sm="9">Posts since signature was found:</b-col>
                      <b-col>{{ batch.totalPostsWithSig }}</b-col>
                    </b-row>
                    <b-row>
                      <b-col sm="9" class="mb-2">Days since signature was found:</b-col>
                      <b-col>{{ batch.totalPostDays }}</b-col>
                    </b-row>
                  </div>
                </b-col>
              </b-row>
            </b-card>
          </template>
        </b-table>
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
        {key: 'VTX_Tokens', sortable: true},
        'show_details'
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