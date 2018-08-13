from __future__ import absolute_import, unicode_literals

import re
from datetime import timedelta
from operator import itemgetter

import rollbar
from celery import shared_task
from celery.result import AsyncResult, ResultSet
from celery.signals import task_failure
from constance import config
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from postmarker.core import PostmarkClient
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

from venue.models import (ForumPost, ForumProfile, ForumSite, ForumUserRank, Ranking, Signature, UserProfile)
from venue.utils import translation_on


@task_failure.connect
def handle_task_failure(**kw):
    rollbar.report_exc_info(extra_data=kw)


@shared_task(queue='scrapers')
def multiplier(x, y):
    return x * y


@shared_task(queue='scrapers')
def test_task():
    import time
    import random
    time.sleep(2)
    return random.randint(0, 100)


def load_scraper(name):
    name = name.strip('.py')
    scraper = __import__('venue.scrapers.' + name, fromlist=[name])
    return scraper


def get_expected_links(code):
    terms = re.split('[\[\]]', code)
    links = []
    for term in terms:
        if 'url=' in term:
            link = term.split('url=')[1]
            if link:
                links.append(link)
    return set(links)


@shared_task(queue='scrapers')
def scrape_forum_profile(forum_profile_id, test_mode=None):
    forum_profile = ForumProfile.objects.get(id=forum_profile_id)
    if test_mode is None:
        test_mode = config.TEST_MODE
    if forum_profile.dummy:
        pass
    else:
        scraper = load_scraper(forum_profile.forum.scraper_name)
        expected_links = get_expected_links(forum_profile.signature.code)
        results = scraper.verify_and_scrape(
            forum_profile.id,
            forum_profile.forum_user_id,
            expected_links,
            vcode=forum_profile.verification_code,
            test_mode=test_mode,
            test_signature=forum_profile.signature.test_signature)
        status_code, page_ok, signature_found, total_posts, username, position = results
        del username
        # Update forum profile page status
        status_list = forum_profile.last_page_status
        if len(status_list):
            old_status = status_list[-1]
            new_status_list = [old_status]
        else:
            new_status_list = []
        new_status = {
            'status_code': status_code,
            'page_ok': page_ok,
            'signature_found': signature_found
        }
        new_status_list.append(new_status)
        forum_profile.last_page_status = new_status_list
        forum_profile.save()
        # Update the forum user rank, if it changed
        forum_rank = ForumUserRank.objects.get(name=position)
        if forum_profile.forum_rank != forum_rank:
            forum_profile.forum_rank = forum_rank
            forum_profile.save()
        # Get the current last scrape timestamp
        last_scrape = forum_profile.get_last_scrape()
        # Check posts that haven't reached maturatation
        tracked_posts = []
        for post in forum_profile.posts.filter(matured=False):
            # Check if it's not due to mature yet
            post_timestamp = post.timestamp.replace(tzinfo=None)
            tdiff = timezone.now().replace(tzinfo=None) - post_timestamp
            tdiff_hours = tdiff.total_seconds() / 3600
            if tdiff_hours > config.MATURATION_PERIOD:
                post.matured = True
                post.date_matured = timezone.now()
                post.save()
            else:
                tracked_posts.append(post.message_id)
        # Get the latest posts from this forum profile
        # Latest means posts in the last 24 hours
        posts_scrape_start = last_scrape - timedelta(hours=24)
        posts = scraper.scrape_posts(
            forum_profile.forum_user_id,
            start=posts_scrape_start.replace(tzinfo=None)
        )
        # Save each new post
        message_ids = []
        for post in posts:
            message_ids.append(post['message_id'])
            post_check = ForumPost.objects.filter(
                forum_profile=forum_profile,
                topic_id=post['topic_id'],
                message_id=post['message_id'],
            )
            if not post_check.exists():
                forum_post = ForumPost(
                    user_profile=forum_profile.user_profile,
                    forum_profile=forum_profile,
                    forum_rank=forum_profile.forum_rank,
                    topic_id=post['topic_id'],
                    message_id=post['message_id'],
                    unique_content_length=post['content_length'],
                    timestamp=post['timestamp']
                )
                forum_post.save()
        # Check for post deletion
        deleted_posts = ForumPost.objects.filter(
            forum_profile=forum_profile,
            matured=False,
            timestamp__gte=posts_scrape_start
        ).exclude(
            message_id__in=message_ids
        )
        for post in deleted_posts:
            post.credited = False
            post.monitoring = False
            post.save()
        # Update tracked posts
        for post in tracked_posts:
            forum_post = ForumPost.objects.get(
                message_id=post,
                forum_profile=forum_profile
            )
            forum_post.save()
        # Update the forum_profile's last scrape timestamp
        forum_profile.last_scrape = timezone.now()
        forum_profile.save()


@shared_task(queue='scrapers')
def verify_profile_signature(forum_site_id, forum_profile_id, signature_id):
    forum_profile = ForumProfile.objects.get(id=forum_profile_id)
    signature = Signature.objects.get(id=signature_id)
    expected_links = get_expected_links(signature.code)
    forum = ForumSite.objects.get(id=forum_site_id)
    scraper = load_scraper(forum.scraper_name)
    results = scraper.verify_and_scrape(
        forum_profile_id,
        forum_profile.forum_user_id,
        expected_links,
        test_mode=config.TEST_MODE,
        test_signature=signature.test_signature)
    status_code, page_ok, verified, posts, username, position = results
    del status_code, posts, position
    if verified:
        # Save the forum username
        forum_profile.forum_username = username
        forum_profile.save()
    return verified


@shared_task(queue='scrapers')
def get_user_position(forum_site_id, profile_url, user_id):
    forum = ForumSite.objects.get(id=forum_site_id)
    scraper = load_scraper(forum.scraper_name)
    forum_user_id = scraper.extract_user_id(profile_url)
    try:
        status_code, position, username = scraper.get_user_position(forum_user_id)
        result = {
            'status_code': status_code,
            'found': True,
            'position': position,
            'forum_user_id': forum_user_id,
            'forum_user_name': username
        }
        fp_check = ForumProfile.objects.filter(
            forum=forum,
            forum_user_id=forum_user_id
        )
        result['active'] = False
        result['with_signature'] = False
        result['exists'] = fp_check.exists()
        if fp_check.exists():
            fp = fp_check.latest()
            result['forum_profile_id'] = fp.id
            result['own'] = False
            if fp.user_profile.user.id == user_id:
                result['own'] = True
                if fp.posts.count():
                    result['active'] = True
            result['verified'] = fp.verified
            if fp.signature and fp.verified:
                result['with_signature'] = True
    except scraper.ProfileDoesNotExist:
        result = {'found': False}
    return result


def send_websocket_signal(signal):
    # Send a test message over websocket
    redis_publisher = RedisPublisher(facility='signals', broadcast=True)
    message = RedisMessage(signal)
    redis_publisher.publish_message(message)


@shared_task(queue='compute')
def compute_ranking():
    users = UserProfile.objects.filter(
        user__is_active=True
    )
    user_points = []
    for user in users:
        if user.with_forum_profile:
            total_points = user.total_points
            info = {
                'user_profile_id': str(user.id),
                'total_points': total_points
            }
            user_points.append(info)
    if user_points:
        # Sort the points based on the total
        user_points = sorted(
            user_points,
            key=itemgetter('total_points'),
            reverse=True
        )
    # Ranking batch
    global_total = 0
    try:
        last_ranking = Ranking.objects.all().latest()
        batch_number = last_ranking.batch + 1
    except Ranking.DoesNotExist:
        batch_number = 1
    for rank, user in enumerate(user_points, 1):
        # Update user's ranking
        user_points[rank - 1]['rank'] = rank
        ranking = Ranking(
            batch=batch_number,
            user_profile_id=user['user_profile_id'],
            rank=rank
        )
        ranking.save()
    # Compute the global total points
    global_total = sum([x['total_points'] for x in user_points])
    # Send ws signals to all connected clients if global total has changed
    old_total = settings.REDIS_DB.get('global_total_points')
    if old_total:
        if float(old_total) != global_total:
            send_websocket_signal('refresh')
    # Save the global total points in redis
    settings.REDIS_DB.set('global_total_points', global_total)
    return {'total': global_total, 'points': user_points}


@shared_task(queue='compute', bind=True, max_retries=600)
def compute_points(self, subtasks=None):
    proceed = False
    if subtasks:
        jobs = [AsyncResult(x) for x in subtasks]
        results = ResultSet(jobs)
        if results.ready():
            proceed = True
    else:
        proceed = True
    # Proceed to compute the points
    if proceed:
        posts = ForumPost.objects.filter(
            forum_profile__user_profile__user__is_active=True,
            forum_profile__active=True,
            monitoring=True
        )
        for post in posts:
            pct_threshold = config.UPTIME_PERCENTAGE_THRESHOLD
            downtime_threshold_pct = (100 - pct_threshold)
            maturation = config.MATURATION_PERIOD
            downtime_pct = (post.invalid_sig_minutes / (maturation * 60))
            downtime_pct *= 100
            if downtime_pct >= downtime_threshold_pct:
                post.credited = False
                post.monitoring = False
                post.save()
        # Call the task to compute the ranking
        compute_ranking.delay()
    else:
        self.retry(countdown=5)


@shared_task(queue='scrapers')
def update_data(forum_profile_id=None):
    # Create a bakcground tasks workflow as a chain
    if forum_profile_id:
        forum_profiles = ForumProfile.objects.filter(id__in=[forum_profile_id])
    else:
        forum_profiles = ForumProfile.objects.filter(
            user_profile__user__is_active=True,
            active=True,
            verified=True
        )
    # Send scraping tasks to the queue
    subtasks = []
    for profile in forum_profiles:
        job = scrape_forum_profile.delay(profile.id)
        subtasks.append(job.id)
    compute_points.delay(subtasks)
    return subtasks


@shared_task(queue='control')
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
        rate_per_min = num_users / (settings.USER_SCRAPE_INTERVAL / 60)
        rate_per_min = int(round(rate_per_min, 2))
        if rate_per_min > 1:
            rate = '%s/m' % rate_per_min
    cmd = 'celery -A volentix control rate_limit'
    cmd += ' venue.tasks.scrape_forum_profile %s' % rate
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return (rate, stdout.decode())


# -----------------------------------
# Tasks for sending automated emails
# -----------------------------------


postmark = PostmarkClient(
    server_token=settings.POSTMARK_TOKEN,
    account_token=settings.POSTMARK_TOKEN)


@shared_task(queue='mails')
def send_email_confirmation(email, name, code, language):
    return send_email(
        template='venue/email_confirmation.html',
        email=email, name=name, code=code,
        language=language, subject='Email Confirmation',
    )


@shared_task(queue='mails')
def send_deletion_confirmation(email, name, code, language):
    return send_email(
        template='venue/deletion_confirmation.html',
        email=email, name=name, code=code,
        language=language, subject='Account Deletion Confirmation',
    )


@shared_task(queue='mails')
def send_email_change_confirmation(email, name, code, language):
    return send_email(
        template='venue/email_change.html',
        email=email, name=name, code=code,
        language=language, subject='Email Change Confirmation',
    )


@shared_task(queue='mails')
def send_reset_password(email, name, code, language):
    return send_email(
        template='venue/reset_password.html',
        email=email, name=name, code=code,
        language=language, subject='Account Password Reset',
    )


def send_email(*, template, email, subject, language, **kwargs):
    """
    Generic function to send email
    :param template: path to template to be used
    :param email: email to send
    :param subject: email subject
    :param language: language code (en, fr, etc..)
    :return:
    """
    kwargs['domain'] = settings.VENUE_FRONTEND,
    with translation_on(language):
        html = get_template(template).render(kwargs)
        mail = postmark.emails.send(
            From=settings.POSTMARK_SENDER_EMAIL,
            To=email,
            Subject=subject,
            ReplyTo=settings.POSTMARK_REPLY_EMAIL,
            HtmlBody=html)
        return mail
