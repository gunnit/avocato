from .base import *

# Security settings
DEBUG = True  # Temporarily enable debug for troubleshooting
SECRET_KEY = 'django-insecure-o2d6u5@lq4$zdtt%64^w!8i4g6yjb!hqnbt)xaph2u++3$wi2@'

ALLOWED_HOSTS = [
    'avocato-fvhmgsdxgtcbdxhz.germanywestcentral-01.azurewebsites.net',
    '.azurewebsites.net',
]

# Database configuration for Azure PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'avocato',
        'USER': 'postgres',
        'PASSWORD': 'Born1984!@',
        'HOST': 'projectschool.postgres.database.azure.com',
        'PORT': '5432',
        'OPTIONS': {'sslmode': 'require'},
    }
}

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'cases/templates'),
            os.path.join(BASE_DIR, 'legal_rag/templates'),
        ],
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

# Azure Blob Storage configuration
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
AZURE_ACCOUNT_NAME = 'greg123'
AZURE_ACCOUNT_KEY = 'your-storage-key'  # Replace with actual key from Azure Portal
AZURE_CONTAINER = 'media'
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
AZURE_LOCATION = 'francecentral'

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/assets/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'assets'),
]

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
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
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# API Keys
ANTHROPIC_API_KEY = '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'
OPENAI_API_KEY = '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'
SERPER_API_KEY = '4fcf1f4b77fa58bb96a0071e2800dbb246e814d6'
