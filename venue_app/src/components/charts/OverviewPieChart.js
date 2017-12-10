import { Doughnut, mixins } from 'vue-chartjs'

export default {
  extends: Doughnut,
  mixins: [mixins.reactiveProp],
  props: ['data'],
  mounted () {
    this.renderChart({
      labels: [' Post Points', ' Post Uptime Points', ' Influence Points'],
      datasets: [
        {
          label: 'Overview Pie Chart',
          backgroundColor: ['#2a96b6', '#5a2998', '#b62da9'],
          data: [this.data.post_points, this.data.post_days_points, this.data.influence_points]
        }
      ]
    }, {
      legend: {
        display: false
      }
    })
  }
}
