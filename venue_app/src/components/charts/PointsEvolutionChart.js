import { Line } from 'vue-chartjs'

export default {
  extends: Line,
  mounted () {
    this.renderChart({
      labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
      datasets: [{
        label: 'Points Evolution',
        yAxisID: 'A',
        lineTension: 0,
        backgroundColor: 'rgba(221, 76, 61, 0.5)', // '#dd4c3d',
        data: [40, 20, 12, 39, 10, 40, 39, 80, 40, 20, 12, 11]
      }, {
        label: 'Ranking Evolution',
        yAxisID: 'B',
        lineTension: 0,
        backgroundColor: 'rgba(46, 56, 71, 0.5)', // '#2e3847',
        data: [3, 5, 4, 8, 10, 9, 7, 4, 8, 10, 10, 9]
      }]
    }, {
      legend: {
        display: false
      },
      scales: {
        yAxes: [{
          id: 'A',
          type: 'linear',
          position: 'left'
        }, {
          id: 'B',
          type: 'linear',
          position: 'right'
        }]
      }
    })
  }
}
