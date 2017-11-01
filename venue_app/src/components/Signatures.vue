<template>
  <div class="page-container">
    <b-row>
      <b-col>
        <h2>{{ $t('signatures') }}</h2>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <b-form>
          <b-row>
            <b-col md="4" sm="12">
              <b-form-group 
                id="forum-site-select-group" 
                label="Select forum site:" 
                label-for="forum-site-select">
                <b-form-select id="forum-site-select"
                  :options="forumSites" 
                  v-model="form.forumSite">
                </b-form-select>
              </b-form-group>
            </b-col>
            <b-col></b-col>
          </b-row>
        </b-form>
      </b-col>
    </b-row>
    <b-row v-for="signature in signatures">
      <b-col>
        <h5>{{ signature.name }}</h5>
        <div class="signature-banner">
          <img src="https://dummyimage.com/600x90/baa6ba/989bba">
        </div>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Signatures',
  data () {
    return {
      form: {
        forumSite: 1
      },
      forumSites: [],
      signatures: [
        {name: 'Hero', code: 'sample code'},
        {name: 'Superhero', code: 'sample code'}
      ]
    }
  },
  created () {
    // Get forum sites
    axios.get('/api/forum-sites/').then(response => {
      for (var elem of response.data) {
        this.forumSites.push({value: elem.id, text: elem.name})
      }
    })
  }
}
</script>

<style scoped>
  .signature-banner {
    padding-bottom: 10px;
    padding-left: 30px;
  }
</style>