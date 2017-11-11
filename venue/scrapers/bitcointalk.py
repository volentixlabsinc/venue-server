import requests
from bs4 import BeautifulSoup
from django.conf import settings
from hashids import Hashids

class ScraperError(Exception): pass

class BitcoinTalk(object):
    
    def __init__(self):
        self.base_url = 'https://bitcointalk.org'
    
    def get_profile(self, user_id):
        profile_url = self.base_url + '/index.php?action=profile;u=' + user_id
        resp = requests.get(profile_url)
        self.soup = BeautifulSoup(resp.content, 'html.parser')
        
    def get_total_posts(self):
        row = self.soup.select('div#bodyarea tr')[4]
        if 'Posts' in row.text:
            return int(row.text.split()[-1])
        else:
            raise ScraperError('Cannot get total posts')
            
    def get_user_position(self):
        row = soup.select('div#bodyarea tr')[5]
        if 'Position' in row.text:
            return row.text.strip().split()[-1]
        else:
            return ScrapingError('Cannot get user position')
            
    def verify_code(self, code, forum_profile_id, forum_user_id):
        hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)
        numbers = hashids.decode(code)
        verified = False
        if numbers == (forum_profile_id, forum_user_id):
            verified = True
        return verified
        
    def check_signature(self, signature_code):
        sig = self.soup.select('div#bodyarea tr')[25]
        sig_found = False
        if 'Signature' in sig.text:
            if signature_code in sig.parent.text:
                sig_found = True
        else:
            raise ScraperError('Page has changed')
        return sig_found
        
def execute(user_id, signature_code, test_mode=False):
    scraper = BitcoinTalk()
    scraper.get_profile(user_id)
    if test_mode:
        data = (scraper.get_total_posts(), True)
    else:
        data = (scraper.get_total_posts(), scraper.check_signature(signature_code))
    return data
    
def verify_profile_signature(profile_url):
    # TODO -- Check for the presence of our signature in the given profile page
    return True