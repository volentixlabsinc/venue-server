<template>
  <b-row>
    <b-col sm="5">
      <b-row>
        <b-col>
          <p style="text-align: center;">Your Current Points Overview</p>
          <overview-pie-chart :height="250"></overview-pie-chart>
        </b-col>
      </b-row>
    </b-col>
    <b-col>
      <b-row>
        <b-col>
          <p style="text-align: center;">Your Points Relative to Others</p>
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
            <p style="text-align: center;">Daily Total Points</p>
            <points-evolution-chart :height="150"></points-evolution-chart>
        </b-col>
      </b-row>
    </b-col>
  </b-row>
</template>

<script>
import PointsPieChart from '@/components/charts/PointsPieChart'
import OverviewPieChart from '@/components/charts/OverviewPieChart'
import PointsEvolutionChart from '@/components/charts/PointsEvolutionChart'

export default {
  name: 'DashboardVisuals',
  components: { PointsPieChart, OverviewPieChart, PointsEvolutionChart },
  props: ['points'],
  data () {
    return {
      points: this.points
    }
  }
}
</script>
