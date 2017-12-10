<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col v-if="!showLeaderboard">
        <h2>{{ $t('dashboard') }}</h2>
      </b-col>
      <b-col v-if="showLeaderboard">
        <h2>{{ $t('leaderboard') }}</h2>
      </b-col>
      <b-col v-if="!showLeaderboard">
        <p style="text-align: right;" @click="refreshData()" v-if="!refreshing">
          Refresh
        </p>
        <img v-if="refreshing" style="float: right;" src="../assets/animated_spinner.gif" height="30">
      </b-col>
    </b-row>
    <dashboard-visuals 
      :userstats="stats.user_level" 
      :sitestats="stats.sitewide" 
      :leaderboard="showLeaderboard">
    </dashboard-visuals>
    <b-row style="margin-top: 45px;" v-if="!showLeaderboard">
      <b-col>
        <b-table v-if="stats.profile_level.length > 0" bordered hover :items="stats.profile_level" :fields="statsFields">
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
    <b-row v-if="showLeaderboard" style="margin-top: 45px;" id="leaderboard">
      <b-col>
        <b-table bordered hover :items="leaderboardData" :fields="leaderboardFields"></b-table>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import DashboardVisuals from '@/components/DashboardVisuals'
import axios from 'axios'

export default {
  name: 'Dashboard',
  components: { DashboardVisuals },
  data () {
    return {
      showPage: false,
      showLeaderboard: null,
      leaderboardData: [],
      leaderboardFields: [
        {key: 'rank', sortable: true},
        {key: 'username', sortable: true},
        {key: 'total_posts', sortable: true},
        {key: 'total_points', sortable: true},
        {key: 'total_tokens', sortable: true}
      ],
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
      stats: {},
      refreshing: false
    }
  },
  methods: {
    refreshData () {
      this.$Progress.start()
      this.refreshing = true
      var payload = { apiToken: this.$store.state.apiToken }
      axios.post('/get-stats/', payload).then(response => {
        this.stats = response.data.stats
        if (this.stats.fresh === true) {
          this.$router.push({
            path: '/signatures',
            query: { initial: true }
          })
        } else {
          this.showPage = true
          // Get leaderboard data
          axios.post('/get-leaderboard-data/').then(response => {
            if (response.data.success) {
              this.leaderboardData = response.data.data
              this.$Progress.finish()
              this.refreshing = false
            }
          })
        }
      })
    }
  },
  created () {
    // Fetch data from the server
    this.refreshData()
    /*
    // Refresh dashboard data every 1 minute
    this.interval = setInterval(function () {
      this.refreshData()
    }.bind(this), 60000)
    */
    if (this.$route.query.leaderboard === '1') {
      this.showLeaderboard = true
      window.scrollTo(0, document.body.scrollHeight)
    }
  },
  watch: {
    showLeaderboard: function (value) {
      if (value) {
        window.scrollTo(0, document.body.scrollHeight)
      }
    }
  },
  beforeRouteUpdate (to, from, next) {
    // Detect leaderboard query param
    if (to.query.leaderboard === '1') {
      this.showLeaderboard = true
    } else {
      this.showLeaderboard = false
    }
    next()
  }
}
</script>

<style scoped>

</style>
