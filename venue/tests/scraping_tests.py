import pytest
from unittest.mock import patch, PropertyMock
from venue.tasks import scrape_forum_profile, get_user_position
from venue.models import ForumProfile, ForumSite, User
from venue.scrapers.bitcointalk import BitcoinTalk
from venue.scrapers.exceptions import ScraperError
from django.conf import settings


class TestForumProfileScraping:

    @pytest.mark.django_db
    @patch('venue.scrapers.bitcointalk.requests')
    def test_profile_checking(self, mock_request, scraper_headers):
        mock_request.get.return_value = PropertyMock(
            text='',
            content=''
        )
        # Get forum site and user objects from pre-loaded dummy data
        forum_site = ForumSite.objects.get(name='bitcointalk.org')
        user = User.objects.get(username='wolverine')
        get_user_position.run(
            str(forum_site.id),
            '0000',
            str(user.id),
            retries=1
        )
        url = 'https://bitcointalk.org/index.php?action=profile;u=0000'
        mock_request.get.assert_called_once_with(
            url,
            headers=scraper_headers,
            proxies=settings.CRAWLERA_PROXIES,
            verify=False
        )

    @pytest.mark.django_db
    @patch('venue.scrapers.bitcointalk.requests')
    def test_fallback_trigger(self, mock_request, scraper_headers):
        # setup test data
        forum_profile = ForumProfile.objects.all()[0]
        forum_profile.dummy = False
        forum_profile.save()
        # Give an obviously wrong profile URL to trigger
        # the fallback scraping using crawlera
        url = "https://bitcointalk.org/index.php?action=login"
        config = {
            'profile_url': url
        }

        # check 1st retry for the scraper
        mock_request.get.return_value = PropertyMock(
            text='',
            content='',
            status=200
        )
        scrape_forum_profile.run(
            str(forum_profile.id),
            test_scrape_config=config,
            retries=0
        )
        mock_request.get.assert_called_once_with(
            url,
            headers=scraper_headers,
            proxies=None,
            verify=False
        )

        # check 4th retry for the scraper
        mock_request.get.reset_mock()
        scrape_forum_profile.run(
            str(forum_profile.id),
            test_scrape_config=config,
            retries=1
        )
        mock_request.get.assert_called_once_with(
            url,
            headers=scraper_headers,
            proxies=settings.CRAWLERA_PROXIES,
            verify=False
        )

    def test_catching_connection_error(self):
        scraper = BitcoinTalk()
        with pytest.raises(ScraperError):
            scraper.get_profile(
                'xxx',
                test_config={
                    'profile_url': 'http://www.non-existent-domain.xxx'
                }
            )
