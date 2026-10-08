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

    # Slideshow
    path('slideshows/', views.SlideshowView.as_view(), name='slideshows'),
    path('slideshows/<int:slideshow_id>/', views.SlideshowDetailView.as_view(), name='slideshow-detail'),

    # Live
    path('livepresentation/', views.LivePresentationView.as_view(), name='livepresentation'),
    path('liveslides/', views.LiveSlidesView.as_view(), name='liveslides'),

    # Parameters
    path('parameters/', views.ParameterSetView.as_view(), name='parameters'),
    path('parameters/<int:section_id>/', views.ParameterSetDetailView.as_view(), name='parameters-detail'),

    # Parameters
    path('globalparameters/', views.GlobalParametersView.as_view(), name='globalparameters'),
    #path('globalparameters/<int:section_id>/', views.GlobalParameterSetDetailView.as_view(), name='globalparameters-detail'),

    # Tags
    path('tags/slides/<str:tag_name>/', views.SlideTagView.as_view(), name='tag-slides'),
    path('tags/<str:tag_name>/slide/<int:slide_id>/', views.SlideTagView.as_view(), name='tag-slide-remove'),
    path('tags/scenes/<str:tag_name>/', views.SceneTagView.as_view(), name='tag-scenes'),
    path('tags/<str:tag_name>/scene/<int:scene_id>/', views.SceneTagView.as_view(), name='tag-scene-remove'),
    path('tags/available/', views.TagView.as_view(), name='available-tags'),
    
    # Maps
    path('maps/layers/', views.MapLayerView.as_view(), name='maps'),
    path('maps/layers/<int:layer_id>/', views.MapLayerDetailsView.as_view(), name='maps'),
]