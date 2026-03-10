"""
WSGI config for ipo_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

print("WSGI: Starting WSGI application initialization...", file=sys.stderr)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    print("WSGI: Calling get_wsgi_application()...", file=sys.stderr)
    application = get_wsgi_application()
    print("WSGI: get_wsgi_application() completed successfully.", file=sys.stderr)
except Exception as e:
    print(f"WSGI: Error during initialization: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise
