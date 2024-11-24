from .base import *
import os

# Security settings
DEBUG = env.bool('DEBUG', default=False)
SECRET_KEY = env('DJANGO_SECRET_KEY')

# Azure Web App default domain and your custom domain
ALLOWED_HOSTS = [
    'avocato.azurewebsites.net',  # Default Azure domain
    'avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net',
    '.azurewebsites.net',
    'viagea.oa.r.appspot.com',  # Google App Engine domain
    '*',  # Temporarily allow all hosts for troubleshooting
]

# Database configuration for Azure PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='avocato'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='projectschool.postgres.database.azure.com'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# File Storage Configuration
try:
    AZURE_ACCOUNT_KEY = env('AZURE_STORAGE_ACCOUNT_KEY')
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    AZURE_ACCOUNT_NAME = env('AZURE_STORAGE_ACCOUNT_NAME', default='greg123')
    AZURE_CONTAINER = env('AZURE_STORAGE_CONTAINER_NAME', default='media')
    AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
    AZURE_LOCATION = env('AZURE_LOCATION', default='francecentral')
except Exception:
    # Fall back to local file storage if Azure storage is not configured
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files configuration
STATIC_URL = '/static/'  # Changed from /assets/ to /static/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security settings
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('DJANGO_SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('DJANGO_CSRF_COOKIE_SECURE', default=True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('DJANGO_SECURE_HSTS_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('DJANGO_SECURE_HSTS_PRELOAD', default=True)

# CORS settings
CORS_ALLOWED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host != '*'
]
CORS_ALLOW_CREDENTIALS = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    }
}

# API Keys
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY')
OPENAI_API_KEY = env('OPENAI_API_KEY')
SERPER_API_KEY = env('SERPER_API_KEY', default='')
