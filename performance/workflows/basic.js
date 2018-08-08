import { check, sleep, group } from "k6";
import http from 'k6/http';
import BaseTest from '../BaseTest.js';
import { API_NAME, BASE_URL } from '../constants.js';

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


        var payload = '{"username":"thor","password":"default2018"}';
        var params =  { headers: { "Content-Type": "application/json" } }
        var responseLogin = http.post(this.URL, payload, params);

       check(responseLogin, {
            "is status 200": (r) => r.status === 200
        });
        
        var body = JSON.parse(responseLogin.body);
        var token = body.token;
        check(body, {
            "is success true": (b) => b.success === true,
            "username is Thor": (b) => b.username === 'thor',
            "email is good": (b) => b.email === 'joemar.ct+thor@gmail.com',
            "email is confirmed": (b) => b.email_confirmed === true,
            "lang is en": (b) => b.language === 'en'
        });
        
        // now lets get the stats
        var params =  { 
            headers: { 
                "Content-Type": "application/json" ,
                "authorization": "Token " + body.token
            } 
        };
        var responseStats = http.get(`${BASE_URL}/api/retrieve/stats/`, params);
        check(responseStats, {
            "is statsstatus 200": (r) => r.status === 200
        });
        var statsBody = JSON.parse(responseStats.body);
        check(statsBody, {
            "is stats success true": (b) => b.success === true,
            "stats user bct userid correct": (b) => b.stats.profile_level[0].forumUserId === '1216831',
            "stats user bct user rank correct": (b) => b.stats.profile_level[0].forumUserRank === 'Legendary'
        });
        
        var params =  { 
            headers: { 
                "Content-Type": "application/json" ,
                "authorization": "Token " + body.token
            } 
        };
        var responseLogout = http.get(`${BASE_URL}/api/logout/`, params);
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