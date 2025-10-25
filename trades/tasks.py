# tasks.py
from celery import Celery
from django.core.management import call_command
from django.core.cache import cache
from copiqat.celery import app  # Import from copiqat.celery



@app.task(max_retries=3, retry_backoff=True)
def update_prices_task():
    lock_id = "update_prices_lock"
    if cache.add(lock_id, "locked", timeout=60):
        try:
            call_command('update_asset_prices')
            print("Successfully ran update_asset_prices command")
        except Exception as e:
            print(f"Error running update_prices: {e}")
            raise
        finally:
            cache.delete(lock_id)
    else:
        print("Task is already running, skipping...")


