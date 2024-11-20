from .base import *
from decouple import config

# Security settings
DEBUG = False
SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = [
    'avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net',
    '.azurewebsites.net',
]

# Database configuration for Azure PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

# Azure Blob Storage configuration
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
AZURE_ACCOUNT_NAME = config('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = config('AZURE_STORAGE_ACCOUNT_KEY')
AZURE_CONTAINER = config('AZURE_STORAGE_CONTAINER_NAME', default='media')
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
AZURE_LOCATION = 'germanywestcentral'  # Matches your Azure region

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS settings
CORS_ALLOWED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS
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
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# App Service Plan: ASP-assitants-9053 (B1: 1)
# Operating System: Linux
# Location: Germany West Central
# Subscription ID: 35b21a57-0665-4790-9112-a29a2a5ece6c
