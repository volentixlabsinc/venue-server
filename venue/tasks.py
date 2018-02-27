from __future__ import absolute_import, unicode_literals
import traceback
from operator import itemgetter
from django.template.loader import get_template
from django.utils import timezone
from django.conf import settings
from celery import shared_task, chain, group
from postmarker.core import PostmarkClient
from datetime import timedelta
from constance import config
import pandas as pd
from .models import (UserProfile, UptimeBatch, GlobalStats, SignatureCheck, 
                     PointsCalculation, DataUpdateTask, ScrapingError, ForumSite,
                     ForumProfile, Signature, Ranking)


def load_scraper(name):
    name = name.strip('.py')
    scraper = __import__('venue.scrapers.' + name, fromlist=[name])
    return scraper
    
@shared_task
def scrape_forum_profile(forum_profile_id, master_task_id):
    forum_profile = ForumProfile.objects.get(id=forum_profile_id)
    try:
        scraper = load_scraper(forum_profile.forum.scraper_name)
        status_code, signature_found, total_posts, username = scraper.verify_and_scrape(
            forum_profile.id,
            forum_profile.forum_user_id,
            forum_profile.signature.expected_links.splitlines(),
            test_mode=config.TEST_MODE)
        if status_code == 200:
            sigcheck = SignatureCheck(
                forum_profile=forum_profile,
                total_posts=total_posts,
                signature_found=signature_found,
                status_code=status_code
            )
            sigcheck.save()
    except Exception as exc:
        if master_task_id:
            data_update = DataUpdateTask.objects.get(task_id=master_task_id)
            scrape_error = ScrapingError(
                error_type=type(exc).__name__,
                forum=forum_profile.forum, 
                forum_profile=forum_profile,
                traceback=traceback.format_exc()
            )
            scrape_error.save()
            data_update.scraping_errors.add(scrape_error)
        raise exc


@shared_task
def verify_profile_signature(forum_site_id, forum_profile_id, signature_id):
    forum_profile = ForumProfile.objects.get(id=forum_profile_id)
    signature = Signature.objects.get(id=signature_id)
    expected_links = signature.expected_links.splitlines()
    forum = ForumSite.objects.get(id=forum_site_id)
    scraper = load_scraper(forum.scraper_name)
    status_code, verified, posts, username = scraper.verify_and_scrape(
        forum_profile_id, 
        forum_profile.forum_user_id, 
        expected_links,
        test_mode=config.TEST_MODE)
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
    status_code, position = scraper.get_user_position(forum_user_id)
    result = {
        'status_code': status_code,
        'position': position,
        'forum_user_id': forum_user_id
    }
    fp_check = ForumProfile.objects.filter(forum=forum, forum_user_id=forum_user_id)
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
    
@shared_task
def update_global_stats():
    users = UserProfile.objects.all()
    total_posts = 0
    total_posts_with_sig = 0
    total_days = 0
    for user in users:
        fps = user.forum_profiles.all()
        for fp in fps:
            if fp.uptime_batches.count():
                #latest_batch = fp.uptime_batches.last()
                #total_posts += latest_batch.get_total_posts()
                for batch in fp.uptime_batches.all():
                    total_posts += batch.get_total_posts()
                    total_posts_with_sig += batch.get_total_posts_with_sig()
                    total_days += batch.get_total_days()
    gstats = GlobalStats(
        total_posts=total_posts,
        total_posts_with_sig=total_posts_with_sig,
        total_days=total_days
    )
    gstats.save()

@shared_task
def calculate_points():
    batches = UptimeBatch.objects.all()
    for batch in batches:
        latest_check = batch.regular_checks.last()
        calc = PointsCalculation(
            uptime_batch=batch,
            signature_check=latest_check
        )
        calc.save()

@shared_task
def calculate_rankings():
    """ Calculates the rankings and saves to DB """
    users = UserProfile.objects.filter(email_confirmed=True)
    users_points = []
    # Generate the rankings
    for user in users:
        user_data = {
            'user_profile_id': user.id,
            'points': user.get_total_points()
        }
        users_points.append(user_data)
    users_points.sort(key=itemgetter('points'), reverse=True)
    # Save the rankings
    for rank, user in enumerate(users_points, 1):
        ranking = Ranking(
            user_profile_id=user['user_profile_id'],
            rank=rank)
        ranking.save()


@shared_task
def database_cleanup():
    uptime_batches = UptimeBatch.objects.all()
    dt = timezone.now().date()
    # Delete the regular signature checks, retain only the last one per day,
    # the last check, the last initial check, and the very first check per batch
    for batch in uptime_batches:
        checks = batch.regular_checks.all()
        if checks.count() > 1:
            earliest_check = checks.first()
            latest_check = checks.last()
            latest_initial = checks.filter(initial=True).last()
            latest_found = checks.filter(signature_found=True).last()
            df = pd.DataFrame(list(checks.values('id', 'date_checked')))
            dfs = df.groupby([df['date_checked'].dt.date]).agg('max')
            excluded = list(dfs['id']) + [earliest_check.id, latest_check.id, latest_initial.id, latest_found.id]
            # Retain also anything with new posts
            with_new_posts = checks.filter(new_posts__gt=0)
            excluded += list(with_new_posts.values_list('id', flat=True))
            checks.exclude(id__in=excluded).delete()
    # Retain only the latest row per day in global stats
    stats = GlobalStats.objects.all()
    df = pd.DataFrame(list(stats.values('id', 'date_updated')))
    dfs = df.groupby([df['date_updated'].dt.date]).agg('max')
    stats.exclude(id__in=list(dfs['id'])).delete()
    # Remove the data upload task records older than 24 hours
    threshold_time = timezone.now() - timedelta(hours=24)
    updates = DataUpdateTask.objects.filter(date_completed__lt=threshold_time)
    updates.delete()
    # Retain only the latest ranking per day per user
    rankings = Ranking.objects.all()
    df = pd.DataFrame(list(rankings.values('id', 'user_profile_id', 'ranking_date')))
    agg_funcs = {'ranking_date': 'max', 'id': 'max'}
    dfs = df.groupby(['user_profile_id', df['ranking_date'].dt.date], as_index=False).agg(agg_funcs)
    rankings.exclude(id__in=list(dfs['id'])).delete()
    
@shared_task
def mark_master_task_complete(master_task_id):
    master_task = DataUpdateTask.objects.get(task_id=master_task_id)
    master_task.date_completed = timezone.now()
    if master_task.scraping_errors.count():
        master_task.success = False
    else:
        master_task.success = True
    master_task.save()

@shared_task
def update_data(forum_profile_id=None):
    # Save this data update task
    task_id = update_data.request.id
    data_update = DataUpdateTask(task_id=task_id)
    data_update.save()
    # Create a bakcground tasks workflow as a chain
    if forum_profile_id:
        forum_profiles = ForumProfile.objects.filter(id__in=[forum_profile_id])
    else:
        forum_profiles = ForumProfile.objects.filter(active=True, verified=True)
    scraping_tasks = group(scrape_forum_profile.s(fp.id, task_id) for fp in forum_profiles)
    workflow = chain(
        scraping_tasks, # Execute scraping tasks
        update_global_stats.si(), # Execute task to update global stats
        calculate_points.si(), # Execute task to calculate points
        mark_master_task_complete.si(task_id), # Mark the data update run as complete
        calculate_rankings.si(),
        database_cleanup.si() # Trigger the database cleanup task
    )
    # Send to the workflow to the queue
    workflow.apply_async()

#-----------------------------------
# Tasks for sending automated emails
#-----------------------------------

postmark = PostmarkClient(
    server_token=settings.POSTMARK_TOKEN,
    account_token=settings.POSTMARK_TOKEN)
      
@shared_task
def send_email_confirmation(email, name, code):
    context = {'name': name, 'code': code}
    html = get_template('venue/email_confirmation.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Email Confirmation',
        HtmlBody=html)
    return mail
    
@shared_task
def send_deletion_confirmation(email, name, code):
    context = {'name': name, 'code': code}
    html = get_template('venue/deletion_confirmation.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Account Deletion Confirmation',
        HtmlBody=html)
    return mail
    
@shared_task
def send_email_change_confirmation(email, name, code):
    context = {'name': name, 'code': code}
    html = get_template('venue/email_change.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Email Change Confirmation',
        HtmlBody=html)
    return mail
    
@shared_task
def send_reset_password(email, name, code):
    context = {'name': name, 'code': code}
    html = get_template('venue/reset_password.html').render(context)
    mail = postmark.emails.send(
        From=settings.POSTMARK_SENDER_EMAIL,
        To=email,
        Subject='Account Password Reset',
        HtmlBody=html)
    return mail