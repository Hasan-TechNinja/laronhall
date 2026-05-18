from django.urls import path
from . import views
urlpatterns = [
    path('organization-types/', views.OrganizationTypeListView.as_view(), name='organization-types'),
    path('create/', views.EventCreateInitView.as_view(), name='event-create'),
    path('my-events/', views.MyEventsView.as_view(), name='my-events'),
    path('<int:id>/name/', views.EventUpdateNameView.as_view(), name='event-update-name'),
    path('<int:id>/estimates/', views.EventUpdateEstimatesView.as_view(), name='event-update-estimates'),
    path('<int:id>/', views.EventDetailView.as_view(), name='event-detail'),
]