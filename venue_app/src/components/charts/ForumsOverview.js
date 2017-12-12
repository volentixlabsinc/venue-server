import { HorizontalBar, mixins } from 'vue-chartjs'

export default {
  extends: HorizontalBar,
  mixins: [mixins.reactiveProp],
  props: ['data'],
  mounted () {
    this.renderChart({
      datasets: [
        {
          label: 'Bitcoin Forum',
          backgroundColor: 'red',
          data: [35]
        },
        {
          label: 'Bitcoin Talk',
          backgroundColor: 'yellow',
          data: [89]
        }
      ]
    }, {
      legend: {
        display: false
      },
      scales: {
        xAxes: {
          stacked: true
        },
        yAxes: {
          stacked: true
        }
      }
    })
  }
}
