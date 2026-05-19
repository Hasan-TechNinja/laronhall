from django.urls import path
from . import views
urlpatterns = [
    path('organization-types/', views.OrganizationTypeListView.as_view(), name='organization-types'),
    path('create/', views.EventCreateInitView.as_view(), name='event-create'),
    path('my-events/', views.MyEventsView.as_view(), name='my-events'),
    path('<int:id>/name/', views.EventUpdateNameView.as_view(), name='event-update-name'),
    path('<int:id>/estimates/', views.EventUpdateEstimatesView.as_view(), name='event-update-estimates'),
    path('<int:id>/', views.EventDetailView.as_view(), name='event-detail'),
    path('join/', views.EventJoinView.as_view(), name='event-join'),
    path('<int:id>/extend/', views.EventExtendView.as_view(), name='event-extend'),
    path('fundraiser/<int:id>/', views.FundraiserDetailView.as_view(), name='fundraiser-detail'),
    path('fundraiser/<int:id>/name/', views.FundraiserUpdateNameView.as_view(), name='fundraiser-update-name'),
    path('fundraiser/<int:id>/goal/', views.FundraiserUpdateGoalView.as_view(), name='fundraiser-update-goal'),
    path('fundraiser/<int:id>/description/', views.FundraiserUpdateDescriptionView.as_view(), name='fundraiser-update-description'),
    path('<int:event_id>/fundraisers/', views.EventFundraiserListView.as_view(), name='event-fundraiser-list'),
    path('<int:id>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
]