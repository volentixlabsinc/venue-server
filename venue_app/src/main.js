// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from '@/App'
import router from '@/router'
import store from '@/store'
import BootstrapVue from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import VeeValidate from 'vee-validate'
import VueI18n from 'vue-i18n'
import messages from '@/translations'
import VueClipboards from 'vue-clipboards'
import VueSwal from 'vue-swal'
import VueCookies from 'vue-cookies'
import VueProgressBar from 'vue-progressbar'
import axios from 'axios'

const options = {
  color: '#007bff',
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

axios.defaults.xsrfHeaderName = 'X-CSRFTOKEN'
axios.defaults.xsrfCookieName = 'csrftoken'

// axios.defaults.baseURL = 'http://localhost:8000'

Vue.use(VueCookies)
Vue.use(VueSwal)
Vue.use(VueClipboards)
Vue.use(VueI18n)
Vue.use(VeeValidate)
Vue.use(BootstrapVue)
Vue.config.productionTip = false

const i18n = new VueI18n({
  locale: 'en',
  messages
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
