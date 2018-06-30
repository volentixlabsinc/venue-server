from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.exceptions import ObjectDoesNotExist


def post_migrate_callback(sender, **kwargs):
    from venue.tasks import compute_ranking
    try:
        compute_ranking()
    except ObjectDoesNotExist:
        pass


class VenueConfig(AppConfig):
    name = 'venue'

    def ready(self):
        post_migrate.connect(post_migrate_callback, sender=self)
