import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "copiqat.settings")

app = Celery("copiqat")

# Load settings from Django settings.py using CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()
