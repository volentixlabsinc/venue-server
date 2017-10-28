<template>
  <div id="app" v-cloak>
    <top-navigation></top-navigation>
    <b-container fluid>
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
.help {
  display: block;
  color: red;
}
[v-cloak] { display:none; }
</style>
