from django.apps import AppConfig


class TradesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trades"

    default_auto_field = "django.db.models.BigAutoField"
    name = "trades"  # your app name

    def ready(self):
        import trades.signals  # make sure this matches your app and file
