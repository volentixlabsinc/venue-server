import time
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from dateutil import parser
# from selenium import webdriver
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from .exceptions import ScraperError, ProfileDoesNotExist

logger = settings.LOGGER


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
        self.response_text = None

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

    def make_request(self, url, proxies=None, verify=True):
        response = requests.get(
            url,
            headers=self.headers,
            proxies=proxies,
            verify=verify
        )
        self.response_text = response.text
        self.status_code = response.status_code
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def get_profile(self, user_id, fallback=None, test_config=None):
        profile_url = self.base_url + '/index.php?action=profile;u='
        profile_url += str(user_id)
        if test_config:
            profile_url = test_config['profile_url']
        if fallback == 'crawlera':
            # try to get data using crawlera
            proxies = settings.CRAWLERA_PROXIES
            self.make_request(url=profile_url, proxies=proxies, verify=False)
        if fallback == 'crawlera+selenium':
            # TODO -- This is a placeholder for the implementation of
            # Crawlera+Selenium scraping fallback
            pass
        if not fallback:
            self.make_request(url=profile_url, verify=False)
        # Check if profile exists
        body_area = self.soup.find('div', {'id': 'bodyarea'})
        if body_area:
            body_text = body_area.text
            if 'The user whose profile you are trying to view does not exist.' in body_text:
                raise ProfileDoesNotExist()

    def get_total_posts(self):
        row = self.soup.select('div#bodyarea tr')[4]
        return int(row.text.split()[-1])

    def get_user_position(self):
        try:
            rows = self.soup.select('div#bodyarea tr')
            found = False
            for row in rows:
                if 'Position' in row.text.strip()[0:10]:
                    found = True
                    pos_td = row.find_all('td')[1]
                    return pos_td.text.strip()
            if not found:
                raise ScraperError('Cannot get user position')
        except IndexError:
            return ''

    def get_username(self):
        try:
            rows = self.soup.select('div#bodyarea tr')
            found = False
            for row in rows:
                if 'Name' in row.text.strip()[0:10]:
                    found = True
                    text_list = row.text.split()
                    name_index = text_list.index('Name:')
                    return text_list[name_index + 1]
            if not found:
                raise ScraperError('Cannot get username')
        except IndexError:
            return ''

    def verify_links(self,
                     scraped_links,
                     expected_links,
                     scraped_signature=None):
        verified = False
        vcode = None
        if self.test:
            scraped_signature = scraped_signature.split('Signature:')[1]
            if self.test_signature.strip() == scraped_signature.strip():
                verified = True
            return (verified, scraped_signature)
        else:
            if scraped_links:
                links = []
                for link in scraped_links:
                    try:
                        if 'vcode=' in link: 
                            clean_link, vcode = link.split('vcode=')
                            vcode = vcode.split('&')[0]
                        else:
                            clean_link = link
                        links.append(clean_link.replace('?', ''))
                    except ValueError:
                        pass
                if set(links) == set(expected_links):
                    verified = True
        return (verified, vcode)

    def check_signature(self, vcode=None):
        sig = None
        page_ok = False
        if 'icons/profile_sm.gif' in self.response_text:
            page_ok = True
        try:
            rows = self.soup.select('div#bodyarea tr')
            found = False
            for row in rows:
                if 'Signature' in row.text.strip()[0:10]:
                    found = True
                    # text_list = row.text.split()
                    # name_index = text_list.index('Signature:')
                    sig = row
                    break
            if not found:
                # raise ScraperError('Cannot find signature')
                page_ok = False
        except IndexError:
            pass
        if sig:
            # Find links and check their integrity
            links = sig.find_all('a')
            if links:
                links = [x.attrs['href'] for x in links]
            else:
                links = sig.text.strip().splitlines()
            if links:
                links = list(set(links))
            else:
                links = []
            links_verified, scraped_vcode = self.verify_links(
                links,
                self.expected_links,
                scraped_signature=sig.text
            )
            code_verified = False
            if self.test:
                code_verified = True
            else:
                if vcode and scraped_vcode:
                    if vcode == scraped_vcode:
                        code_verified = True
                else:
                    code_verified = True
            sig_found = False
            if links_verified and code_verified:
                sig_found = True
        else:
            sig_found = False
        return (page_ok, sig_found)

    def _scrape_posts_page(self, soup, start=None):
        post_details = []
        posts = soup.select('.post')
        check_datetime = timezone.now()
        start_reached = False
        for post in posts:
            header = post.parent.parent.parent.select('tr')[0]
            title = header.select('td')[1]
            post_link = title.select('a')[-1].attrs['href']
            topic_id = post_link.split('topic=')[-1].split('.')[0]
            message_id = post_link.split('topic=')[-1].split('#')[-1]
            message_id = message_id.replace('msg', '')
            date = header.select('td')[2].text.strip().replace('on: ', '')
            if 'Today ' in date:
                date = date.strip().replace('Today at ', '')
                timestamp = datetime.combine(
                    check_datetime.date(),
                    parser.parse(date).time()
                )
            else:
                timestamp = parser.parse(date)
            if timestamp >= start:
                # if message_id in tracked_posts:
                # Remove all the elements with inside quotes
                for div in post.find_all("div", {'class': 'quoteheader'}):
                    div.decompose()
                for div in post.find_all("div", {'class': 'quote'}):
                    div.decompose()
                # Get the cleaned up text
                clean_content = post.text.strip()
                details = {
                    'topic_id': topic_id,
                    'message_id': message_id,
                    'timestamp': timestamp,
                    'content_length': len(clean_content),
                    'check_datetime': check_datetime
                }
                post_details.append(details)
            else:
                start_reached = True
        return (post_details, start_reached)

    def scrape_posts(self, user_id, **kwargs):
        url = self.base_url + '/index.php?action=profile;u=%s;' % user_id
        url += 'sa=showPosts;start=0'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, 'html.parser')
        pages = soup.select('.navPages')
        pages = [x.attrs['href'] for x in pages]
        posts, start_reached = self._scrape_posts_page(soup, **kwargs)
        if not start_reached:
            for page in pages:
                resp = requests.get(page)
                soup = BeautifulSoup(resp.content, 'html.parser')
                posts, start_reached = self._scrape_posts_page(
                    soup,
                    **kwargs
                )
                if start_reached:
                    break
        return posts


def verify_and_scrape(forum_profile_id,
                      forum_user_id,
                      expected_links,
                      vcode=None,
                      test_mode=False,
                      test_signature=None,
                      fallback=None,
                      test_config=None):
    scraper = BitcoinTalk(test=test_mode, test_signature=test_signature)
    scraper.set_params(forum_profile_id, forum_user_id, expected_links)
    scraper.get_profile(
        forum_user_id,
        fallback=fallback,
        test_config=test_config
    )
    try:
        username = scraper.get_username()
        position = scraper.get_user_position()
        page_ok, verified = scraper.check_signature(vcode=vcode)
    except ScraperError:
        log_opts = {
            'level': 'error',
            'meta': {
                'forum_profile_id': str(forum_profile_id),
                'forum_user_id': forum_user_id,
                'response_status_code': scraper.status_code
            }
        }
        message = 'Error in scraping forum profile page'
        logger.info(message, log_opts)
        raise ScraperError(message)
    posts = scraper.get_total_posts()
    data = (
        scraper.status_code,
        page_ok,
        verified,
        posts,
        username,
        position,
        fallback
    )
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


def scrape_posts(forum_user_id, **kwargs):
    scraper = BitcoinTalk()
    posts = scraper.scrape_posts(forum_user_id, **kwargs)
    return posts
