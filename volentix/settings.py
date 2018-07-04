"""
Django settings for volentix project.

Generated by 'django-admin startproject' using Django 1.11.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import redis
import rollbar
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a85zgf@jc^_!8jcu-(j9l7p5z%ck+rwhceff2=@(n8o00%j2%o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['localhost', '.volentix.com', '.volentix.io', '.venue.ninja', 'venue-service']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_media_fixtures',
    'django.contrib.humanize',
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'constance',
    'ws4redis',
    'venue'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

CONSTANCE_ADDITIONAL_FIELDS = {
    'textfield': [
        'django.forms.CharField', 
        {'widget': 'django.forms.Textarea', 'required': False}
    ]
}

CONSTANCE_CONFIG = {
    'DISABLE_SIGN_UP': (False, 'Disable user sign up'),
    'VTX_AVAILABLE': (120000, 'Total VTX tokens available'),
    'TEST_MODE': (DEBUG, 'Test mode for scraping and points calculations. \
        Signatures are always marked as found under test mode.'),
    'POST_POINTS_MULTIPLIER': (100, 'Points for each new post'),
    'MATURATION_PERIOD': (24, 'Maturation period'),
    'UPTIME_PERCENTAGE_THRESHOLD': (90, 'Percentage of uptime required'),
    'CLOSED_BETA_MODE': (False, 'Enable closed beta mode'),
    'SIGN_UP_WHITELIST': ('', 'Sign up whitelist', 'textfield'),
    'ENABLE_CLICK_TRACKING': (False, 'Enable tracking of clicks in signature links')
}

REDIS_PASSWORD = config('REDIS_PASSWORD', default='4e7a84d5')

CONSTANCE_REDIS_CONNECTION = {
    'password': REDIS_PASSWORD,
    'host': config('REDIS_HOST', default='redis'),
    'port': 6379,
    'db': 0,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddleware'
]

ROOT_URLCONF = 'volentix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'venue_app', 'dist')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'volentix.wsgi_django.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('POSTGRES_NAME', default='venuepostgress'),
        'USER': config('POSTGRES_USER', default='venueadmin'), 
        'PASSWORD': config('POSTGRES_PASSWORD', default='BxKkpaihl67B'),
        'HOST': config('POSTGRES_HOST', default='postgres')
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

CELERY_BROKER_URL = 'redis://:4e7a84d5@redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://:4e7a84d5@redis:6379/1'
CELERY_TIMEZONE = 'UTC'

USER_SCRAPE_INTERVAL = 300  # seconds
CELERY_BEAT_SCHEDULE = {
    'periodic-data-update': {
        'task': 'venue.tasks.update_data',
        'schedule': USER_SCRAPE_INTERVAL
    },
    'periodic-spam-detection': {
        'task': 'venue.tasks.detect_spammers',
        'schedule': 3600 * 6  # Every 6 hours
    }
}

POSTMARK_TOKEN = '53ac5b12-1edc-43bc-9581-561c143f7352'
POSTMARK_SENDER_EMAIL = 'venue@volentix.com'

CORS_ORIGIN_WHITELIST = ('localhost:8080', 'localhost:8000', 'venue.volentix.io')
CORS_ORIGIN_ALLOW_ALL = True
CSRF_COOKIE_NAME = "csrftoken"

ROLLBAR = {
    'access_token': '529481318c454550884186f042d9b4bc',
    'environment': 'development' if DEBUG else 'production',
    'branch': 'master',
    'root': BASE_DIR,
}


rollbar.init(
    '529481318c454550884186f042d9b4bc',
    environment='development' if DEBUG else 'production'
)


def celery_base_data_hook(request, data):
    del request
    data['framework'] = 'celery'


rollbar.BASE_DATA_HOOK = celery_base_data_hook

# Create the logs folder if it does not exist yet
log_folder = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(log_folder):
    os.mkdir(log_folder)


if DEBUG:
    VENUE_DOMAIN = 'http://localhost:8000'
    VENUE_FRONTEND = 'http://localhost:3000'
else:
    VENUE_DOMAIN = config('VENUE_DOMAIN', default='http://demo.venue.ninja')
    VENUE_FRONTEND = config('VENUE_FRONTEND', default='http://demo.venue.ninja')
    # VENUE_DOMAIN = config('VENUE_DOMAIN', default='https://venue.volentix.io')
    # VENUE_FRONTEND = config('VENUE_FRONTEND', default='https://venue.volentix.io')

# if not DEBUG:
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True

WEBSOCKET_URL = '/ws/'
WS4REDIS_PREFIX = 'ws'
WS4REDIS_CONNECTION = {
    'host': 'redis',
    'port': 6379,
    'db': 3,
    'password': REDIS_PASSWORD
}
WS4REDIS_EXPIRE = 0  # Messages expire immediately


REDIS_DB = redis.StrictRedis(
    host='redis',
    port=6379,
    db=4,
    password=REDIS_PASSWORD,
    decode_responses=True
)
