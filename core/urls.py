from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("event/<int:event_id>/", views.EventDetailView.as_view(), name="event-detail"),
    path("event/<int:event_id>/authorize/", views.EventAuthorize.as_view(), name="event-authorize"),
    path("groups/", views.GroupView.as_view(), name="groups"),
    path("slides/", views.SlideView.as_view(), name="slides"),
    path('slides/<int:slide_id>/', views.SlideDetailView.as_view(), name='slide-detail'),
    path('slides/<int:slide_id>/', views.SlideDetailView.as_view(), name='slide-update'),
    path('slides/<int:slide_id>/sections', views.SlideSectionView.as_view(), name='slide-sections'),
    path('tags/<str:tag_name>/', views.SlideTagView.as_view(), name='tag-slides'),
    path('tags/<str:tag_name>/slide/<int:slide_id>/', views.SlideTagView.as_view(), name='tag-remove'),
    path('monitor/<int:event_id>/', views.MonitorView.as_view(), name='monitor'),
    path('scene/', views.SceneView.as_view(), name='scene')
]
