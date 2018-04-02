# Django secure redis
Django caching plugin for django-redis that adds a Serializer class and configuration to support transparent,
symmetrical encryption of cached values using AES 16, 24, or 32 byte encryption.
This plugin also provides encryption for django-rq jobs by simply using the `@secure_redis.secure_rq.job` decorator to annotate the task method instead of using `@django_rq.job`

# Important
Before using this library, make sure that you really need it. By using it, put in mind:
- You are loosing atomic functionalities like `incr()`
- The values stored to redis are now bigger
- Will take more time to set and retrieve data from redis

# Installation
1. Use `pip install` to get this library
2. In `settings.py` in your project, go to `CACHE` settings and ensure you put the following:
 * Add `secure_redis` to `INSTALLED_APPS`
 * Provide base64 encoded 16, 24, or 32 byte `REDIS_SECRET_KEY` for encryption cipher.
 * Configure the `SERIALIZER` setting to use `secure_redis.serializer.SecureSerializer`

# Settings sample

[Django-redis-cache Documentation](
https://media.readthedocs.org/pdf/django-redis-cache/latest/django-redis-cache.pdf)

#### Parsing
NOTE: redis-py comes with two parsers: HiredisParser and PythonParser. The former uses the hiredis library to
parse responses from the redis server, while the latter uses Python. Hiredis is a library that uses C, so it is much faster
than the python parser, but requires installing the library separately.
#### Pickle
The default pickle protocol is -1, which is the highest and latest version. This value should be pinned to a specific
protocol number, since -1 means different things between versions of Python.
#### TCP connction
When working with a TCP connection, it may be beneficial to set the SOCKET_TIMEOUT and
SOCKET_CONNECT_TIMEOUT options to prevent your app from blocking indefinitely.
#### Unix Socket
It is faster to connect using unix sockets rather than TCP.
* edit `/etc/redis/redis.conf`
* comment out 'port' and 'bind' lines
* uncomment the two unixsocket lines
```
unixsocket /var/run/redis/redis.sock
unixsocketperm 700
```
* restart redis `sudo service redis-server restart`

#### DB
The DB option will allow key/values to exist in a different keyspace. The DB value can either be defined in the
OPTIONS or in the LOCATION scheme.
#### KEY_PREFIX
Must be used if sharing the same cache Redis cache with other clients

### Sample using unixsocket:
```
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': '/var/run/redis/redis.sock',
        'OPTIONS': {
            'DB': 1,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'SERIALIZER': 'secure_redis.serializer.SecureSerializer',
            'PICKLE_VERSION': 2,
            'REDIS_SECRET_KEY': '4VQ57H2MldvuAcqybWPenwRe3CXSW5R5JHQPkbthMZI=',
        },
        'KEY_PREFIX': 'app1:secure',
        'TIMEOUT': 60 * 60 * 24
    },
}
```

**NOTE:** Do NOT store REDIS_SECRET_KEY in source code.  Sensitive data should be read in from files that are not committed to source repository.

# Data migration
If you already have an existing data in your redis, you might need to consider data migration for un-encrypted values,
you are free to handle this case as you want, we would suggest to use django management command to handle this case:

1. Keep old redis cache settings and add your new secure django redis cache configuration
2. Make sure your new secure django redis cache settings has different `KEY_PREFIX`
3. Make sure old configutation still point at the correct `LOCATION` and `DB`
4. You can see an example configuration in the previous section of `Settings sample`
5. Make sure either to delete old keys or make sure your redis can holds the new values
6. Code sinppet for sample command is shown below:
```
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.core import cache


class Command(BaseCommand):
    def handle(self, *args, **options):
        new_cache_name = 'default'
        old_cache_name = 'insecure'
        old_key_prefix = 'app1'
        new_prefix = 'app1:secure'
        delete_old_keys = False

        old_cache = cache.caches[old_cache_name]
        new_cache = cache.caches[new_cache_name]

        # Use low level api to access full key name
        existing_keys = old_cache.client.get_client().keys('{}*'.format(old_key_prefix))
        for key in existing_keys:
            if new_prefix not in key:
                actual_key = old_cache.client.reverse_key(key)
                unencrypted_val = old_cache.get(actual_key)
                if new_cache.set(actual_key, unencrypted_val):
                    if delete_old_keys:
                        old_cache.delete(actual_key)

```

# Scheduler related usage
This library also provides additional functionality for that encrypts the payload of RQ jobs. To make use of this functionality, first ensure that `DJANGO_REDIS_SECURE_CACHE_NAME` is defined in your settings (if not set, this setting will default to using the `default` cache). Once configured, replace all instances of the `django_rq.job` decorator with `@secure_redis.secure_rq.job`. The `@secure_redis.secure_rq.job` provides the following functionality:

1. A `delay` method, which can be used when calling the task method (ex: `my_task.delay()`). This method has the same functionality as `django_rq.job.delay`
2. An `enqueue_at` method, which can be used when calling the task method (ex: `my_job.enqueue_at()`). This method has the same functionality as `django_rq.Scheduler.enqueue_at`
3. A `schedule_once` method, which can be used when calling the task method (ex: `my_job.schedule_once()`). This method has the same functionality as `django_rq.Scheduler.schedule`, but will check if the method already exists and will not add it to the scheduler a second time.

## Important:
When using the `@secure_redis.secure_rq.job decorator`, the method name displayed in the Django admin will be that of the wrapped proxy method instead of the actual task method name. If you want to see the actual task method name in the Django admin, you must use `secure_redis.urls` instead of `django_rq.urls` when installing RQ into the Django admin in your `urls.py` file.
