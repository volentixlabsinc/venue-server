<template>
  <div class="page-container" v-if="showPage">
    <b-row>
      <b-col>
        <h2>{{ $t('dashboard') }}</h2>
      </b-col>
      <b-col>
        <p style="text-align: right;" v-if="!refreshing">
          <span style="cursor: pointer;" @click="refreshData()">{{ $t('refresh') }}</span>
        </p>
        <img v-if="refreshing" style="float: right;" src="../assets/animated_spinner.gif" height="30">
      </b-col>
    </b-row>
    <dashboard-visuals 
      :userstats="stats.user_level" 
      :sitestats="stats.sitewide">
    </dashboard-visuals>
    <b-row style="margin-top: 45px;">
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
                    {{ $t('latest_check_negative') }}
                  </b-alert>
                </b-col>
              </b-row>
              <b-row>
                <b-col sm="4">
                  <b-row class="mb-2">
                    <b-col>
                      <b>{{ $t('profile_details') }}</b>
                    </b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">{{ $t('forum_site') }}:</b-col>
                    <b-col>{{ row.item.forumSite }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">{{ $t('user_id') }}:</b-col>
                    <b-col>{{ row.item.forumUserId }}</b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="5">{{ $t('rank') }}:</b-col>
                    <b-col>{{ row.item.forumUserRank }}</b-col>
                  </b-row>
                  <b-row v-if="row.item.totalPosts > 0">
                    <b-col sm="5">{{ $t('total_posts') }}:</b-col>
                    <b-col>{{ row.item.totalPosts }}</b-col>
                  </b-row>
                </b-col>
                <b-col>
                  <b-row class="mb-2">
                    <b-col>
                      <b>{{ $t('current_batch_credits') }}</b>
                    </b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">{{ $t('batch_number') }} {{ row.item.currentUptimeBatch.batch }}:</b-col>
                    <b-col></b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">{{ $t('total_posts_with_sig') }}:</b-col>
                    <b-col>
                      <span style="color: green;">
                        {{ row.item.currentUptimeBatch.totalPostsWithSig }}
                      </span>
                    </b-col>
                  </b-row>
                  <b-row>
                    <b-col sm="9">{{ $t('total_posts_uptime') }}:</b-col>
                    <b-col>{{ row.item.currentUptimeBatch.totalPostDays }}</b-col>
                  </b-row>
                </b-col>
                <b-col>
                  <b-row v-if="row.item.hasPreviousBatches" class="mb-2">
                    <b-col>
                      <b>{{ $t('previous_batch_credits') }}</b>
                    </b-col>
                  </b-row>
                  <div v-for="batch in row.item.previousBatches" :key="batch.batch">
                    <b-row>
                      <b-col sm="9">{{ $t('batch_number') }} {{ batch.batch }}:</b-col>
                      <b-col></b-col>
                    </b-row>
                    <!--
                    <b-row>
                      <b-col sm="9">{{ $t('total_posts_with_sig') }}:</b-col>
                      <b-col>
                        <span style="color: green;">{{ batch.totalPostsWithSig }}</span>
                      </b-col>
                    </b-row>
                    <b-row v-if="batch.deletedPosts">
                      <b-col sm="9">{{ $t('deleted_posts') }}:</b-col>
                      <b-col>
                        <span style="color: red;">-{{ batch.deletedPosts }}</span>
                      </b-col>
                    </b-row>
                    -->
                    <b-row>
                      <b-col sm="9" class="mb-2">{{ $t('total_posts_uptime') }}:</b-col>
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
import DashboardVisuals from '@/components/DashboardVisuals'
import axios from 'axios'

export default {
  name: 'Dashboard',
  components: { DashboardVisuals },
  data () {
    return {
      showPage: false,
      statsFields: [
        {key: 'forumSite', sortable: true, label: this.$t('forum_site')},
        {key: 'User_ID', sortable: true, label: this.$t('user_id')},
        {key: 'postPoints', sortable: true, label: this.$t('post_points')},
        {key: 'postDaysPoints', sortable: true, label: this.$t('post_uptime_points')},
        {key: 'influencePoints', sortable: true, label: this.$t('influence_points')},
        {key: 'totalPoints', sortable: true, label: this.$t('total_points')},
        {key: 'VTX_Tokens', sortable: true, label: this.$t('vtx_tokens')},
        {key: 'show_details', label: this.$t('show_details')}
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
        // Issue: Stats data for the points evolution chart is not updating when
        // merely clicking on the Refresh link. Hard refresh works though
        // TODO -- make the above line reactive by changing it to:
        // this.$set(this.stats, response.data.stats)
        // Not tested yet but may work
        if (this.stats.fresh === true) {
          this.$router.push({
            path: '/signatures',
            query: { initial: true }
          })
        } else {
          this.showPage = true
        }
        this.$Progress.finish()
        this.refreshing = false
      })
    }
  },
  created () {
    // Fetch data from the server
    this.refreshData()
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
