#!/bin/bash
gunicorn legal_assistant.wsgi:application --bind 0.0.0.0:$PORT
