from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("health/", views.health_check.as_view(), name="health-check"),
    path("event/<int:event_id>/", views.EventDetailView.as_view(), name="event-detail"),
    path("event/<int:event_id>/authorize/", views.EventAuthorize.as_view(), name="event-authorize"),
    path('monitor/<int:monitor_id>/', views.MonitorView.as_view(), name='monitor'),
    path("participants/", views.ParticipantView.as_view(), name="participants"),
    path("participants/<int:participant_id>/", views.ParticipantDetailView.as_view(), name="participant-detail"),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('moderator/', views.ModeratorView.as_view(), name='moderator')
]
