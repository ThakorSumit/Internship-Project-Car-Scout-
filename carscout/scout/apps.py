from django.apps import AppConfig


class ScoutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scout'
    def ready(self):
        import scout.signals