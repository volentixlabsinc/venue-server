import pytest
from venue.tasks import scrape_forum_profile, get_user_position
from venue.models import ForumProfile, ForumSite, User
from venue.scrapers.bitcointalk import BitcoinTalk
from venue.scrapers.exceptions import ScraperError
from django.core.management import call_command


class TestScrapingRetries:

    @pytest.mark.django_db(transaction=True)
    def test_get_user_position(self, celery_app, celery_worker, capfd):
        call_command('loaddata', 'fixtures/test_data.json')
        forum_site = ForumSite.objects.all()[0]
        user = User.objects.get(username='wolverine')
        job = get_user_position.delay(
            str(forum_site.id),
            '0000',
            str(user.id),
        )
        job.get()
        assert not job.result['found']
        out, err = capfd.readouterr()
        assert 'Retry 3' in out

    @pytest.mark.django_db(transaction=True)
    def test_fallback_trigger(self, celery_app, celery_worker, capfd):
        call_command('loaddata', 'fixtures/test_data.json')
        forum_profile = ForumProfile.objects.all()[0]
        forum_profile.dummy = False
        forum_profile.save()
        job = scrape_forum_profile.delay(
            str(forum_profile.id)
        )
        job.get()
        out, err = capfd.readouterr()
        assert 'Retry 3' in out

    def test_catching_connection_error(self):
        scraper = BitcoinTalk()
        with pytest.raises(ScraperError):
            scraper.get_profile(
                'xxx',
                test_config={
                    'profile_url': 'http://www.non-existent-domain.xxx'
                }
            )
