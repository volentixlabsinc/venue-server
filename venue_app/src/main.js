// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from '@/App'
import router from '@/router'
import store from '@/store'
import BootstrapVue from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import en from 'vee-validate/dist/locale/en'
import ja from 'vee-validate/dist/locale/ja'
import VeeValidate from 'vee-validate'
import VueI18n from 'vue-i18n'
import messages from '@/translations'
import VueClipboards from 'vue-clipboards'
import VueSwal from 'vue-swal'
import VueCookies from 'vue-cookies'
import VueProgressBar from 'vue-progressbar'
import VueQRCodeComponent from 'vue-qrcode-component'
import axios from 'axios'
import Rollbar from 'vue-rollbar'
import numeral from 'numeral'
import VueNativeSock from 'vue-native-websocket'


const options = {
  color: '#2a96b6',
  failedColor: '#c82333',
  thickness: '5px',
  transition: {
    speed: '0.2s',
    opacity: '0.6s',
    termination: 300
  },
  autoRevert: true,
  location: 'top',
  inverse: false
}

Vue.use(VueProgressBar, options)
Vue.use(Rollbar, {
  accessToken: '5a9b5663381543638d778e472f571805',
  captureUncaught: true,
  captureUnhandledRejections: true,
  payload: {
    environment: 'debug'
  }
})

axios.defaults.xsrfHeaderName = 'X-CSRFTOKEN'
axios.defaults.xsrfCookieName = 'csrftoken'

let env = process.env.NODE_ENV || 'development'
var websocketUrl
if (env === 'development') {
  axios.defaults.baseURL = 'http://localhost:8000'
  websocketUrl = 'ws://localhost:8000/ws/foobar?subscribe-broadcast'
} else {
  axios.defaults.baseURL = 'https://venue.volentix.com'
  websocketUrl = 'wss://venue.volentix.com/ws/foobar?subscribe-broadcast'
}

Vue.use(VueNativeSock, websocketUrl, {
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 3000
})

Vue.use(VueCookies)
Vue.use(VueSwal)
Vue.use(VueClipboards)
Vue.use(VueI18n)
Vue.use(BootstrapVue)
Vue.component('qr-code', VueQRCodeComponent)

Vue.config.productionTip = false

Vue.use(VeeValidate, {
  locale: 'en',
  dictionary: { en, ja }
})

const i18n = new VueI18n({
  locale: 'en',
  messages
})

Vue.config.devtools = false
Vue.config.productionTip = false

Vue.filter('thousands_sep', function (value) {
  try {
    return numeral(value).format('0,0')
  } catch (err) {
    return value
  }
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  i18n,
  store,
  router,
  template: '<App/>',
  components: { App }
})
