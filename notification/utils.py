from firebase_admin import messaging
from .models import DeviceToken, Notification

def send_push_notification(user, title, body, data=None):
    if not user:
        return

    # Save to db
    Notification.objects.create(
        user=user,
        title=title,
        body=body,
        data=data
    )

    devices = DeviceToken.objects.filter(user=user, is_active=True)
    if not devices.exists():
        return

    tokens = list(devices.values_list('token', flat=True))
    
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=data if data else {},
        tokens=tokens,
    )
    
    try:
        response = messaging.send_each_for_multicast(message)
        # We can also handle token removal if tokens are unregistered
        if response.failure_count > 0:
            responses = response.responses
            for idx, resp in enumerate(responses):
                if not resp.success:
                    if resp.exception.code in ['messaging/invalid-registration-token', 'messaging/registration-token-not-registered']:
                        DeviceToken.objects.filter(token=tokens[idx]).delete()
    except Exception as e:
        print(f"Error sending push notification: {e}")
