#!/bin/bash

# Exit on error
set -e

echo "Activating virtual environment..."
source antenv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate

echo "Starting Gunicorn..."
# Use proper timeout and logging settings
gunicorn --bind=0.0.0.0:8000 \
         --timeout 600 \
         --workers 4 \
         --access-logfile '-' \
         --error-logfile '-' \
         --log-level info \
         legal_assistant.wsgi:application
