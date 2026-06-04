from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("events/", views.EventView.as_view(), name="events"),
    path("groups/", views.GroupView.as_view(), name="groups"),
]
