<template>
  <!-- Login Modal -->
  <b-modal 
    id="leaderboard-modal" 
    :title="$i18n.t('leaderboard')" 
    ref="leaderboardModal" centered hide-footer>
    <h3>The leaderboard content goes here!</h3>
  </b-modal>
</template>

<script>
export default {
  name: 'LeaderboardModal'
}
</script>