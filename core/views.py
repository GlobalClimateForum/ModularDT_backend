from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.utils import timezone

from .models import Event, Group
import datetime


def index(request):
    return HttpResponse("Hello, welcome to the Decision Theater backend server.")


class EventView(View):

    def get(self, request):
        events = Event.objects.all()
        event_list = [event.name for event in events]
        return HttpResponse(f"Events: {', '.join(event_list)}")

    def post(self, request, *args, **kwargs):
        event_name = request.POST.get("name")
        event_description = request.POST.get("description", "")
        event_date = request.POST.get("date") or timezone.now()
        n_groups = int(request.POST.get("n_groups", 3))
        n_monitor = int(request.POST.get("n_monitor", 1))

        event = Event.objects.create(
            name=event_name,
            description=event_description,
            date=event_date,
            n_groups=n_groups,
            n_monitor=n_monitor,
        )
        return HttpResponse(f"Event '{event_name}' created successfully.")

class GroupView(View):
    def get(self, request):
        groups = Group.objects.all()
        group_list = [group.name for group in groups]
        return HttpResponse(f"Groups: {', '.join(group_list)}")

    def post(self, request, *args, **kwargs):
        group_name = request.POST.get("name")
        group = Group.objects.create(name=group_name)
        return HttpResponse(f"Group '{group_name}' created successfully.")