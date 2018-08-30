import pytest
from unittest.mock import patch, PropertyMock
from venue.tasks import scrape_forum_profile
from venue.models import ForumProfile


class TestRollbarLogging:

    @pytest.mark.django_db
    @patch('venue.tasks.rollbar')
    @patch('venue.scrapers.bitcointalk.requests')
    def test_logging_on_scraper_error(self, mock_request, mock_rollbar):
        mock_request.get.return_value = PropertyMock(
            text='',
            content='',
            status_code=200
        )
        forum_profile = ForumProfile.objects.all()[0]
        url = "https://bitcointalk.org/index.php?action=login"
        config = {
            'profile_url': url
        }
        result = scrape_forum_profile.run(
            str(forum_profile.id),
            test_scrape_config=config,
            retries=5
        )
        assert result == 'gave up'
        mock_rollbar.report_exc_info.assert_called()
