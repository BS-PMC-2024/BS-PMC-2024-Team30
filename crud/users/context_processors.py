from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
        read_notifications = Notification.objects.filter(user=request.user, is_read=True)
        return {
            'unread_notifications': unread_notifications,
            'read_notifications': read_notifications,
        }
    return {}
