from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import DeviceToken, Notification

class RegisterDeviceTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        platform = request.data.get('platform', 'unknown')
        device_id = request.data.get('device_id')
        osVersion = request.data.get('osVersion')
        deviceName = request.data.get('deviceName')

        device_token, created = DeviceToken.objects.get_or_create(user=request.user, token=token)
        device_token.platform = platform
        device_token.device_id = device_id
        device_token.osVersion = osVersion
        device_token.deviceName = deviceName
        device_token.is_active = True
        device_token.save()

        return Response({'message': 'Token registered successfully'}, status=status.HTTP_200_OK)

class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        data = [{
            'id': noti.id,
            'title': noti.title,
            'body': noti.body,
            'data': noti.data,
            'is_read': noti.is_read,
            'created_at': noti.created_at
        } for noti in notifications]
        return Response(data, status=status.HTTP_200_OK)

class NotificationMarkAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk=None):
        if pk:
            try:
                notification = Notification.objects.get(id=pk, user=request.user)
                notification.is_read = True
                notification.save()
                return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)
            except Notification.DoesNotExist:
                return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)

class NotificationDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk=None):
        if pk:
            try:
                notification = Notification.objects.get(id=pk, user=request.user)
                notification.delete()
                return Response({'message': 'Notification deleted successfully'}, status=status.HTTP_200_OK)
            except Notification.DoesNotExist:
                return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            Notification.objects.filter(user=request.user).delete()
            return Response({'message': 'All notifications deleted successfully'}, status=status.HTTP_200_OK)
