import os

from .base import *

# Security settings
DEBUG = env.bool('DEBUG', default=False)
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-o2d6u5@lq4$zdtt%64^w!8i4g6yjb!hqnbt)xaph2u++3$wi2@')

# Azure Web App default domain and your custom domain
ALLOWED_HOSTS = [
    'avocato.azurewebsites.net',
    'avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net',
    '.azurewebsites.net',
    'themis.pugliai.com',
    os.environ.get('WEBSITE_HOSTNAME', 'localhost'),  # Azure App Service hostname
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'https://themis.pugliai.com',
    'https://avocato.azurewebsites.net',
    'https://avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net'
]

# Add WhiteNoise to INSTALLED_APPS before django.contrib.staticfiles
INSTALLED_APPS = [
                     'whitenoise.runserver_nostatic',  # Add this before django.contrib.staticfiles
                 ] + INSTALLED_APPS

# Database configuration for Azure PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='avocato'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='projectschool.postgres.database.azure.com'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Middleware configuration - ensure WhiteNoise is after SecurityMiddleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise right after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# File Storage Configuration
DEFAULT_FILE_STORAGE = 'cases.views.azure.AzureMediaStorage'

# Static files configuration - use environment variables
STATIC_URL = os.environ.get('DJANGO_STATIC_URL', '/assets/')
STATIC_ROOT = os.environ.get('DJANGO_STATIC_ROOT', os.path.join(BASE_DIR, 'staticfiles'))
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'assets'),
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False  # More forgiving in production
WHITENOISE_USE_FINDERS = False
WHITENOISE_AUTOREFRESH = False
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz',
                                       'br', 'swf', 'flv', 'woff', 'woff2']

# Security settings
# SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
# SESSION_COOKIE_SECURE = env.bool('DJANGO_SESSION_COOKIE_SECURE', default=True)
# CSRF_COOKIE_SECURE = env.bool('DJANGO_CSRF_COOKIE_SECURE', default=True)
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=31536000)
# SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('DJANGO_SECURE_HSTS_SUBDOMAINS', default=True)
# SECURE_HSTS_PRELOAD = env.bool('DJANGO_SECURE_HSTS_PRELOAD', default=True)

# CORS settings
CORS_ALLOWED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host != '*'
]
CORS_ALLOW_CREDENTIALS = True

# Comprehensive logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'whitenoise': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'gunicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# Ensure logs directory exists
if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.makedirs(os.path.join(BASE_DIR, 'logs'))

# API Keys
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY')
OPENAI_API_KEY = env('OPENAI_API_KEY')
SERPER_API_KEY = env('SERPER_API_KEY', default='')
