import pytest
from unittest.mock import patch
from venue.tasks import scrape_forum_profile
from venue.models import ForumProfile, ForumSite


class TestRollbarLogging:

    @pytest.mark.django_db(transaction=True)
    @patch('venue.tasks.rollbar')
    def test_logging_on_scraper_error(self, mock_rollbar, celery_app, celery_worker):
        forum_profile = ForumProfile.objects.all()[0]
        forum_profile.dummy = False
        forum_profile.save()
        job = scrape_forum_profile.delay(
            str(forum_profile.id),
        )
        job.get(timeout=10)
        print(job.result)
        mock_rollbar.report_exc_info.assert_called()
