from django.urls import path
from . import views
urlpatterns = [
    path('organization-types/', views.OrganizationTypeListView.as_view(), name='organization-types'),
    path('create/', views.EventCreateInitView.as_view(), name='event-create'),
    path('<int:id>/update/', views.EventUpdateView.as_view(), name='event-update'),
    path('my-events/', views.MyEventsView.as_view(), name='my-events'),
    path('my-events/history/', views.MyEventsHistoryView.as_view(), name='my-events-history'),
    path('<int:id>/', views.EventDetailView.as_view(), name='event-detail'),
    path('<int:id>/detailed/', views.EventDetailedView.as_view(), name='event-detailed'),
    path('join/', views.EventJoinView.as_view(), name='event-join'),
    path('<int:id>/extend/', views.EventExtendView.as_view(), name='event-extend'),
    path('fundraiser/<int:id>/', views.FundraiserDetailView.as_view(), name='fundraiser-detail'),
    path('fundraiser/<int:id>/public/', views.FundraiserPublicView.as_view(), name='fundraiser-public'),
    path('fundraiser/<int:id>/name/', views.FundraiserUpdateNameView.as_view(), name='fundraiser-update-name'),
    path('fundraiser/<int:id>/goal/', views.FundraiserUpdateGoalView.as_view(), name='fundraiser-update-goal'),
    path('fundraiser/<int:id>/description/', views.FundraiserUpdateDescriptionView.as_view(), name='fundraiser-update-description'),
    path('fundraiser/<int:id>/media/', views.FundraiserUpdateMediaView.as_view(), name='fundraiser-update-media'),
    path('<int:event_id>/fundraisers/', views.EventFundraiserListView.as_view(), name='event-fundraiser-list'),
    path('<int:event_id>/my-fundraiser/', views.MyFundraiserDetailView.as_view(), name='my-fundraiser-detail'),
    path('<int:id>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
    path('<int:event_id>/leaderboard/', views.EventLeaderboardView.as_view(), name='event-leaderboard'),
    path('fundraiser/<int:id>/supporters/', views.FundraiserSupporterListView.as_view(), name='fundraiser-supporters'),
]