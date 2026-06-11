from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.utils import timezone
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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
        slides = list(Slide.objects.values('id', 'name', 'content', 'updated_at', 'created_at', 'tags'))
        
        for slide in slides:
            tags = slide.pop('tags') or ''
            slide['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
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
            {'id': slide.id, 'name': slide.name, 'content': slide.content, 'tags': slide.tag_list},
            status=201,
        )

@method_decorator(csrf_exempt, name='dispatch')    
class SlideDetailView(View):
            
    def get(self, request, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            response_data = {
                'id': slide.id,
                'name': slide.name,
                'content': slide.content,
                'created_at': slide.created_at,
                'updated_at': slide.updated_at,
                'tags': slide.tag_list,
            }
            return JsonResponse(response_data)
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found', 'status': 'error'}, status=404)

    def patch(self, request, slide_id):
        return self._update(request, slide_id)
        
    def put(self, request, slide_id):
        return self._update(request, slide_id)

    def _update(self, request, slide_id):
        
        try:
            slide = Slide.objects.get(id=slide_id)
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found', 'status': 'error'}, status=404)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status': 'error'}, status=400)
        
        slide.name = data.get('name', slide.name)
        slide.content = data.get('content', slide.content)
        slide.tags = ', '.join(data.get('tags', slide.tag_list))
        slide.updated_at = timezone.now()
        
        try:
            slide.full_clean()
            slide.save()
            return JsonResponse({'status': 'success', 'id': slide.id, 'name': slide.name, 'content': slide.content, 
                                 'updated_at': slide.updated_at, 'created_at': slide.created_at, 'tags': slide.tag_list})
       
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict, 'status': 'error'}, status=400)
        
    def delete(self, request, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            slide.delete()
            return JsonResponse({'message': 'Slide deleted successfully', 'status': 'success'})
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found', 'status': 'error'}, status=404)

class EventDetailView(View):
    
    # Get details of a specific event, including its associated scenes
    def get(self, request, event_id):
        try:
            event = Event.objects.get(eventID=event_id)
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)
        return JsonResponse({
            'id': event.eventID,
            'name': event.name,
            'description': event.description,
            'date': event.date,
            'n_groups': event.n_groups,
            'n_monitor': event.n_monitor,
            'scenes': list(event.scenes.values('id', 'title')),
        })

class EventAuthorize(View): 
    
    def post(self, request, event_id): 
        
        # Check if event exists
        try:
            event = Event.objects.get(eventID=event_id)
        
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)

        # Get the pin from the request and check it against the event's moderator pin
        pin = json.loads(request.body).get('pin', '')
        if not event.moderator_pin:
            return JsonResponse({'valid': True, 'message': 'No pin set'})
        valid = event.check_pin(pin)
        return JsonResponse({'valid': valid, 'message': 'Pin valid' if valid else 'Invalid pin'})