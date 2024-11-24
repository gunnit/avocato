#!/bin/bash

# Activate virtual environment
source antenv/bin/activate

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn with proper settings
gunicorn --bind=0.0.0.0:8000 --timeout 600 --access-logfile '-' --error-logfile '-' legal_assistant.wsgi:application
