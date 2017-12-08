<template>
  <b-row>
    <b-col sm="5">
      <b-row>
        <b-col>
          <p style="text-align: center;"><strong>Tokens You Earned</strong></p>
          <div class="iCountUp">
            <i-count-up
              :start="0"
              :end="stats.total_tokens"
              :decimals="0"
              :duration="1.5">
            </i-count-up> VTX
          </div>
        </b-col>
      </b-row>
      <b-row style="margin-top: 35px;">
        <b-col>
          <p style="text-align: center;"><strong>Your Current Points Overview</strong></p>
          <overview-pie-chart :data="stats" :height="250"></overview-pie-chart>
        </b-col>
      </b-row>
      <b-row style="margin-top: 35px;">
        <b-col>
          <p style="text-align: center;"><strong>Your Current Rank</strong></p>
          <div class="iCountUp">
            Rank #
            <i-count-up
              :start="0"
              :end="stats.overall_rank"
              :decimals="0"
              :duration="1.5">
            </i-count-up>
          </div>
        </b-col>
      </b-row>
    </b-col>
    <b-col>
      <b-row>
        <b-col>
          <p style="text-align: center;"><strong>Your Points Relative to Others</strong></p>
        </b-col>
      </b-row>
      <b-row class="justify-content-md-center">
        <b-col sm="3">
          <p style="text-align: center;">Post Points</p>
          <points-pie-chart 
            :height="320" 
            color="#2a96b6" 
            label="My Post Points" 
            :myPoints="stats.post_points" 
            :totalPoints="6000">
          </points-pie-chart>
        </b-col>
        <b-col sm="3">
          <p style="text-align: center;">Post Days Points</p>
          <points-pie-chart 
            :height="320" 
            color="#5a2998" 
            label="My Post Days Points" 
            :myPoints="stats.post_days_points" 
            :totalPoints="3800">
          </points-pie-chart>
        </b-col>
        <b-col sm="3">
          <p style="text-align: center;">Influence Points</p>
          <points-pie-chart 
            :height="320" 
            color="#b62da9" 
            label="My Influence Points" 
            :myPoints="stats.influence_points" 
            :totalPoints="200">
          </points-pie-chart>
        </b-col>
        <b-col sm="3">
          <p style="text-align: center;">Total Points</p>
          <points-pie-chart 
            :height="320" 
            color="#dd4c3d" 
            label="My Total Points" 
            :myPoints="stats.total_points" 
            :totalPoints="10000">
          </points-pie-chart>
        </b-col>
      </b-row>
      <b-row style="margin-top: 40px;">
        <b-col>
            <p style="text-align: center;"><strong>Daily Total Points and Ranking</strong></p>
            <points-evolution-chart :data="stats.daily_stats" :height="200"></points-evolution-chart>
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
  props: ['stats'],
  data () {
    return {
      stats: this.stats
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
</style>