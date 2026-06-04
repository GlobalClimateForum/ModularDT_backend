from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("events/", views.EventView.as_view(), name="events"),
    path("groups/", views.GroupView.as_view(), name="groups"),
    path("slides/", views.SlideView.as_view(), name="slides"),
    path('slides/<int:slide_id>/', views.SlideDetailView.as_view(), name='slide-detail'),
    path('slides/<int:slide_id>/', views.SlideDetailView.as_view(), name='slide-update'),
]
