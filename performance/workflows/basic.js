import { check, sleep, group } from "k6";
import http from 'k6/http';
import BaseTest from '../BaseTest.js';
import { API_NAME, BASE_URL } from '../constants.js';

import {nextUser} from '../users.js';

class Basic extends BaseTest {
  constructor() {
    super('Fetch Comments');
    this.API_NAME = API_NAME;
    this.projects = ['venue'];
    this.URL = `${BASE_URL}/api/authenticate/`;
    this.LATEST_PERFORMANCE = 600.0;
  }

  test() {
    group(this.TEST_NAME, () => {
        var payload = nextUser().rstring
        //console.log(payload);
        var params1 =  { headers: { "Content-Type": "application/json" } }
        var responseLogin = http.post(this.URL, payload, params1);

       
        if (responseLogin.status != 200 ) {
            console.log("Status Logout: " + responseLogin.status);
            console.log(payload);
            console.log(responseLogin.body)
        }

       check(responseLogin, {
            "is status 200": (r) => r.status === 200
        });
        
        var body = JSON.parse(responseLogin.body);
        var token = body.token;
        check(body, {
            "is success true": (b) => b.success === true,
            "email is confirmed": (b) => b.email_confirmed === true,
            "lang is en": (b) => b.language === 'en'
        });
        
      /*
        // now lets get the stats
        var params2 =  { 
            headers: { 
                "Content-Type": "application/json" ,
                "authorization": "Token " + body.token
            } 
        };

         
        var responseStats = http.get(`${BASE_URL}/api/retrieve/stats/`, params2);
        check(responseStats, {
            "is statsstatus 200": (r) => r.status === 200
        });
        var statsBody = JSON.parse(responseStats.body);
        check(statsBody, {
            "is stats success true": (b) => b.success === true,
            "stats user bct userid correct": (b) => b.stats.profile_level[0].forumUserId === '1216831',
            "stats user bct user rank correct": (b) => b.stats.profile_level[0].forumUserRank === 'Legendary'
        });

       
        var params3 =  { 
            headers: { 
                "Content-Type": "application/json"
            } 
        };
        var responseLeaderboard = http.get(`${BASE_URL}/api/retrieve/leaderboard-data/`, params3);
        check(responseLeaderboard, {
            "is statsstatus 200": (r) => r.status === 200
        });
        */
       
        var params4 =  { 
            headers: { 
                "Content-Type": "application/json" ,
                "authorization": "Token " + body.token
            } 
        };
        var responseLogout = http.get(`${BASE_URL}/api/logout/`, params4);

        if (responseLogout.status != 200 ) {
            console.log("Status Logout: " + responseLogout.status);
            console.log(responseLogout.body)
        }
        
        check(responseLogout, {
            "is logout status 200": (r) => r.status === 200
        });
        var statslogout = JSON.parse(responseLogout.body);
        check(statslogout, {
            "is logout success true": (b) => b.success === true
        });

    });
  }
}

export const basicInstance = new Basic();
export default () => basicInstance.test();