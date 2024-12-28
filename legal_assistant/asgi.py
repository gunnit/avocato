"""
ASGI config for legal_assistant project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_assistant.settings.local')

application = get_asgi_application()
