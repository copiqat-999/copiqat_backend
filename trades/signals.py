from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Vault, BuyAndSell
from django_redis import get_redis_connection
from django.core.cache import cache
from .utils import clear_user_trade_cache

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_vault(sender, instance, created, **kwargs):
    if created:
        Vault.objects.create(user=instance)


@receiver(post_save, sender=BuyAndSell)
def clear_trade_cache_on_save(sender, instance, **kwargs):
    clear_user_trade_cache(instance.user.id)

@receiver(post_delete, sender=BuyAndSell)
def clear_trade_cache_on_delete(sender, instance, **kwargs):
    clear_user_trade_cache(instance.user.id)