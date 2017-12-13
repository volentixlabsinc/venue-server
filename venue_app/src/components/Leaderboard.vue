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
              <p class="card-text sm">Total Points Available: {{ sitewideStats.available_points }}</p>
            </b-card>
          </b-col>
          <b-col>
            <b-card class="text-center">
              <p class="card-text sm">Total Tokens Available: {{ sitewideStats.available_tokens }}</p>
            </b-card>
          </b-col>
        </b-row>
        <b-row>
          <b-col>
            <b-row>
              <b-col v-if="$store.state.apiToken">
                <p style="text-align: center;"><strong>Your Current Tokens</strong></p>
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
                  <p style="text-align: center;">Join the signature campaign now or login!</p>
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
                <b-card header="Your Rank" class="text-center" v-if="$store.state.apiToken">
                  <p class="card-text">{{ userStats.overall_rank }}</p>
                </b-card>
                <b-card header="Your Rank" class="text-center" v-if="!$store.state.apiToken">
                  <p class="card-text">NA</p>
                </b-card>
              </b-col>
              <b-col sm="4">
                <b-card header="Total Users" class="text-center">
                  <p class="card-text">{{ sitewideStats.total_users }}</p>
                </b-card>
              </b-col>
              <b-col sm="4">
                <b-card header="Total Posts" class="text-center">
                  <p class="card-text">{{ sitewideStats.total_posts }}</p>
                </b-card>
              </b-col>
            </b-row>
          </b-col>
        </b-row>
        <b-row style="margin-top: 40px;" v-if="false">
          <b-col>
            <div>
              <div class="graph-div" style="background: #dd4c3d; height: 30px; display: inlibe-block; width: 30%; float: right;">
                23 users
              </div>
              <div class="graph-div" style="background: gray; height: 30px; display: inline-block; width: 70%;">
                67 users
              </div>
              <span stle="color: gray;">Bitcointalk</span>
              <span style="color: #dd4c3d; float: right;">Bitcoin Forum</span>
            </div>
          </b-col>
          <b-col>
            <div>
              <div class="graph-div" style="background: #dd4c3d; height: 30px; display: inlibe-block; width: 45%; float: right;">
                46 posts
              </div>
              <div class="graph-div" style="background: gray; height: 30px; display: inline-block; width: 55%;">
                54 posts
              </div>
              <span stle="color: gray;">Bitcointalk</span>
              <span style="color: #dd4c3d; float: right;">Bitcoin Forum</span>
            </div>
          </b-col>
        </b-row>
        <b-row style="margin-top: 35px;">
          <b-col>
            <p style="text-align: center;"><strong>Total Users Per Forum Site</strong></p>
            <forums-overview :data="forumUsers" title="Total Users" :height="90"></forums-overview>
          </b-col>
          <b-col>
            <p style="text-align: center;"><strong>Total Posts Per Forum Site</strong></p>
            <forums-overview :data="forumPosts" title="Total Posts" :height="90"></forums-overview>
          </b-col>
        </b-row>
        <b-row style="margin-top: 45px;">
            <b-col>
                <b-table bordered hover 
                  :per-page="perPage" 
                  :current-page="currentPage" 
                  :items="leaderboardData" 
                  :fields="leaderboardFields">
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
        {key: 'rank', sortable: true},
        {key: 'username', sortable: true},
        {key: 'total_posts', sortable: true},
        {key: 'total_points', sortable: true},
        {key: 'total_tokens', sortable: true}
      ],
      leaderboardData: [],
      sitewideStats: {},
      userStats: {},
      perPage: 10,
      currentPage: 1,
      forumPosts: [
        {forumSite: 'Bitcointalk', value: 30, color: 'red'},
        {forumSite: 'Bitcoin Forum', value: 7, color: 'blue'}
      ]
    }
  },
  created () {
    this.$Progress.start()
    let payload = { apiToken: this.$store.state.apiToken }
    axios.post('/get-leaderboard-data/', payload).then(response => {
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