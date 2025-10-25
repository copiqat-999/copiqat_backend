from django.core.cache import cache

def clear_user_trade_cache(user_id):
    """
    Deletes both open and closed trade caches for a specific user.
    """
    cache_keys = [
        f"user_trades_{user_id}_trade_status__iexact=open",
        f"user_trades_{user_id}_trade_status__iexact=closed"
    ]
    for key in cache_keys:
        cache.delete(key)
