import { Doughnut } from 'vue-chartjs'

export default {
  extends: Doughnut,
  mounted () {
    this.renderChart({
      labels: [' Post Points', ' Post Days Points', ' Influence Points'],
      datasets: [
        {
          label: 'Overview Pie Chart',
          backgroundColor: ['#2a96b6', '#5a2998', '#b62da9'],
          data: [4501, 2349, 150]
        }
      ]
    }, {
      legend: {
        display: false
      }
    })
  }
}
