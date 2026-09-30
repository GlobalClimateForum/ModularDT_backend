from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("health/", views.health_check.as_view(), name="health-check"),
    path('monitor/', views.MonitorView.as_view(), name='monitor'),
    path('monitor/<int:monitor_id>/', views.MonitorDetailView.as_view(), name='monitor-detail'),
    path("participants/", views.ParticipantView.as_view(), name="participants"),
    path("participants/<int:participant_id>/", views.ParticipantDetailView.as_view(), name="participant-detail"),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('moderator/', views.ModeratorView.as_view(), name='moderator'),
    path('events/', views.EventView.as_view(), name='events'),
    path('events/<int:event_id>/', views.EventDetailView.as_view(), name='event-detail'),
    path('authorize/<str:pin>/', views.Authorize.as_view(), name='authorize'),
    path('authorize/', views.Authorize.as_view(), name='authorize_post')
]
