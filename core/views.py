from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.utils import timezone
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import json

from .models import Event, Group, Slide
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
        groups_data = [{"id": group.id, "name": group.name} for group in groups]
        return JsonResponse({"groups": groups_data})

    def post(self, request, *args, **kwargs):
        group_name = request.POST.get("name")
        group = Group.objects.create(name=group_name)
        return HttpResponse(f"Group '{group_name}' created successfully.")

@method_decorator(csrf_exempt, name='dispatch')
class SlideView(View):
   
    def get(self, request, *args, **kwargs):
        slides = list(Slide.objects.values('id', 'name', 'content', 'updated_at', 'created_at'))
        return JsonResponse(slides, safe=False)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        name = data.get('name')
        content = data.get('content', '')

        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        slide = Slide(name=name, content=content)
        try:
            slide.full_clean()   # runs validate_single_slide + field checks
            slide.save()
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict}, status=400)

        return JsonResponse(
            {'id': slide.id, 'name': slide.name, 'content': slide.content},
            status=201,
        )

@method_decorator(csrf_exempt, name='dispatch')    
class SlideDetailView(View):
            
    def get(self, request, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            return JsonResponse({'id': slide.id, 'name': slide.name, 'content': slide.content})
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found'}, status=404)
        
    def put(self, request, slide_id):
        
        try:
            slide = Slide.objects.get(id=slide_id)
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found'}, status=404)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        slide.name = data.get('name', slide.name)
        slide.content = data.get('content', slide.content)
        slide.updated_at = timezone.now()
        try:
            slide.full_clean()
            slide.save()
            return JsonResponse({'status': 'success'})
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict}, status=400)
        
    def delete(self, request, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            slide.delete()
            return JsonResponse({'message': 'Slide deleted successfully'})
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found'}, status=404)