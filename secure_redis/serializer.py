from __future__ import unicode_literals

from Crypto.Cipher import AES
from Crypto import Random
import base64
import binascii

import django_redis.serializers.pickle

from . import settings


class SecureSerializer(django_redis.serializers.pickle.PickleSerializer):
    def __init__(self, options):
        super(SecureSerializer, self).__init__(options)

        redis_secret_key = options.get('REDIS_SECRET_KEY', None)

        if redis_secret_key is None:
            raise Exception('REDIS_SECRET_KEY is required')

        try:
            self.aes_key = base64.b64decode(redis_secret_key)
        except binascii.Error:
            raise Exception('REDIS_SECRET_KEY must be base64 encoded')

        if len(self.aes_key) not in (16, 24, 32):
            raise Exception('REDIS_SECRET_KEY must be 16, 24, or 32 bytes long')

    def encrypt(self, plaintext):
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.aes_key, AES.MODE_CFB, iv)
        ciphertext = cipher.encrypt(plaintext)
        return (iv + ciphertext)

    def decrypt(self, ciphertext):
        iv = ciphertext[:AES.block_size]
        cipher = AES.new(self.aes_key, AES.MODE_CFB, iv)
        return cipher.decrypt(ciphertext[AES.block_size:])

    def dumps(self, value):
        plaintext = super(SecureSerializer, self).dumps(value)
        return self.encrypt(plaintext)

    def loads(self, value):
        plaintext = self.decrypt(value)
        return super(SecureSerializer, self).loads(plaintext)


default_secure_serializer = SecureSerializer(settings.get_secure_cache_opts())
