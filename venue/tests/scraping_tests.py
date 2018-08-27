import pytest
from venue.tasks import multiplier, scrape_forum_profile
from venue.models import ForumProfile
from unittest.mock import patch, PropertyMock
from venue.scrapers.exceptions import ScraperError
from django.conf import settings


class TestBackgroundTaskExecution:

    def test_task_execution(self):
        # Send the task to queue
        task = multiplier.delay(10, 10, ran_from_tests=True)
        # Wait for the task to finish
        task.get()
        # Check results
        assert task.status == 'SUCCESS'
        assert task.result == 100


class TestForumProfileScraping:

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
        mock_request.get.return_value = PropertyMock(text='', content='', status=200)
        with patch('venue.tasks.count_retry') as mock_count_retry:
            mock_count_retry.return_value = 1
            with pytest.raises(ScraperError):
                scrape_forum_profile.run(
                    str(forum_profile.id),
                    test_scrape_config=config
                )
            mock_request.get.assert_called_once_with(
                url,
                headers=scraper_headers,
                proxies=None,
                verify=False
            )

        # check 4th retry for the scraper
        mock_request.get.reset_mock()
        with patch('venue.tasks.count_retry') as mock_count_retry:
            mock_count_retry.return_value = 4
            with pytest.raises(ScraperError):
                scrape_forum_profile.run(
                    str(forum_profile.id),
                    test_scrape_config=config
                )
            mock_request.get.assert_called_once_with(
                url,
                headers=scraper_headers,
                proxies=settings.CRAWLERA_PROXIES,
                verify=False
            )
