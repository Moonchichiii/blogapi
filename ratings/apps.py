from django.apps import AppConfig


class RatingsConfig(AppConfig):
    name = "ratings"

    def ready(self):
        import ratings.signals
