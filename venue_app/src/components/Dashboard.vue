<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col>
        <h2>{{ $t('dashboard') }}</h2>
      </b-col>
    </b-row>
    <b-row class="justify-content-md-center">
      <b-col sm="2">
        <p style="text-align: center;">Post Points</p>
        <points-chart :height="320" label="My Post Points" :myPoints="points.postPoints" :totalPoints="6000"></points-chart>
      </b-col>
      <b-col sm="2">
        <p style="text-align: center;">Post Days Points</p>
        <points-chart :height="320" label="My Post Days Points" :myPoints="points.postDaysPoints" :totalPoints="3800"></points-chart>
      </b-col>
      <b-col sm="2">
        <p style="text-align: center;">Influence Points</p>
        <points-chart :height="320" label="My Influence Points" :myPoints="points.influencePoints" :totalPoints="200"></points-chart>
      </b-col>
      <b-col sm="2">
        <p style="text-align: center;">Total Points</p>
        <points-chart :height="320" label="My Total Points" :myPoints="points.totalPoints" :totalPoints="10000"></points-chart>
      </b-col>
      <b-col sm="2">
        <p style="text-align: center;">VTX Tokens</p>
        <points-chart :height="320" label="My VTX Tokens" :myPoints="points.VTX_Tokens" :totalPoints="120000"></points-chart>
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
              <b-row v-if="row.item._rowVariant === 'danger'">
                <b-col>
                  <b-alert show variant="danger">
                    The latest check did not find our signature in your profile.
                  </b-alert>
                </b-col>
              </b-row>
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
                    <b-col sm="9">Batch number {{ row.item.currentUptimeBatch.batch }}:</b-col>
                    <b-col></b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">Posts since signature was found:</b-col>
                    <b-col>{{ row.item.currentUptimeBatch.totalPostsWithSig }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">Days since signature was found:</b-col>
                    <b-col>{{ row.item.currentUptimeBatch.totalPostDays }}</b-col>
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
                      <b-col sm="9">Batch number {{ batch.batch }}:</b-col>
                      <b-col></b-col>
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

    <leaderboard-modal></leaderboard-modal>
  </div>
</template>

<script>
import LeaderboardModal from '@/components/modals/LeaderboardModal'
import PointsChart from '@/components/charts/PointsChart'
import axios from 'axios'

export default {
  name: 'Dashboard',
  components: { LeaderboardModal, PointsChart },
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
      stats: [],
      points: {}
    }
  },
  created () {
    this.$Progress.start()
    var payload = { apiToken: this.$store.state.apiToken }
    axios.post('/get-stats/', payload).then(response => {
      this.stats = response.data.stats
      this.points = this.stats[0]
      if (this.stats.length === 0) {
        this.$router.push({
          path: '/signatures',
          query: { initial: true }
        })
      } else {
        this.showPage = true
        this.$Progress.finish()
      }
    })
  }
}
</script>

<style scoped>

</style>
