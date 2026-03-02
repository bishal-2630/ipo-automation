import os
import sys

# Simulate the environment by only allowing imports from specific packages
# (This is just a quick check for common django imports)

print("Starting Import Test...")

try:
    import django
    print("✅ Django")
    import rest_framework
    print("✅ DRF")
    import corsheaders
    print("✅ CorsHeaders")
    import environ
    print("✅ Environ")
    import celery
    print("✅ Celery")
    import redis
    print("✅ Redis")
    import django_celery_beat
    print("✅ Django Celery Beat")
    import dj_database_url
    print("✅ DJ Database URL")
    import psycopg2
    print("✅ Psycopg2")
    import firebase_admin
    print("✅ Firebase Admin")
    
    # Try to load settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    from django.conf import settings
    # Access a setting to trigger setup
    _ = settings.INSTALLED_APPS
    print("✅ Django Settings Loaded")
    
    print("\nAll core dependencies for API look satisfied!")
    
except ImportError as e:
    print(f"\n❌ Missing Dependency: {e}")
except Exception as e:
    print(f"\n❌ Error during setup: {e}")
