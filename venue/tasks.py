from __future__ import absolute_import, unicode_literals
from .models import UserProfile, UptimeBatch, GlobalStats, PointsCalculation
from celery import shared_task

@shared_task
def add(x, y):
    return x + y
    
@shared_task
def update_global_stats():
    users = UserProfile.objects.all()
    total_posts = 0
    total_posts_with_sig = 0
    total_days = 0
    for user in users:
        total_posts += user.get_total_posts()
        total_posts_with_sig += user.get_total_posts_with_sig()
        total_days += user.get_total_days()
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
        for check in batch.regular_checks.all():
            calc = PointsCalculation(
                uptime_batch=batch,
                signature_check=check
            )
            calc.save()