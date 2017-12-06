from bs4 import BeautifulSoup
from django.conf import settings
from hashids import Hashids
import requests

class BitcoinForum(object):
    
    def __init__(self, username, password):
        self.login_url = 'https://forum.bitcoin.com/ucp.php?mode=login'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) '
                'AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
            'Origin': 'https://forum.bitcoin.com',
            'Host': 'forum.bitcoin.com',
            'Referer': self.login_url
        }
        self.cookies = {}
        self.status_code = None
        self.login(username, password)
        
    def list_forum_positions(self):
        positions = [
            'Nickel Bitcoiner',
            'Bronze Bitcoiner',
            'Silver Bitcoiner',
            'Gold Bitcoiner',
            'Platinum Bitcoiner',
            'Junior Mod',
            'Global Moderator',
            'Site Admin',
            'Founder'
        ]
        return positions
        
    def set_params(self, forum_profile_id, forum_user_id, expected_links):
        self.forum_profile_id = forum_profile_id
        self.forum_user_id = forum_user_id
        self.expected_links = expected_links
        
    def send_get(self, url):
        headers = self.headers
        if self.cookies:
            return requests.get(url, headers=headers, cookies=self.cookies)
        return requests.get(url, headers=headers)
        
    def send_post(self, url, payload):
        return requests.post(url, payload, headers=self.headers)
    
    def login(self, username, password):
        resp = self.send_get(self.login_url)
        self.status_code = resp.status_code
        payload = {
            'username': username,
            'password': password,
            'redirect': self.login_url,
            'sid': resp.cookies['btcfora_phpbb_sid'],
            'login': 'Login'
        }
        resp = self.send_post(self.login_url, payload)
        self.cookies = resp.history[0].cookies
        return resp
        
    def get_profile(self, user_id):
        if str(user_id).startswith('http'):
            url = user_id
        else:
            url = 'https://forum.bitcoin.com/hungnx-u%s/' % user_id
        self.response = self.send_get(url)
        self.soup = BeautifulSoup(self.response.content, 'html.parser')
        
    def get_total_posts(self):
        elem = self.soup.select('div.bg2 div.column2 dl.details dd')
        return elem[2].text.split()[0]
        
    def get_user_position(self):
        position = 'No rank'
        elem = self.soup.select('div.bg1 dl.left-box dd')
        if elem:
            try:
                position = elem[1].img.attrs['title']
            except AttributeError:
                pass
        if not position:
            details = {}
            dt_keys = self.soup.select('div.bg1 dl.profile-details dt')
            dt_values = self.soup.select('div.bg1 dl.profile-details dd')
            for i, dk in enumerate(dt_keys):
                key = dk.text.strip().replace(':', '')
                if dt_values[i]:
                    details[key] = dt_values[i].text.strip()
            if 'Rank' in details.keys():
                position = details['Rank']
        return position
        
    def verify_code(self, code, forum_profile_id, forum_user_id):
        hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)
        numbers = hashids.decode(code)
        verified = False
        if numbers == (forum_profile_id, int(forum_user_id)):
            verified = True
        return verified
        
    def verify_links(self, scraped_links, expected_links):
        verified = False
        vcode = None
        if scraped_links:
            links = []
            for link in scraped_links:
                try:
                    clean_link, vcode = link.split('vcode=')
                    vcode = vcode.split('&')[0]
                    links.append(clean_link.replace('?', ''))
                except ValueError:
                    pass
            if set(links) == set(expected_links):
                verified = True
        return (verified, vcode)
        
    def check_signature(self):
        sig_found = False
        sig_div = self.soup.select('div.signature')
        if sig_div:
            # Find links and check their integrity
            links = sig_div[0].find_all('a')
            if links:
                links = [x.attrs['href'] for x in links]
            else:
                links = sig_div[0].text.strip().splitlines() 
            links_verified, vcode = self.verify_links(links, self.expected_links)
            code_verified = False
            if vcode:
                code_verified = self.verify_code(vcode.strip(), self.forum_profile_id, self.forum_user_id)
            if links_verified and code_verified:
                sig_found = True
        return sig_found
        
default_credentials = {
    'username': 'joemarct',
    'password': 'a8L2f4a6%ojZ'
}

def verify_and_scrape(forum_profile_id, forum_user_id, expected_links, test_mode=False, credentials=None):
    if not credentials:
        credentials = default_credentials
    scraper = BitcoinForum(credentials['username'], credentials['password'])
    scraper.set_params(forum_profile_id, forum_user_id, expected_links)
    scraper.get_profile(forum_user_id)
    if test_mode:
        data = (scraper.status_code, True, scraper.get_total_posts())
    else:
        verified = scraper.check_signature()
        posts = 0
        if verified:
            posts = scraper.get_total_posts()
        data = (scraper.status_code, verified, posts)
    return data
    
def get_user_position(forum_user_id, credentials=None):
    if not credentials:
        credentials = default_credentials
    scraper = BitcoinForum(credentials['username'], credentials['password'])
    scraper.get_profile(forum_user_id)
    position = scraper.get_user_position()
    return (scraper.response.status_code, position)
    
def extract_user_id(profile_url):
    return profile_url.strip('/').split('/')[-1].split('-u')[-1]