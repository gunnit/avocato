#!/bin/bash

# Activate virtual environment
source antenv/bin/activate

# Apply database migrations
python manage.py migrate

# Start Gunicorn
gunicorn --bind=0.0.0.0:8000 legal_assistant.wsgi:application
