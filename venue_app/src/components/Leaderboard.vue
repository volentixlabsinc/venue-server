<template>
    <div class="page-container" v-if="showPage">
        <b-row>
            <b-col>
                <h2>{{ $t('leaderboard') }}</h2>
            </b-col>
        </b-row>
        <b-row style="margin-bottom: 45px;">
          <b-col>
            <b-card class="text-center">
              <p class="card-text sm">{{ $t('points_available') }}: {{ sitewideStats.available_points }}</p>
            </b-card>
          </b-col>
          <b-col>
            <b-card class="text-center">
              <p class="card-text sm">{{ $t('tokens_available') }}: {{ sitewideStats.available_tokens }}</p>
            </b-card>
          </b-col>
        </b-row>
        <b-row>
          <b-col>
            <b-row>
              <b-col v-if="$store.state.apiToken">
                <p style="text-align: center;"><strong>{{ $t('your_current_tokens') }}</strong></p>
                <div class="iCountUp">
                  <i-count-up
                    :start="0"
                    :end="userStats.total_tokens"
                    :decimals="0"
                    :duration="1.5">
                  </i-count-up> VTX
                </div>
              </b-col>
              <b-col v-if="!$store.state.apiToken" style="padding: 10px 40px;">
                  <p style="text-align: center;">{{ $t('join_or_login') }}</p>
                  <p style="text-align: center;">
                    <b-btn variant="primary"
                      v-b-modal.signup-modal>
                      {{ $t('signup') }}
                    </b-btn> &nbsp;
                    <b-btn variant="dark"
                      v-b-modal.login-modal>
                      {{ $t('login') }}
                    </b-btn>
                  </p>
              </b-col>
            </b-row>
          </b-col>
          <b-col>
            <b-row class="justify-content-md-center">
              <b-col sm="4">
                <b-card :header="$t('your_rank')" class="text-center" v-if="$store.state.apiToken">
                  <p class="card-text">{{ userStats.overall_rank }}</p>
                </b-card>
                <b-card :header="$t('your_rank')" class="text-center" v-if="!$store.state.apiToken">
                  <p class="card-text">NA</p>
                </b-card>
              </b-col>
              <b-col sm="4">
                <b-card :header="$t('total_users')" class="text-center">
                  <p class="card-text">{{ sitewideStats.total_users }}</p>
                </b-card>
              </b-col>
              <b-col sm="4">
                <b-card :header="$t('total_posts')" class="text-center">
                  <p class="card-text">{{ sitewideStats.total_posts }}</p>
                </b-card>
              </b-col>
            </b-row>
          </b-col>
        </b-row>
        <b-row style="margin-top: 35px;">
          <b-col>
            <p style="text-align: center;"><strong>{{ $t('total_forum_users') }}</strong></p>
            <forums-overview :data="forumUsers" :title="$t('total_users')" :height="90"></forums-overview>
          </b-col>
          <b-col>
            <p style="text-align: center;"><strong>{{ $t('total_forum_posts') }}</strong></p>
            <forums-overview :data="forumPosts" :title="$t('total_posts')" :height="90"></forums-overview>
          </b-col>
        </b-row>
        <b-row style="margin-top: 45px;">
            <b-col>
                <b-table bordered hover 
                  :per-page="perPage" 
                  :current-page="currentPage" 
                  :items="leaderboardData" 
                  :fields="leaderboardFields">
                  <template slot="show_details" scope="row">
                    <b-form-checkbox v-model="row.item._showDetails"></b-form-checkbox>
                  </template>
                  <template slot="row-details" scope="row">
                    <b-card style="padding-left: 20px;">
                      <b-row>
                        <b-col sm="4">
                          <b-row class="mb-2">
                            <b-col>
                              <b>{{ $t('points_breakdown') }}</b>
                            </b-col>
                          </b-row>
                          <b-row>
                            <b-col sm="7">{{ $t('post_points') }}:</b-col>
                            <b-col align="right">{{ row.item.post_points }} points</b-col>
                          </b-row>
                          <b-row>
                            <b-col sm="7">{{ $t('post_uptime_points') }}:</b-col>
                            <b-col align="right">{{ row.item.uptime_points }} points</b-col>
                          </b-row>
                          <b-row style="border-bottom: 1px solid black;">
                            <b-col sm="7">{{ $t('influence_points') }}:</b-col>
                            <b-col align="right">{{ row.item.influence_points }} points</b-col>
                          </b-row>
                          <b-row>
                            <b-col sm="7"><strong>{{ $t('total_points') }}</strong>:</b-col>
                            <b-col align="right">{{ row.item.total_points }} points</b-col>
                          </b-row>
                        </b-col>
                      </b-row>
                    </b-card>
                  </template>
                </b-table>
                <b-pagination 
                  v-if="leaderboardData.length > perPage"  
                  :total-rows="leaderboardData.length" 
                  :per-page="perPage" 
                  v-model="currentPage" />
            </b-col>
        </b-row>
        <sign-up-modal></sign-up-modal>
    </div>
</template>

<script>
import SignUpModal from '@/components/modals/SignUpModal'
import ForumsOverview from '@/components/charts/ForumsOverview'
import ICountUp from 'vue-countup-v2'
import axios from 'axios'

export default {
  name: 'Leaderboard',
  components: { ICountUp, SignUpModal, ForumsOverview },
  data () {
    return {
      showPage: false,
      leaderboardFields: [
        {key: 'rank', sortable: true, label: this.$t('rank')},
        {key: 'username', sortable: true, label: this.$t('username')},
        {key: 'total_posts', sortable: true, label: this.$t('total_posts')},
        {key: 'total_points', sortable: true, label: this.$t('total_points')},
        {key: 'total_tokens', sortable: true, label: this.$t('total_tokens')},
        {key: 'show_details', label: this.$t('show_details')}
      ],
      leaderboardData: [],
      sitewideStats: {},
      userStats: {},
      perPage: 10,
      currentPage: 1,
      forumPosts: []
    }
  },
  created () {
    this.$Progress.start()
    axios.get('/retrieve/leaderboard-data/').then(response => {
      if (response.data.success) {
        this.leaderboardData = response.data.rankings
        this.sitewideStats = response.data.sitewide
        this.userStats = response.data.userstats
        this.forumPosts = response.data.forumstats.posts
        this.forumUsers = response.data.forumstats.users
        this.$Progress.finish()
        this.showPage = true
      }
    })
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

<style scoped>
.iCountUp {
  font-size: 45px;
  text-align: center;
  margin: -10px;
  padding: 0;
  color: #232c3b;
}
.graph-div {
  padding: 5px 5px;
}
.card-text {
  font-size: 24px;
}
.card-text.sm {
  font-size: 20px;
}
</style>