from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-o2d6u5@lq4$zdtt%64^w!8i4g6yjb!hqnbt)xaph2u++3$wi2@')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# API Keys for RAG system - Use environment variables in production!
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
SERPER_API_KEY = env('SERPER_API_KEY', default='')
