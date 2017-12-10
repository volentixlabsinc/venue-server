import { Line, mixins } from 'vue-chartjs'

export default {
  extends: Line,
  mixins: [mixins.reactiveProp],
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
        label: 'New Posts',
        yAxisID: 'A',
        lineTension: 0.2,
        backgroundColor: 'rgba(221, 76, 61, 0.5)', // '#dd4c3d',
        borderColor: '#dd4c3d',
        data: posts
      }, {
        label: 'Ranking',
        yAxisID: 'B',
        lineTension: 0.2,
        fill: 'bottom',
        backgroundColor: 'rgba(46, 56, 71, 0.5)', // '#2e3847',
        borderColor: '#2e3847',
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
          position: 'left',
          ticks: {
            beginAtZero: true
          },
          scaleLabel: {
            display: true,
            fontColor: '#dd4c3d',
            labelString: 'Number of New Posts'
          }
        }, {
          id: 'B',
          type: 'linear',
          position: 'right',
          ticks: {
            reverse: true
          },
          scaleLabel: {
            display: true,
            fontColor: '#2e3847',
            labelString: 'Ranking'
          }
        }]
      }
    })
  }
}
