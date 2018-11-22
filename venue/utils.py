import base64
import json
from contextlib import contextmanager

import redis
import rncryptor
from django.utils import translation
from django.conf import settings
import requests


class RedisTemp(object):

    def __init__(self, namespace):
        self.rconn = redis.StrictRedis(host='redis', db=2, password='4e7a84d5')
        if len(namespace.split()) > 1:
            raise Exception('Namespace should not contain spaces')
        else:
            self.namespace = namespace

    def generate_key(self, key):
        return 'temp__' + key + '__' + self.namespace

    def store(self, key, value):
        key = self.generate_key(key)
        json_value = json.dumps(value)
        return self.rconn.set(key, json_value)

    def retrieve(self, key):
        key = self.generate_key(key)
        value = self.rconn.get(key)
        if value:
            return json.loads(value.decode('utf-8'))
        else:
            return value

    def remove(self, key):
        key = self.generate_key(key)
        return self.rconn.delete(key)


# ------------------------------------
# Encryption and decryption functions
# ------------------------------------


def encrypt_data(data, password):
    cryptor = rncryptor.RNCryptor()
    encrypted_data = cryptor.encrypt(data, password)
    encoded_data = base64.b64encode(encrypted_data)
    return encoded_data.decode('utf-8')


def decrypt_data(data, password):
    cryptor = rncryptor.RNCryptor()
    decoded_data = base64.b64decode(data)
    decrypted_data = cryptor.decrypt(decoded_data, password)
    return decrypted_data


@contextmanager
def translation_on(locale):
    translation.activate(locale)
    yield
    translation.deactivate()


def check_language_exists(language_code):
    """
    Check language code exists in the settings
    :param language_code: e.g. 'en'
    :return: bool
    """
    return language_code in [l[0] for l in settings.LANGUAGES]


# ---------------------------------
# Constant Contact helper functions
# ---------------------------------


def send_to_constant_contact(username, email):
    payload = {
        'first_name': username,
        'email_addresses': [{
            'email_address': email,
            'confirm_status': 'CONFIRMED'
        }],
        'lists': [{
            'id': str(settings.CONSTANT_CONTACT_LIST_ID)
        }]
    }
    url = 'https://api.constantcontact.com/v2/contacts?action_by=ACTION_BY_OWNER&api_key='
    url += settings.CONSTANT_CONTACT_ACCESS_TOKEN
    headers = {
        'Authorization': 'Bearer ' + settings.CONSTANT_CONTACT_API_KEY
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp
