import { check, sleep, group } from "k6";
import http from 'k6/http';
import BaseTest from '../BaseTest.js';
import { API_NAME, BASE_URL } from '../constants.js';

import {nextUser} from '../users.js';

// let count = 1;

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
        
        var date1 = new Date();
        var responseLogin = http.post(this.URL, payload, params1);
        var date2 = new Date();
        console.log("Login took: " + (date2.getTime() - date1.getTime()));
        
       
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
        
        // now lets get the stats
        var params2 =  { 
            headers: { 
                "Content-Type": "application/json" ,
                "authorization": "Token " + body.token
            } 
        };

        date1 = new Date();var date1 = new Date();
        var responseStats = http.get(`${BASE_URL}/api/retrieve/stats/`, params2);
        date2 = new Date();
        console.log("Stats took: " + (date2.getTime() - date1.getTime()));
        
        check(responseStats, {
            "is statsstatus 200": (r) => r.status === 200
        });

       
        var params3 =  { 
            headers: { 
                "Content-Type": "application/json"
            } 
        };

        date1 = new Date();var date1 = new Date();
        var responseLeaderboard = http.get(`${BASE_URL}/api/retrieve/leaderboard-data/`, params3);
        date2 = new Date();
        console.log("leaderboard took: " + (date2.getTime() - date1.getTime()));
        //console.log("Status: " + responseLeaderboard.status + " Count: " + count++)
        check(responseLeaderboard, {
            "is statsstatus 200": (r) => r.status === 200
        });
        
        var params4 =  { 
            headers: { 
                "Content-Type": "application/json" ,
                "authorization": "Token " + body.token
            } 
        };
        date1 = new Date();var date1 = new Date();
        var responseLogout = http.get(`${BASE_URL}/api/logout/`, params4);
        date2 = new Date();
        console.log("logout took: " + (date2.getTime() - date1.getTime()));
        
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