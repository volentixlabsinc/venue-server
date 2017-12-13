import { HorizontalBar, mixins } from 'vue-chartjs'

export default {
  extends: HorizontalBar,
  mixins: [mixins.reactiveProp],
  props: ['data', 'title'],
  mounted () {
    let sites = this.data.map(function (i) {
      return i.forumSite
    })
    let values = this.data.map(function (i) {
      return i.value
    })
    let colors = this.data.map(function (i) {
      return i.color
    })
    this.renderChart({
      labels: sites,
      datasets: [
        {
          label: this.title,
          backgroundColor: colors,
          data: values
        }
      ]
    }, {
      legend: {
        display: false
      },
      scales: {
        yAxes: [{
          ticks: {
            display: true
          }
        }],
        xAxes: [{
          ticks: {
            min: 0,
            beginAtZero: true,
            stepSize: 1
          }
        }]
      }
    })
  }
}
