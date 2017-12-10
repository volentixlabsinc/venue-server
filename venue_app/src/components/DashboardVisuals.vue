<template>
  <b-row>
    <b-col sm="5">
      <b-row>
        <b-col>
          <p style="text-align: center;"><strong>Tokens You Earned</strong></p>
          <div class="iCountUp">
            <i-count-up
              :start="0"
              :end="userstats.total_tokens"
              :decimals="0"
              :duration="1.5">
            </i-count-up> VTX
          </div>
        </b-col>
      </b-row>
      <b-row style="margin-top: 35px;" v-if="!leaderboard">
        <b-col>
          <p style="text-align: center;"><strong>Your Current Points Overview</strong></p>
          <overview-pie-chart :data="userstats" :height="250"></overview-pie-chart>
        </b-col>
      </b-row>
      <b-row style="margin-top: 20px;" v-if="!leaderboard">
        <b-col offset-sm="2" sm="10">
          <div>
            <div class="legend-color" style="background-color: #2a96b6;"></div> 
            <span class="legend-text">Post Points - {{ userstats.post_points }} out of 6000</span>
          </div>
          <div>
            <div class="legend-color" style="background-color: #5a2998;"></div> 
            <span class="legend-text">Post Uptime Points - {{ userstats.post_days_points }} out of 3800</span>
          </div>
          <div>
            <div class="legend-color" style="background-color: #b62da9;"></div> 
            <span class="legend-text">Influence Points - {{ userstats.influence_points }} out of 200</span>
          </div>
          <div>
            <div class="legend-color"></div> 
            <span class="legend-text">Total Points - {{ userstats.total_points }} out of 10000</span>
          </div>
        </b-col>
      </b-row>
    </b-col>
    <b-col>
      <b-row class="justify-content-md-center">
        <b-col sm="4">
          <b-card header="Your Rank" class="text-center">
            <p class="card-text">#{{ userstats.overall_rank }}</p>
          </b-card>
        </b-col>
        <b-col sm="4">
          <b-card header="Total Users" class="text-center">
            <p class="card-text">{{ sitestats.total_users }}</p>
          </b-card>
        </b-col>
        <b-col sm="4">
          <b-card header="Total Posts Sitewide" class="text-center">
            <p class="card-text">{{ sitestats.total_posts }}</p>
          </b-card>
        </b-col>
      </b-row>
      <b-row style="margin-top: 40px;" v-if="!leaderboard">
        <b-col>
            <p style="text-align: center;"><strong>Daily Posts and Ranking</strong></p>
            <points-evolution-chart :data="userstats.daily_stats" :height="200"></points-evolution-chart>
        </b-col>
      </b-row>
    </b-col>
  </b-row>
</template>

<script>
import PointsPieChart from '@/components/charts/PointsPieChart'
import OverviewPieChart from '@/components/charts/OverviewPieChart'
import PointsEvolutionChart from '@/components/charts/PointsEvolutionChart'
import ICountUp from 'vue-countup-v2'

export default {
  name: 'DashboardVisuals',
  components: {
    PointsPieChart,
    OverviewPieChart,
    PointsEvolutionChart,
    ICountUp
  },
  props: ['userstats', 'sitestats', 'leaderboard'],
  data () {
    return {
      userstats: this.userstats,
      sitestats: this.sitestats,
      leaderboard: this.leaderboard
    }
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

.legend-color {
  margin-top: 2px;
  width: 20px; 
  height: 20px; 
  display: inline-block;
}

.legend-text {
  vertical-align: top;
}

.card-text {
  font-size: 24px;
}
</style>