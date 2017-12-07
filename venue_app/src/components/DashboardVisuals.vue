<template>
  <b-row>
    <b-col sm="5">
      <b-row>
        <b-col>
          <p style="text-align: center;"><strong>Tokens You Earned</strong></p>
          <div class="iCountUp">
            <i-count-up
              :start="0"
              :end="80500"
              :decimals="0"
              :duration="2.5">
            </i-count-up> VTX
          </div>
        </b-col>
      </b-row>
      <b-row style="margin-top: 30px;">
        <b-col>
          <p style="text-align: center;"><strong>Your Current Points Overview</strong></p>
          <overview-pie-chart :height="250"></overview-pie-chart>
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
            :myPoints="points.postPoints" 
            :totalPoints="6000">
          </points-pie-chart>
        </b-col>
        <b-col sm="3">
          <p style="text-align: center;">Post Days Points</p>
          <points-pie-chart 
            :height="320" 
            color="#5a2998" 
            label="My Post Days Points" 
            :myPoints="points.postDaysPoints" 
            :totalPoints="3800">
          </points-pie-chart>
        </b-col>
        <b-col sm="3">
          <p style="text-align: center;">Influence Points</p>
          <points-pie-chart 
            :height="320" 
            color="#b62da9" 
            label="My Influence Points" 
            :myPoints="points.influencePoints" 
            :totalPoints="200">
          </points-pie-chart>
        </b-col>
        <b-col sm="3">
          <p style="text-align: center;">Total Points</p>
          <points-pie-chart 
            :height="320" 
            color="#dd4c3d" 
            label="My Total Points" 
            :myPoints="points.totalPoints" 
            :totalPoints="10000">
          </points-pie-chart>
        </b-col>
      </b-row>
      <b-row style="margin-top: 40px;">
        <b-col>
            <p style="text-align: center;"><strong>Daily Total Points and Ranking</strong></p>
            <points-evolution-chart :height="200"></points-evolution-chart>
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
  props: ['points'],
  data () {
    return {
      points: this.points
    }
  }
}
</script>

<style scoped>
  .iCountUp {
    font-size: 45px;
    text-align: center;
    margin: 0;
    padding: 0;
    color: #232c3b;
  }
</style>