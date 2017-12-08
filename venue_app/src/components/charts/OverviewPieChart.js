import { Doughnut } from 'vue-chartjs'

export default {
  extends: Doughnut,
  props: ['data'],
  mounted () {
    this.renderChart({
      labels: [' Post Points', ' Post Days Points', ' Influence Points'],
      datasets: [
        {
          label: 'Overview Pie Chart',
          backgroundColor: ['#2a96b6', '#5a2998', '#b62da9'],
          data: [this.data.post_points, this.data.post_days_points, this.data.influence_points]
        }
      ]
    }, {
      legend: {
        position: 'bottom',
        maxWidth: 200
      }
    })
  }
}
