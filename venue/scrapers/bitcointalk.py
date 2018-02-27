import requests
from bs4 import BeautifulSoup
from django.conf import settings
from hashids import Hashids

class ScraperError(Exception): pass

class BitcoinTalk(object):
    
    def __init__(self):
        self.base_url = 'https://bitcointalk.org'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) '
                'AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
            'Host': 'bitcointalk.org',
            'Origin': self.base_url,
            'Referer': self.base_url
        }
        self.status_code = None
        
    def list_forum_positions(self):
        positions = [
            'Brand New',
            'Newbie',
            'Jr. Member',
            'Member',
            'Full Member',
            'Sr. Member',
            'Hero Member',
            'Legendary'
        ]
        return positions
        
    def set_params(self, forum_profile_id, forum_user_id, expected_links):
        self.forum_profile_id = forum_profile_id
        self.forum_user_id = forum_user_id
        self.expected_links = expected_links
        
    def get_profile(self, user_id):
        if user_id.startswith('http'):
            profile_url = user_id
        else:
            profile_url = self.base_url + '/index.php?action=profile;u=' + str(user_id)
        self.response = requests.get(profile_url, headers=self.headers)
        self.status_code = self.response.status_code
        self.soup = BeautifulSoup(self.response.content, 'html.parser')
        
    def get_total_posts(self):
        row = self.soup.select('div#bodyarea tr')[4]
        #if 'Posts' in row.text:
        return int(row.text.split()[-1])
        #else:
        #    raise ScraperError('Cannot get total posts')
            
    def get_user_position(self):
        try:
            row = self.soup.select('div#bodyarea tr')[7]
            if 'Position' in row.text:
                pos_td = row.find_all('td')[1]
                return pos_td.text.strip()
            else:
                raise ScraperError('Cannot get user position')
        except IndexError:
            return ''

    def get_username(self):
        try:
            row = self.soup.select('div#bodyarea tr')[3]
            if 'Name' in row.text:
                pos_td = row.find_all('td')[1]
                return pos_td.text.strip()
            else:
                raise ScraperError('Cannot get username')
        except IndexError:
            return ''
            
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
        sig = self.soup.select('div#bodyarea tr')[26]
        # Find links and check their integrity
        links = sig.find_all('a')
        if links:
            links = [x.attrs['href'] for x in links]
        else:
            links = sig.text.strip().splitlines() 
        links_verified, vcode = self.verify_links(links, self.expected_links)
        if vcode:
            code_verified = self.verify_code(vcode.strip(), self.forum_profile_id, self.forum_user_id)
        else:
            code_verified = False
        sig_found = False
        if links_verified and code_verified:
            sig_found = True
        return sig_found
        
def verify_and_scrape(forum_profile_id, forum_user_id, expected_links, test_mode=False):
    scraper = BitcoinTalk()
    scraper.set_params(forum_profile_id, forum_user_id, expected_links)
    scraper.get_profile(forum_user_id)
    username = scraper.get_username()
    if test_mode:
        data = (scraper.status_code, True, scraper.get_total_posts(), username)
    else:
        verified = scraper.check_signature()
        posts = 0
        if verified:
            posts = scraper.get_total_posts()
        data = (scraper.status_code, verified, posts, username)
    return data
    
def get_user_position(forum_user_id):
    scraper = BitcoinTalk()
    scraper.get_profile(forum_user_id)
    position = scraper.get_user_position()
    return (scraper.response.status_code, position)
    
def extract_user_id(profile_url):
    return profile_url.split('profile;u=')[-1].strip()