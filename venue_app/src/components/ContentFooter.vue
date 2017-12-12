<template>
  <b-containter>
    <b-row id="footer">
      <b-col>
        <span>Volentix Labs, Inc.</span>
        <span style="float: right;">Frequently Asked Questions (FAQs)</span>
      </b-col>
    </b-row>
  </b-containter>
</template>

<<script>
export default {
  name: 'ContentFooter',
  methods: {
    getDocumentHeight () {
      let body = document.body
      let html = document.documentElement

      return Math.max(body.scrollHeight, body.offsetHeight,
          html.clientHeight, html.scrollHeight, html.offsetHeight)
    },
    getWindowHeight () {
      return document.documentElement.clientHeight
    },
    getWindowWidth () {
      return document.documentElement.clientWidth
    }
  },
  mounted () {
    let footerBox = this.$refs.footer.getBoundingClientRect()
    console.log(footerBox.y)
    console.log(this.getDocumentHeight())
    console.log(this.getWindowHeight())
    let docHeight = this.getDocumentHeight()
    let winHeight = this.getWindowHeight()
    // let winWidth = this.getWindowWidth()
    if (docHeight === winHeight) {
      document.getElementById('footer').setAttribute('style', 'background: red;')
    }
  }
}
</script>

<style scoped>
#footer {
  background-color: rgb(52, 58, 63);
  padding: 20px;
  position: fixed;
  right: 0;
  left: 0;
  bottom: 0;
  color: white;
}
</style>
