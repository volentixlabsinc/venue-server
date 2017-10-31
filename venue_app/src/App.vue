<template>
  <div id="app" v-cloak>
    <top-navigation></top-navigation>
    <b-container id="main-container">
      <router-view></router-view>
    </b-container>
  </div>
</template>

<script>
import TopNavigation from '@/components/TopNavigation'

export default {
  name: 'app',
  components: { TopNavigation }
}
</script>

<style>
#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
#main-container {
  padding-top: 15px;
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
