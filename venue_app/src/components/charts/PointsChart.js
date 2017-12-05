import { Doughnut } from 'vue-chartjs'

export default {
  extends: Doughnut,
  props: ['label', 'myPoints', 'totalPoints'],
  mounted () {
    let myPoints = parseFloat(this.myPoints.toString().replace(/,/g, ''))
    let totalPoints = parseFloat(this.totalPoints.toString().replace(/,/g, ''))
    let restPts = totalPoints - myPoints
    this.renderChart({
      labels: [' My Points', ' Rest'],
      datasets: [
        {
          label: this.label,
          backgroundColor: ['#007bff', 'lightgray'],
          data: [Math.round(myPoints), Math.round(restPts)]
        }
      ]
    }, {
      legend: {
        display: false
      }
    })
  }
}
