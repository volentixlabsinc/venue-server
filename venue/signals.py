from django.db.models.signals import post_save
from django.dispatch import receiver
# from .models import PostUptimeStats
from .tasks import compute_ranking


# @receiver(post_save, sender=PostUptimeStats, dispatch_uid='trigger_ranking')
# def trigger_ranking(sender, instance, **kwargs):
#    compute_ranking.delay()
