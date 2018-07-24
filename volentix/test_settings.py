from volentix.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('TEST_POSTGRES_NAME', default='venuepostgress'),
        'USER': config('TEST_POSTGRES_USER', default='venueadmin'), 
        'PASSWORD': config('TEST_POSTGRES_PASSWORD', default='BxKkpaihl67B'),
        'HOST': config('TEST_POSTGRES_HOST', default='postgres')
    }
}