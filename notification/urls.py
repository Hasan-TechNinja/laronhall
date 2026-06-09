from django.urls import path
from .views import (
    RegisterDeviceTokenView, 
    DeregisterDeviceTokenView,
    NotificationListView, 
    NotificationMarkAsReadView, 
    NotificationDeleteView
)

urlpatterns = [
    path('register-token/', RegisterDeviceTokenView.as_view(), name='register_token'),
    path('deregister-token/', DeregisterDeviceTokenView.as_view(), name='deregister_token'),
    path('list/', NotificationListView.as_view(), name='notification_list'),
    
    path('<int:pk>/mark-as-read/', NotificationMarkAsReadView.as_view(), name='notification_mark_read'),
    path('mark-all-as-read/', NotificationMarkAsReadView.as_view(), name='notification_mark_all_read'),
    
    path('<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification_delete'),
    path('delete-all/', NotificationDeleteView.as_view(), name='notification_delete_all'),
]