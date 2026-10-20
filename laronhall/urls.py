"""
URL configuration for laronhall project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from shop.views import admin_dashboard_html_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.views.decorators.cache import cache_page


urlpatterns = [
    path('admin/dashboard/', admin_dashboard_html_view, name='admin-dashboard'),
    path('admin/', admin.site.urls),

    path('auth/', include('authentication.urls')),
    path('event/', include('event.urls')),
    path('shop/', include('shop.urls')),
    path('notification/', include('notification.urls')),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
]

@cache_page(60 * 60 * 24)  # Cache media files in Redis for 24 hours
def cached_media_serve(request, path, document_root=None, show_indexes=False):
    return serve(request, path, document_root=document_root, show_indexes=show_indexes)

from django.urls import re_path

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', cached_media_serve, {'document_root': settings.MEDIA_ROOT}),
]

# Force unregister models from the Django admin dashboard
try:
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    from django.contrib.auth.models import Group
    
    admin.site.unregister(OutstandingToken)
    admin.site.unregister(BlacklistedToken)
    admin.site.unregister(Group)
except Exception:
    pass