<template>
  <div id="app" v-cloak @scroll="handleScroll($event)">
    <top-navigation></top-navigation>
    <vue-progress-bar></vue-progress-bar>
    <b-container id="main-container">
      <router-view></router-view>
    </b-container>
    <content-footer v-if="$store.state.showFooter"></content-footer>
  </div>
</template>

<script>
import TopNavigation from '@/components/TopNavigation'
import ContentFooter from '@/components/ContentFooter'

export default {
  name: 'app',
  components: { TopNavigation, ContentFooter },
  methods: {
    handleScroll () {
      if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight) {
        this.$store.commit('updateShowFooter', true)
      } else {
        this.$store.commit('updateShowFooter', false)
      }
    }
  },
  mounted () {
    window.addEventListener('scroll', this.handleScroll)
  },
  destroyed () {
    window.removeEventListener('scroll', this.handleScroll)
  }
}
</script>

<style>
#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height:100%;
  position:relative;
}
#main-container {
  padding-bottom: 90px;
}
.help {
  display: block;
  color: red;
}
.page-container h2 {
  margin-bottom: 20px;
}
[v-cloak] { display:none; }
</style>
