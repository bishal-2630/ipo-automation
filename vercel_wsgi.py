# Vercel WSGI Handler for IPO Automation
# Force trigger: de4ba9e
import os
from django.core.wsgi import get_wsgi_application

# Set the settings module for the Vercel serverless environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get the WSGI application
app = get_wsgi_application()
