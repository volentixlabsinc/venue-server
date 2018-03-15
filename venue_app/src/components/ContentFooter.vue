<template>
  <b-container>
    <b-row id="footer">
      <b-col>
        <img src="../assets/logo.png" height="40">
        <span style="float: right; line-height: 40px;">{{ $t('faq') }}</span>
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
export default {
  name: 'ContentFooter'
}
</script>

<style scoped>
#footer {
  background-color: #232C3B;
  padding: 10px;
  position: fixed;
  right: 0;
  left: 0;
  bottom: 0;
  color: white;
}
</style>
