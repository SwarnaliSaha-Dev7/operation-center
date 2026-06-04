from django.core.checks.security.base import CROSS_ORIGIN_OPENER_POLICY_VALUES
from root.applist import SYSTEM_APPS, THIRD_PARTY_APPS, LOCAL_APPS
from pathlib import Path
import os, colorlog

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-j%7k(xa1x^l34fxv!f#++q-scns8%wc*a%!5g450b@%&k$0+_9')

DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if os.getenv('DJANGO_ALLOWED_HOSTS') else ['localhost', '127.0.0.1', '5.189.160.172', 'ops.ellbob.com']

# Security: set DJANGO_SECRET_KEY in .env for production (50+ random chars)
_default_key = 'dev-only-not-for-production-ChangeMeInProduction-8k2mN9xL'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', _default_key)
if not DEBUG and (not SECRET_KEY or len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure-')):
    raise ValueError('Set a long, random DJANGO_SECRET_KEY (50+ chars) in production.')

if DEBUG:
    SECURE_HSTS_SECONDS = 0
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = SYSTEM_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom User with member fields (employee_id, phone, team, department, designation).
# If you already ran migrations with the default User, use a fresh DB or see Django docs for switching.
AUTH_USER_MODEL = 'memberapp.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if os.getenv('CORS_ALLOWED_ORIGINS') else []
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'True').lower() in ('true', '1', 'yes')
CORS_ALLOW_METHODS = os.getenv('CORS_ALLOW_METHODS', '').split(',') if os.getenv('CORS_ALLOW_METHODS') else []
CORS_ALLOW_HEADERS = os.getenv('CORS_ALLOW_HEADERS', '').split(',') if os.getenv('CORS_ALLOW_HEADERS') else []


ROOT_URLCONF = 'root.urls'

templates_dir = [BASE_DIR / 'templates']
for folder in templates_dir:
    folder.mkdir(parents=True, exist_ok=True)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': templates_dir,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notificationapp.context_processors.notification_badge',
                'commonapp.context_processors.global_filter_choices',
            ],
        },
    },
]

WSGI_APPLICATION = 'root.wsgi.application'
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if os.getenv('CSRF_TRUSTED_ORIGINS') else []
CROSS_ORIGIN_OPENER_POLICY_VALUES = os.getenv('CROSS_ORIGIN_OPENER_POLICY_VALUES', '').split(',') if os.getenv('CROSS_ORIGIN_OPENER_POLICY_VALUES') else []


DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
}

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

# Login / logout
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Member list "Online" column: counts users with a non-expired row in django_session
# (browser has a session cookie after login). Does not work with cookie-only
# session backends (e.g. signed_cookies) because sessions are not stored in the DB.
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# Refresh session on each request so active browsing keeps the session alive.
SESSION_SAVE_EVERY_REQUEST = True


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' 
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

STATIC_URL = '/static/'
# Project assets (versioned in git). Do not set STATIC_ROOT to the same path.
STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles',
]
STATIC_ROOT = BASE_DIR / 'static'
for folder in list(STATICFILES_DIRS) + [STATIC_ROOT]:
    folder.mkdir(parents=True, exist_ok=True)


LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_MAX_BYTES = 1024 * 1024 * int(os.getenv('DJANGO_LOG_MB', '10'))
LOG_BACKUP_COUNT = int(os.getenv('DJANGO_LOG_BACKUP', '5'))
LOG_LEVEL = 'DEBUG' if DEBUG else 'WARNING'

try:
    CONSOLE_FORMATTER = 'colored' if DEBUG else 'verbose'
    _formatters = {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
        'exception': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d}\n{message}',
            'style': '{',
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)s %(asctime)s %(module)s %(message)s',
            'log_colors': {
                'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow',
                'ERROR': 'red', 'CRITICAL': 'bold_red',
            },
        },
    }
except ImportError:
    CONSOLE_FORMATTER = 'verbose'
    _formatters = {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
        'exception': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d}\n{message}',
            'style': '{',
        },
    }

_rotating = {
    'class': 'logging.handlers.RotatingFileHandler',
    'maxBytes': LOG_MAX_BYTES,
    'backupCount': LOG_BACKUP_COUNT,
}
_django_logger = {'handlers': ['rotating_file', 'console'], 'level': LOG_LEVEL}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': _formatters,
    'handlers': {
        'rotating_file': {
            **_rotating,
            'filename': LOG_DIR / 'django.log',
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': CONSOLE_FORMATTER,
        },
        'exception_file': {
            **_rotating,
            'filename': LOG_DIR / 'exceptions.log',
            'level': 'ERROR',
            'formatter': 'exception',
        },
    },
    'loggers': {
        'django': {**_django_logger, 'propagate': True},
        'django.server': {**_django_logger, 'propagate': False},
        'exceptions': {'handlers': ['exception_file'], 'level': 'ERROR', 'propagate': False},
    },
}