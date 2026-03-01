from firebase_admin import messaging
from .models import FCMToken
import logging

logger = logging.getLogger(__name__)

def send_fcm_notification(user, title, body, data=None):
    """
    Sends a push notification to all devices registered for a specific user.
    """
    tokens = FCMToken.objects.filter(user=user).values_list('token', flat=True)
    if not tokens:
        logger.info(f"No FCM tokens found for user {user.username}")
        return

    # Create a list of messages for multicasting
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=list(tokens),
    )

    try:
        response = messaging.send_multicast(message)
        logger.info(f"Successfully sent {response.success_count} messages for user {user.username}")
        if response.failure_count > 0:
            logger.warning(f"Failed to send {response.failure_count} messages.")
            # Optional: Clean up invalid tokens
            for idx, res in enumerate(response.responses):
                if not res.success:
                    # Token might be invalid/expired
                    invalid_token = list(tokens)[idx]
                    FCMToken.objects.filter(token=invalid_token).delete()
    except Exception as e:
        logger.error(f"Error sending FCM notification: {str(e)}")
