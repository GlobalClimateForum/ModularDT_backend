from django.urls import path
from . import views

urlpatterns = [
    # Slides
    path('slides/', views.SlideView.as_view(), name='slides'),
    path('slides/interactive/', views.InteractiveSlidesView.as_view(), name='interactive-slides'),
    path('slides/ipanels/', views.InteractivePanelsView.as_view(), name='interactive-panels'),
    path('slides/<int:slide_id>/', views.SlideDetailView.as_view(), name='slide-detail'),
    path('slides/<int:slide_id>/sections', views.SlideSectionView.as_view(), name='slide-sections'),

    # Scenes
    path('scenes/', views.SceneView.as_view(), name='scenes'),
    path('scenes/<int:scene_id>/', views.SceneDetailView.as_view(), name='scene-detail'),

    # Presentations
    path('presentations/', views.PresentationView.as_view(), name='presentations'),
    path('presentations/<int:presentation_id>/', views.PresentationDetailView.as_view(), name='presentation-detail'),

    # Live
    path('livepresentation/', views.LivePresentationView.as_view(), name='livepresentation'),
    path('liveslides/', views.LiveSlidesView.as_view(), name='liveslides'),

    # Parameters
    path('parameters/<int:section_id>/', views.ParameterSetView.as_view(), name='parameters'),

    # Tags
    path('tags/slides/<str:tag_name>/', views.SlideTagView.as_view(), name='tag-slides'),
    path('tags/<str:tag_name>/slide/<int:slide_id>/', views.SlideTagView.as_view(), name='tag-slide-remove'),
    path('tags/scenes/<str:tag_name>/', views.SceneTagView.as_view(), name='tag-scenes'),
    path('tags/<str:tag_name>/scene/<int:scene_id>/', views.SceneTagView.as_view(), name='tag-scene-remove'),
]