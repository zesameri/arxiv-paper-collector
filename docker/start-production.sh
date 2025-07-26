#!/bin/bash

# Production startup script for Django on Cloud Run

set -e

echo "🚀 Starting ArXiv Paper Collector on Cloud Run"

# Change to backend directory first
cd backend

# Use Python directly since we installed with pip
echo "🔧 Using pip-installed dependencies..."

# Run Django migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static files collection failed (continuing anyway)"

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('✅ Superuser already exists')
" || echo "⚠️  Superuser creation failed (continuing anyway)"

# Start Gunicorn directly
echo "🚀 Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application

# Run Django migrations using the virtual environment directly
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static files collection failed (continuing anyway)"

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('✅ Superuser already exists')
" || echo "⚠️  Superuser creation failed (continuing anyway)"

# Start Gunicorn using the virtual environment directly
echo "🚀 Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application 