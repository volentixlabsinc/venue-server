import pytest
import unittest
from venue.tasks import multiplier, scrape_forum_profile
from venue.models import ForumProfile
from django.conf import settings


class BackgroundTaskExecutionTest(unittest.TestCase):

    def test_task_exection(self):
        # Send the task to queue
        task = multiplier.delay(10, 10, ran_from_tests=True)
        # Wait for the task to finish
        task.get()
        # Check results
        self.assertEqual(task.status, 'SUCCESS')
        self.assertEqual(task.result, 100)


class ForumProfileScrapingTest(unittest.TestCase):

    @pytest.mark.django_db
    def test_fallback_trigger(self):
        forum_profile = ForumProfile.objects.all()[0]
        forum_profile.dummy = False
        forum_profile.save()
        # Give an obviously wrong profile URL to trigger
        # the fallback scraping using crawlera
        config = {
            'profile_url': 'https://bitcointalk.org/index.php?action=login'
        }
        task = scrape_forum_profile.delay(
            str(forum_profile.id),
            test_scrape_config=config
        )
        self.assertEqual(task.ready(), False)
        # Wait for the result
        task.get()
        self.assertEqual(task.result, 'pass')
