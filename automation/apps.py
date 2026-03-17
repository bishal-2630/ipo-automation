import os
import firebase_admin
from firebase_admin import credentials
from django.apps import AppConfig
from django.conf import settings

class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automation'

    def ready(self):
        # Initialize Firebase Admin SDK
        firebase_cred_path = os.path.join(settings.BASE_DIR, 'config', 'firebase_vcc.json')
        
        try:
            # Check if already initialized
            firebase_admin.get_app()
            return
        except ValueError:
            pass

        if os.path.exists(firebase_cred_path):
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully from file.")
        else:
            # Fallback: load from base64-encoded env variable
            import base64, json
            b64 = os.environ.get("FIREBASE_CREDENTIALS_B64", "")
            if b64:
                try:
                    cred_json = json.loads(base64.b64decode(b64).decode())
                    cred = credentials.Certificate(cred_json)
                    firebase_admin.initialize_app(cred)
                    print("Firebase Admin SDK initialized successfully from environment variable.")
                except Exception as e:
                    print(f"Warning: Failed to initialize Firebase from FIREBASE_CREDENTIALS_B64: {e}")
            else:
                print(f"Warning: Firebase credentials not found (tried {firebase_cred_path} and FIREBASE_CREDENTIALS_B64)")
