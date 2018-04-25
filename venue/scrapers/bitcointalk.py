import time
import requests
from hashids import Hashids
from bs4 import BeautifulSoup
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class ScraperError(Exception):
    pass


class BitcoinTalk(object):

    def __init__(self, test=False, test_signature=None):
        self.base_url = 'https://bitcointalk.org'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) '
                'AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
            'Host': 'bitcointalk.org',
            'Origin': self.base_url,
            'Referer': self.base_url
        }
        self.status_code = None
        self.soup = None
        self.test = test
        self.test_signature = test_signature
        
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
            profile_url = self.base_url + '/index.php?action=profile;u='
            profile_url += str(user_id)
        response = requests.get(profile_url, headers=self.headers)
        self.status_code = response.status_code
        self.soup = BeautifulSoup(response.content, 'html.parser')
        if len(self.soup.select('div.cf-im-under-attack')) > 0:
            driver = webdriver.Remote(
                'http://127.0.0.1:4444/wd/hub',
                DesiredCapabilities.CHROME
            )
            driver.get(profile_url)
            # Sleep to wait for the page to load
            time.sleep(6)
            self.soup = BeautifulSoup(driver.page_source, 'html.parser')
            if self.get_username():
                self.status_code = 200
            driver.close()
            driver.quit()

    def get_total_posts(self):
        row = self.soup.select('div#bodyarea tr')[4]
        return int(row.text.split()[-1])

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
        verified = False
        if self.test:
            if code.strip() == self.test_signature.strip():
                verified = True
        else:
            hashids = Hashids(min_length=8, salt=settings.SECRET_KEY)
            numbers = hashids.decode(code.strip())
            if numbers == (forum_profile_id, int(forum_user_id)):
                verified = True
        return verified
        
    def verify_links(self,
                     scraped_links,
                     expected_links,
                     scraped_signature=None):
        verified = False
        vcode = None
        if self.test:
            if self.test_signature.strip() == scraped_signature.strip():
                verified = True
            return (verified, scraped_signature)
        else:
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
        links_verified, vcode = self.verify_links(
            links,
            self.expected_links,
            scraped_signature=sig.text
        )
        if vcode:
            code_verified = self.verify_code(
                vcode.strip(),
                self.forum_profile_id,
                self.forum_user_id
            )
        else:
            code_verified = False
        sig_found = False
        if links_verified and code_verified:
            sig_found = True
        return sig_found


def verify_and_scrape(forum_profile_id,
                      forum_user_id,
                      expected_links,
                      test_mode=False,
                      test_signature=None):
    scraper = BitcoinTalk(test=test_mode, test_signature=test_signature)
    scraper.set_params(forum_profile_id, forum_user_id, expected_links)
    scraper.get_profile(forum_user_id)
    username = scraper.get_username()
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
    username = scraper.get_username()
    return (scraper.status_code, position, username)


def extract_user_id(profile_url):
    user_id = profile_url.split('profile;u=')[-1]
    user_id = user_id.split(';')[0].strip()
    return user_id
