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
from django.core.management.utils import get_random_secret_key

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY', default=get_random_secret_key())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    'localhost',
    '.volentix.com',
    '.volentix.io',
    '.venue.ninja',
    'venue-service',
    '.dev.vlabs.ninja',
    '.vlabs.ninja'
]

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
    'knox',
    'corsheaders',
    'constance',
    'ws4redis',
    'venue'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'knox.auth.TokenAuthentication',
    ),
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

if not DEBUG:
    MIDDLEWARE.append('rollbar.contrib.django.middleware.RollbarNotifierMiddleware')

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
        'PASSWORD': config('POSTGRES_PASSWORD', default='badpassword'),
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


# Media files settings

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'


# Redis generic settings

REDIS_PASSWORD = config('REDIS_PASSWORD', default='4e7a84d5')

REDIS_HOST = config('REDIS_HOST', default='redis')

REDIS_PORT = config('REDIS_PORT', default=6379)

try:
    REDIS_PORT = int(REDIS_PORT)
except ValueError:
    REDIS_PORT = 6379

# Celery settings

REDIS_URL = 'redis://:{}@{}:{}'.format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT)

# CELERY_BROKER_URL = REDIS_URL + '/0'

# CELERY_RESULT_BACKEND = REDIS_URL+ '/1'
CELERY_BROKER_URL = 'redis://:4e7a84d5@redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://:4e7a84d5@redis:6379/1'

CELERY_TIMEZONE = 'UTC'

USER_SCRAPE_INTERVAL = 300  # seconds

CELERY_BEAT_SCHEDULE = {
    'periodic-data-update': {
        'task': 'venue.tasks.update_data',
        'schedule': USER_SCRAPE_INTERVAL
    },
    # # detect spammers doesn't exist
    # 'periodic-spam-detection': {
    #     'task': 'venue.tasks.detect_spammers',
    #     'schedule': 3600 * 6  # Every 6 hours
    # }
}


# Constance celery backend settings

CONSTANCE_REDIS_CONNECTION = {
    'password': REDIS_PASSWORD,
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': 0,
}


# Websocket settings

WEBSOCKET_URL = '/ws/'

WS4REDIS_PREFIX = 'ws'

WS4REDIS_CONNECTION = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': 3,
    'password': REDIS_PASSWORD
}

WS4REDIS_EXPIRE = 0  # Messages expire immediately


# Redis key-value DB settings

REDIS_DB = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=4,
    password=REDIS_PASSWORD,
    decode_responses=True
)


# Postmark settings

POSTMARK_TOKEN = config('POSTMARK_TOKEN', default='POSTMARK_API_TEST')

POSTMARK_SENDER_EMAIL = config('POSTMARK_SENDER_EMAIL', default='sender@example.com')


# CORS settings

CORS_ORIGIN_WHITELIST = ('localhost:8080', 'localhost:8000', 'venue.volentix.io')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_COOKIE_NAME = "csrftoken"


# Rollbar settings

ROLLBAR_TOKEN = config('ROLLBAR_TOKEN', default='')

if not DEBUG:
    ROLLBAR = {
        'access_token': ROLLBAR_TOKEN,
        'environment': 'development' if DEBUG else 'production',
        'branch': 'master',
        'root': BASE_DIR,
    }


    rollbar.init(
        ROLLBAR_TOKEN,
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


# Venue domain and venue frontend URLs

VENUE_DOMAIN = config('VENUE_DOMAIN', default='http://localhost:8000')
VENUE_FRONTEND = config('VENUE_FRONTEND', default='http://localhost:3000')


# Languages

LANGUAGES = (
    'en',
    'fr',
    'jp',
    'es',
    'pt',
    'ru',
    'zh',
    'ko',
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)
