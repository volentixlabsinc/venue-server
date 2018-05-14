from __future__ import absolute_import, unicode_literals
from django.template.loader import get_template
from django.conf import settings
from celery import shared_task
from celery.signals import task_failure
from postmarker.core import PostmarkClient
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage
from operator import itemgetter
from constance import config
import rollbar
from venue.models import (ForumSite, Signature, UserProfile, ForumProfile,
                          UserPostStats, Ranking)


@task_failure.connect
def handle_task_failure(**kw):
    rollbar.report_exc_info(extra_data=kw)


@shared_task
def multiplier(x, y):
    return x * y


@shared_task
def test_task():
    import time
    import random
    time.sleep(2)
    return random.randint(0, 100)


def load_scraper(name):
    name = name.strip('.py')
    scraper = __import__('venue.scrapers.' + name, fromlist=[name])
    return scraper


@shared_task
def scrape_forum_profile(forum_profile_id, test_mode=None):
    forum_profile = ForumProfile.objects.get(id=forum_profile_id)
    test_mode = test_mode
    if test_mode is None:
        test_mode = config.TEST_MODE
    scraper = load_scraper(forum_profile.forum.scraper_name)
    results = scraper.verify_and_scrape(
        forum_profile.id,
        forum_profile.forum_user_id,
        forum_profile.signature.expected_links.splitlines(),
        test_mode=test_mode,
        test_signature=forum_profile.signature.test_signature)
    status_code, signature_found, total_posts, username = results
    del username
    # Record initial post count
    if forum_profile.post_stats.count() == 0:
        forum_profile.initial_posts_count = total_posts
    # Record the post stats
    post_stats = UserPostStats(
        user_profile=forum_profile.user_profile,
        forum_profile=forum_profile,
        num_posts=total_posts,
        is_signature_valid=signature_found
    )
    post_stats.save()


@shared_task
def verify_profile_signature(forum_site_id, forum_profile_id, signature_id):
    forum_profile = ForumProfile.objects.get(id=forum_profile_id)
    signature = Signature.objects.get(id=signature_id)
    expected_links = signature.expected_links.splitlines()
    forum = ForumSite.objects.get(id=forum_site_id)
    scraper = load_scraper(forum.scraper_name)
    results = scraper.verify_and_scrape(
        forum_profile_id,
        forum_profile.forum_user_id,
        expected_links,
        test_mode=config.TEST_MODE,
        test_signature=signature.test_signature)
    status_code, verified, posts, username = results
    del status_code, posts
    if verified:
        # Save the forum username
        forum_profile.forum_username = username
        forum_profile.save()
    return verified


@shared_task
def get_user_position(forum_site_id, profile_url, user_id):
    forum = ForumSite.objects.get(id=forum_site_id)
    scraper = load_scraper(forum.scraper_name)
    forum_user_id = scraper.extract_user_id(profile_url)
    status_code, position, username = scraper.get_user_position(forum_user_id)
    result = {
        'status_code': status_code,
        'position': position,
        'forum_user_id': forum_user_id,
        'forum_user_name': username
    }
    fp_check = ForumProfile.objects.filter(
        forum=forum,
        forum_user_id=forum_user_id
    )
    result['exists'] = fp_check.exists()
    if fp_check.exists():
        fp = fp_check.last()
        result['forum_profile_id'] = fp.id
        result['own'] = False
        if fp.user_profile.user.id == user_id:
            result['own'] = True
            if fp.uptime_batches.filter(active=True).count():
                result['active'] = True
            else:
                result['active'] = False
        result['verified'] = fp.verified
        result['with_signature'] = False
        if fp.signature:
            result['with_signature'] = True
    return result


def send_websocket_signal(signal):
    # Send a test message over websocket
    # TODO -- This is not called at the moment,
    # This needs to be called somehow at a later time
    # to inform the frontend that new data is available
    redis_publisher = RedisPublisher(facility='signals', broadcast=True)
    message = RedisMessage(signal)
    redis_publisher.publish_message(message)


@shared_task
def update_data(forum_profile_id=None):
    # Create a bakcground tasks workflow as a chain
    if forum_profile_id:
        forum_profiles = ForumProfile.objects.filter(id__in=[forum_profile_id])
    else:
        forum_profiles = ForumProfile.objects.filter(
            active=True,
            verified=True
        )
    # Send scraping tasks to the queue
    for profile in forum_profiles:
        scrape_forum_profile.delay(profile.id)


@shared_task
def compute_ranking():
    users = UserProfile.objects.all()
    user_points = []
    for user in users:
        total_points = user.post_points + user.uptime_points
        info = {
            'user_profile_id': int(user.id),
            'total_points': total_points
        }
        user_points.append(info)
    # Sort the points based on the total
    user_points = sorted(
        user_points,
        key=itemgetter('total_points'),
        reverse=True
    )
    for rank, user in enumerate(user_points, 1):
        # Update user's ranking
        ranking = Ranking(
            user_profile_id=user['user_profile_id'],
            rank=rank
        )
        ranking.save()
    # Save the global total points in redis
    global_total = sum([x['total_points'] for x in user_points])
    settings.REDIS_DB.set('global_total_points', global_total)
    return {'total': global_total}


@shared_task
def set_scraping_rate(num_users=None):
    from subprocess import Popen, PIPE
    if not num_users:
        forum_profiles = ForumProfile.objects.filter(active=True)
        num_users = forum_profiles.count()
    rate = '1/s'
    rate_per_sec = num_users / settings.USER_SCRAPE_INTERVAL
    rate_per_sec = int(round(rate_per_sec, 2))
    if rate_per_sec > 1:
        rate = '%s/s' % rate_per_sec
    else:
        rate_per_min = num_users / (settings.USER_SCRAPE_INTERVAL/60)
        rate_per_min = int(round(rate_per_min, 2))
        if rate_per_min > 1:
            rate = '%s/m' % rate_per_min
    cmd = 'celery -A volentix control rate_limit'
    cmd += ' venue.tasks.scrape_forum_profile %s' % rate
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return (rate, stdout)


# -----------------------------------
# Tasks for sending automated emails
# -----------------------------------


postmark = PostmarkClient(
    server_token=settings.POSTMARK_TOKEN,
    account_token=settings.POSTMARK_TOKEN)


@shared_task
def send_email_confirmation(email, name, code):
    context = {
        'domain': settings.VENUE_DOMAIN,
        'name': name,
        'code': code
    }
    html = get_template('venue/email_confirmation.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Email Confirmation',
        ReplyTo='noreply@volentixlabs.com',
        HtmlBody=html)
    return mail


@shared_task
def send_deletion_confirmation(email, name, code):
    context = {
        'domain': settings.VENUE_DOMAIN,
        'name': name,
        'code': code
    }
    html = get_template('venue/deletion_confirmation.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Account Deletion Confirmation',
        ReplyTo='noreply@volentixlabs.com',
        HtmlBody=html)
    return mail


@shared_task
def send_email_change_confirmation(email, name, code):
    context = {
        'domain': settings.VENUE_DOMAIN,
        'name': name,
        'code': code
    }
    html = get_template('venue/email_change.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Email Change Confirmation',
        ReplyTo='noreply@volentixlabs.com',
        HtmlBody=html)
    return mail


@shared_task
def send_reset_password(email, name, code):
    context = {
        'domain': settings.VENUE_DOMAIN,
        'name': name,
        'code': code
    }
    html = get_template('venue/reset_password.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Account Password Reset',
        ReplyTo='noreply@volentixlabs.com',
        HtmlBody=html)
    return mail
