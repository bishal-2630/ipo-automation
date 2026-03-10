import os
import firebase_admin
from firebase_admin import credentials
from django.apps import AppConfig
from django.conf import settings

class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automation'

    def ready(self):
        import sys
        print("AutomationConfig: ready() called. Initializing Firebase...", file=sys.stderr)
        # Initialize Firebase Admin SDK
        firebase_cred_path = os.path.join(settings.BASE_DIR, 'config', 'firebase_vcc.json')
        if os.path.exists(firebase_cred_path):
            try:
                # Check if already initialized to avoid ValueError
                firebase_admin.get_app()
                print("AutomationConfig: Firebase already initialized.", file=sys.stderr)
            except ValueError:
                print(f"AutomationConfig: Initializing Firebase from {firebase_cred_path}", file=sys.stderr)
                cred = credentials.Certificate(firebase_cred_path)
                firebase_admin.initialize_app(cred)
                print("AutomationConfig: Firebase Admin SDK initialized successfully.", file=sys.stderr)
        else:
            print(f"AutomationConfig: Warning: Firebase credentials not found at {firebase_cred_path}", file=sys.stderr)
