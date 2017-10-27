import requests
from bs4 import BeautifulSoup

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
            raise ScraperError('Page has changed')
        
    def check_signature(self, signature_code):
        sig = self.soup.select('div#bodyarea tr')[25]
        sig_found = False
        if 'Signature' in sig.text:
            if signature_code in sig.parent.text:
                sig_found = True
        else:
            raise ScraperError('Page has changed')
        return sig_found
        
def execute(user_id, signature_code):
    scraper = BitcoinTalk()
    scraper.get_profile(user_id)
    data = (scraper.get_total_posts(), scraper.check_signature(signature_code))
    return data