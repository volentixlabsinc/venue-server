import { Doughnut } from 'vue-chartjs'

export default {
  extends: Doughnut,
  props: ['label', 'myPoints', 'totalPoints', 'color'],
  mounted () {
    let myPoints = parseFloat(this.myPoints.toString().replace(/,/g, ''))
    let totalPoints = parseFloat(this.totalPoints.toString().replace(/,/g, ''))
    let restPts = totalPoints - myPoints
    this.renderChart({
      labels: [' My Points', ' Others'],
      datasets: [
        {
          label: this.label,
          backgroundColor: [this.color, 'lightgray'],
          data: [Math.round(myPoints), Math.round(restPts)]
        }
      ]
    }, {
      legend: {
        display: true,
        position: 'bottom'
      }
    })
  }
}
