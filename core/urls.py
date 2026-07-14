from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("health/", views.health_check.as_view(), name="health-check"),
    path("event/<int:event_id>/", views.EventDetailView.as_view(), name="event-detail"),
    path("event/<int:event_id>/authorize/", views.EventAuthorize.as_view(), name="event-authorize"),
    path('monitor/<int:monitor_id>/', views.MonitorView.as_view(), name='monitor'),
    # path('monitor/<int:monitor_id>/update/', views.MonitorView.as_view(), name='monitor-update'),
    path("groups/", views.GroupView.as_view(), name="groups"),
    path("slides/", views.SlideView.as_view(), name="slides"),
    path('slides/<int:slide_id>/', views.SlideDetailView.as_view(), name='slide-detail'),
    path('slides/<int:slide_id>/sections', views.SlideSectionView.as_view(), name='slide-sections'),
    path('tags/slides/<str:tag_name>/', views.SlideTagView.as_view(), name='tag-slides'),
    path('tags/<str:tag_name>/slide/<int:slide_id>/', views.SlideTagView.as_view(), name='tag-slide-remove'),
    path('scenes/', views.SceneView.as_view(), name='scenes'),    
    path('scenes/<int:scene_id>/', views.SceneDetailView.as_view(), name='scene-detail'),
    path('presentations/', views.PresentationView.as_view(), name='presentations'),
    path('presentations/<int:presentation_id>/', views.PresentationDetailView.as_view(), name='presentation-detail'),
    path('tags/scenes/<str:tag_name>/', views.SceneTagView.as_view(), name='tag-scenes'),
    path('tags/<str:tag_name>/scene/<int:scene_id>/', views.SceneTagView.as_view(), name='tag-scene-remove'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('live/', views.LivePresentationView.as_view(), name='live'),
    path('parameters/<int:section_id>/', views.ParameterSetView.as_view(), name='parameters'),
    path('slides/interactive/', views.InteractiveSlidesView.as_view(), name='interactive-slides'),
]
