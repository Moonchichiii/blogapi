from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    name = "profiles"

    def ready(self):
        # Import signal handlers to register them
        import profiles.signals
