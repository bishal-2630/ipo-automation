#!/bin/bash
set -e

# Start Redis with a local directory for persistence/logging to avoid permission issues
mkdir -p /app/redis
redis-server --dir /app/redis --daemonize yes

# Run database migrations
python manage.py migrate

# Setup periodic tasks
python manage.py setup_periodic_tasks

# Trigger immediate run for testing/verification
python manage.py run_now

# Start Celery worker in the background
celery -k solo -A config worker --loglevel=info &

# Start Celery beat in the background
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start the Django development server
python manage.py runserver 0.0.0.0:7860
