<template>
  <b-row>
    <b-col sm="5">
      <b-row>
        <b-col>
          <p style="text-align: center;"><strong>{{ $t('your_current_tokens') }}</strong></p>
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
      <b-row style="margin-top: 35px;">
        <b-col>
          <p style="text-align: center;"><strong>{{ $t('your_points_overview') }}</strong></p>
          <overview-pie-chart :data="userstats" :height="250"></overview-pie-chart>
        </b-col>
      </b-row>
      <b-row style="margin-top: 20px;">
        <b-col offset-sm="2" sm="10">
          <div>
            <div class="legend-color" style="background-color: #2a96b6;"></div> 
            <span class="legend-text">{{ $t('post_points') }} - {{ userstats.post_points }} {{ $t('out_of')}} 6000</span>
          </div>
          <div>
            <div class="legend-color" style="background-color: #5a2998;"></div> 
            <span class="legend-text">{{ $t('post_uptime_points') }} - {{ userstats.post_days_points }} {{ $t('out_of')}} 3800</span>
          </div>
          <div>
            <div class="legend-color" style="background-color: #b62da9;"></div> 
            <span class="legend-text">{{ $t('influence_points') }} - {{ userstats.influence_points }} {{ $t('out_of')}} 200</span>
          </div>
        </b-col>
      </b-row>
    </b-col>
    <b-col>
      <b-row class="justify-content-md-center">
        <b-col sm="4">
          <b-card :header="$t('your_rank')" class="text-center">
            <p class="card-text">#{{ userstats.overall_rank }}</p>
          </b-card>
        </b-col>
        <b-col sm="4">
          <b-card :header="$t('your_total_posts')" class="text-center">
            <p class="card-text">{{ userstats.total_posts }}</p>
          </b-card>
        </b-col>
        <b-col sm="4">
          <b-card :header="$t('your_total_points')" class="text-center">
            <p class="card-text">{{ userstats.total_points }}</p>
          </b-card>
        </b-col>
      </b-row>
      <b-row style="margin-top: 40px;">
        <b-col>
            <p style="text-align: center;"><strong>{{ $t('daily_posts_and_ranking') }}</strong></p>
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
  props: ['userstats', 'sitestats']
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