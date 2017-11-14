import requests
from bs4 import BeautifulSoup
from django.conf import settings
from hashids import Hashids

class ScraperError(Exception): pass

class BitcoinTalk(object):
    
    def __init__(self):
        self.base_url = 'https://bitcointalk.org'
        
    def set_params(self, forum_profile_id, forum_user_id, expected_links):
        self.forum_profile_id = forum_profile_id
        self.forum_user_id = forum_user_id
        self.expected_links = expected_links
        
    def get_profile(self, user_id):
        if user_id.startswith('http'):
            profile_url = user_id
        else:
            profile_url = self.base_url + '/index.php?action=profile;u=' + str(user_id)
        self.response = requests.get(profile_url)
        self.soup = BeautifulSoup(self.response.content, 'html.parser')
        
    def get_total_posts(self):
        row = self.soup.select('div#bodyarea tr')[4]
        if 'Posts' in row.text:
            return int(row.text.split()[-1])
        else:
            raise ScraperError('Cannot get total posts')
            
    def get_user_position(self):
        try:
            row = self.soup.select('div#bodyarea tr')[6]
            if 'Position' in row.text:
                pos_td = row.find_all('td')[1]
                return pos_td.text.strip()
            else:
                raise ScraperError('Cannot get user position')
        except IndexError:
            return ''
            
    def verify_code(self, code, forum_profile_id, forum_user_id):
        hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)
        numbers = hashids.decode(code)
        verified = False
        if numbers == (forum_profile_id, forum_user_id):
            verified = True
        return verified
        
    def verify_links(self, scraped_links, expected_links):
        verified = False
        vcode = None
        if scraped_links:
            links = []
            for link in links:
                code_check = x.split('vcode=')
                if len(code_check) == 2:
                    vcode = code_check[1].split('&')[0]
            if set(links) == set(expected_links):
                verified = True
        return (verified, vcode)
        
    def check_signature(self):
        sig = self.soup.select('div#bodyarea tr')[25]
        # Find links and check their integrity
        links = sig.find_all('a')
        if links:
            links = [x.attrs['href'] for x in links]
        links_verified, vcode = self.verify_links(links, self.expected_links)
        # Read the vcodes and verify
        code_verified = self.verify_code(vcode, self.forum_profile_id, self.forum_user_id)
        sig_found = False
        if links_verified and code_verified:
            sig_found = True
        return sig_found
        
def verify_and_scrape(forum_profile_id, forum_user_id, expected_links, test_mode=False):
    scraper = BitcoinTalk()
    scraper.set_params(forum_profile_id, forum_user_id, expected_links)
    scraper.get_profile(forum_user_id)
    if test_mode:
        data = (True, scraper.get_total_posts())
    else:
        verified = scraper.check_signature()
        posts = None
        if verified:
            posts = scraper.get_total_posts()
        data = (verified, posts)
    return data
    
def get_user_position(forum_user_id):
    scraper = BitcoinTalk()
    scraper.get_profile(forum_user_id)
    position = scraper.get_user_position()
    return (scraper.response.status_code, position)
    
def extract_user_id(profile_url):
    return profile_url.split('profile;u=')[-1].strip()