var fs = require('fs')
const uuidv4 = require('uuid/v4');
const Mustache = require('mustache')

var template = fs.readFileSync(__dirname + '/0002_auto_20180710_0208.py.template', 'utf8');
//console.log(template)

let form_records = [];
let users = [];
let form_posts = [];

var rankIds = [
    '09a7ad5e-1da4-4e7b-8799-93cf70ceb6f0',
    '99c3f7d6-8adf-4594-a7d3-b64d47488c5a',
    'dd1bbfa7-a3c3-4163-8c0d-b04eb84db9ad',
    '065d2e38-295e-4b31-9da8-2946aaee5be1',
    '14d22df0-3462-492b-81c5-b5812d3ef777'
]

for (let i = 1; i < 101; i += 1) {

    users.push({
        'password': 'default2018',
        'username': 'perf' + i,
        'email': 'perf' + i + '@nomail.com',
        'is_active': true
    })
    

    var profileid = uuidv4();
    var ran = Math.round(Math.random() * Math.floor(4));
    var rankid = rankIds[ran];
    console.log(ran)
    //console.log(rankid + " ::::::::::::::" + ran);
    form_records.push(
    {
        'id': profileid,
        'forum_id': '4b8b11d1-14bb-46a7-ac8b-397587235b28',
        'forum_rank_id': rankid,
        'forum_username': 'perf' + i,
        'forum_user_id': '' + i,
        'signature_id': '5a506e4d-f5b6-408e-9e00-39f5b7521351',
        'verification_code': '18pTZWD' + i,
        'active': true,
        'verified': true,
        'date_verified': '2018-06-10 03:27:46+00:00',
        'date_added': '2018-06-10 03:27:56+00:00',
        'date_updated': '2018-06-16 03:53:08.829000+00:00',
        'dummy': true
    })
    var numPosts = Math.round(Math.random() * Math.floor(15));

    if (numPosts < 5 ) {
        numPosts = 5;
    }

    for (let p = 1; p < numPosts; p++ ){
        form_posts.push({
            'base_points': '100.00', 
            'credited': true, 
            'date_credited': 
            '2018-06-14 14:32:28+00:00', 
            'date_matured': '2018-06-14 14:32:30+00:00', 
            'influence_bonus_pct': ran + '.00', 
            'influence_bonus_pts': ran + '.00', 
            'invalid_sig_minutes': 0, 
            'matured': true, 
            'message_id': '30' + i + '0' + p, 
            'timestamp': '2018-06-13 14:18:40+00:00', 
            'topic_id': '4' + i + ran + p, 
            'total_points': '100.00', 
            'unique_content_length': 400 + (i * p), 
            'valid_sig_minutes': 1440, 
            'forum_profile_id': profileid, 
            'forum_rank_id': rankid
        })
    }
    
}
var rendered = Mustache.render(template, {
    users: JSON.stringify(users, null, 2).replace(/true/g, 'True'),
    formprofiles: JSON.stringify(form_records, null, 2).replace(/true/g, 'True'),
    formposts: JSON.stringify(form_posts, null, 2).replace(/true/g, 'True')
});
//console.log(rendered)
fs.writeFileSync(__dirname + '/0002_auto_20180710_0208.py', rendered, 'utf8');

//console.log(JSON.stringify(users).replace(/true/g, 'True'));
//console.log(JSON.stringify(form_records).replace(/true/g, 'True'));
//console.log(JSON.stringify(form_posts, null, 2).replace(/true/g, 'True'));


