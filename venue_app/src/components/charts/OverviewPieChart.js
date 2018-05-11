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
          backgroundColor: ['#2a96b6', '#5a2998'],
          data: [this.data.post_points, this.data.uptime_points]
        }
      ]
    }, {
      legend: {
        display: false
      }
    })
  }
}
