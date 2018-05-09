from django.apps import AppConfig


class VenueConfig(AppConfig):
    name = 'venue'

    def ready(self):
        import venue.signals
