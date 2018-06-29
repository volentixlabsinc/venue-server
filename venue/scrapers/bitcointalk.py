import time
import requests
from hashids import Hashids
from bs4 import BeautifulSoup
from django.conf import settings
from selenium import webdriver
from django.utils import timezone
from datetime import datetime
from dateutil import parser
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

    def check_signature(self, vcode=None):
        sig = self.soup.select('div#bodyarea tr')[26]
        # Find links and check their integrity
        links = sig.find_all('a')
        if links:
            links = [x.attrs['href'] for x in links]
        else:
            links = sig.text.strip().splitlines()
        links_verified, scraped_vcode = self.verify_links(
            links,
            self.expected_links,
            scraped_signature=sig.text
        )
        if vcode and scraped_vcode:
            if vcode == scraped_vcode:
                code_verified = True
        else:
            code_verified = False
        sig_found = False
        if links_verified and code_verified:
            sig_found = True
        return sig_found

    def _scrape_posts_page(self, soup, last_scrape=None):
        post_details = []
        posts = soup.select('.post')
        check_datetime = timezone.now()
        last_scrape_reached = False
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
            if timestamp >= last_scrape:
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
                last_scrape_reached = True
        return (post_details, last_scrape_reached)

    def scrape_posts(self, user_id, **kwargs):
        url = self.base_url + '/index.php?action=profile;u=%s;' % user_id
        url += 'sa=showPosts;start=0'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, 'html.parser')
        pages = soup.select('.navPages')
        pages = [x.attrs['href'] for x in pages]
        posts, last_scrape_reached = self._scrape_posts_page(soup, **kwargs)
        if not last_scrape_reached:
            for page in pages:
                resp = requests.get(page)
                soup = BeautifulSoup(resp.content, 'html.parser')
                posts, last_scrape_reached = self._scrape_posts_page(
                    soup,
                    **kwargs
                )
                if last_scrape_reached:
                    break
        return posts


def verify_and_scrape(forum_profile_id,
                      forum_user_id,
                      expected_links,
                      vcode=None,
                      test_mode=False,
                      test_signature=None):
    scraper = BitcoinTalk(test=test_mode, test_signature=test_signature)
    scraper.set_params(forum_profile_id, forum_user_id, expected_links)
    scraper.get_profile(forum_user_id)
    username = scraper.get_username()
    position = scraper.get_user_position()
    verified = scraper.check_signature(vcode=vcode)
    posts = scraper.get_total_posts()
    data = (scraper.status_code, verified, posts, username, position)
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
