import { Line } from 'vue-chartjs'

export default {
  extends: Line,
  props: ['data'],
  mounted () {
    let dates = this.data.map(function (value, index) {
      return value.date
    })
    let posts = this.data.map(function (value, index) {
      return value.posts
    })
    let rankings = this.data.map(function (value, index) {
      return value.rank
    })
    this.renderChart({
      labels: dates,
      datasets: [{
        label: 'Posts',
        yAxisID: 'A',
        lineTension: 0,
        backgroundColor: 'rgba(221, 76, 61, 0.5)', // '#dd4c3d',
        data: posts.map(function (v, i, a) {
          if (i === 0) {
            return 0
          } else {
            return (v - a[i - 1])
          }
        })
      }, {
        label: 'Ranking',
        yAxisID: 'B',
        lineTension: 0,
        backgroundColor: 'rgba(46, 56, 71, 0.5)', // '#2e3847',
        data: rankings
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
