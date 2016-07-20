from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


if hasattr(settings, 'DJANGO_REDIS_SECURE_CACHE_NAME'):
    cache_name = settings.DJANGO_REDIS_SECURE_CACHE_NAME
else:
    cache_name = 'default'

secure_cache_options_settings = settings.CACHES[cache_name]['OPTIONS']
if secure_cache_options_settings['SERIALIZER'] == 'secure_redis.serializer.SecureSerializer':
    if not secure_cache_options_settings.get('REDIS_SECRET_KEY'):
        raise ImproperlyConfigured(
            'REDIS_SECRET_KEY must be defined in settings in secure cache OPTIONS')
