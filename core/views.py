from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.utils import timezone
from django.http import JsonResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.forms.models import model_to_dict
from django.db.models import Prefetch
from django.db import transaction
from django.core.exceptions import ValidationError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
 
import json

from dtbackend import settings
from .models import Event, Participant, Settings, Monitor

#import datetime

def index(request):
    return HttpResponse("Hello, welcome to the Decision Theater backend server.")

class health_check(View):
    
    def get(self, request):
        return JsonResponse({
            "status": "online",
            "message": "server is running smoothly",
            "timestamp": timezone.now().isoformat()
        })

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

        event = Event.objects.create(
            name=event_name,
            description=event_description,
            date=event_date,
            n_groups=n_groups,
        )
        return HttpResponse(f"Event '{event_name}' created successfully.")
    
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
            'n_monitor': event.nmonitors(),
            'monitors': list(event.monitors.values('id', 'name'))
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

@method_decorator(csrf_exempt, name='dispatch')
class MonitorView(View):
    
    def get(self, request, event_id):
        try:
            event = Event.objects.get(eventID=event_id)
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)
        
        monitor_data = {
            'event_id': event.eventID,
            'event_name': event.name,
            'monitors': list(event.monitors.values('id', 'name')),
        }
        return JsonResponse(monitor_data)

    def patch(self, request, monitor_id):
        return self._update(request, monitor_id)
         
    def post(self, request, monitor_id):
        try:
            self._update(request, monitor_id)
            
            return JsonResponse({
                "status": "Erfolgreich", 
                "monitor_id": monitor_id
            })
        except Exception as e:
            return JsonResponse({"status": "Fehler", "error": str(e)}, status=400)

    def _update(self, request, monitor_id):
        channel_layer = get_channel_layer()
        group_name = f'monitor_{monitor_id}'
        data = json.loads(request.body)
    
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_monitor_message', 
                'payload': data.get('payload') 
            }
        )
        return JsonResponse({"status": "success", "message": "Monitor updated"})

@method_decorator(csrf_exempt, name='dispatch')
class ParticipantView(View):
    def get(self, request):
        participants_data = list(
            Participant.objects.values("id", "name", "seat", "interactions")
        )
        return JsonResponse({"participants": participants_data})
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        participant_name = data.get("name")
        participant_seat = data.get("seat", None)
        participant_interactions = data.get("interactions", 0)
        participant = Participant.objects.create(name=participant_name, seat=participant_seat, interactions=participant_interactions)
        return HttpResponse(f"Participant '{participant_name}' created successfully.")

@method_decorator(csrf_exempt, name='dispatch')
class ParticipantDetailView(View): 
    
    def put(self, request, participant_id): 
        participant = Participant.objects.get(id=participant_id)
        data = json.loads(request.body)
        participant.name = data.get("name", participant.name)
        participant.seat = data.get("seat", participant.seat)
        participant.interactions = data.get("interactions", participant.interactions)
        participant.save()
        return JsonResponse({"status": "success", "message": "Participant updated"})
    
    def delete(self, request, participant_id):
        participant = Participant.objects.get(id=participant_id)
        participant.delete()
        return JsonResponse({"status": "success", "message": "Participant deleted"})

    def patch(self, request, participant_id):
        data = json.loads(request.body)

        channel_layer = get_channel_layer()
        group_name = f'participant_{participant_id}'
        data = json.loads(request.body)
    
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_participant_message', 
                'payload': data
            }
        )
        return JsonResponse({"status": "success", "message": "Participant updated"})


@method_decorator(csrf_exempt, name='dispatch')
class SettingsView(View):
   
    def get(self, request, *args, **kwargs):
        settings = list(Settings.objects.all())       
        settings_list= [settings[0]] if settings else []
        return JsonResponse({
            'message': 'Settings read successfully.', 
            'settings': model_to_dict(settings_list[0]) if settings_list else None
        })

    def patch(self, request):
        return self._update(request)
        
    def _update(self, request):
        settings = list(Settings.objects.all())       
        settings_list = [settings[0]] if settings else []
        print(settings_list) 

        if settings_list:
            try:
                data = json.loads(request.body)
                setting_item = settings_list[0]
                setting_item.cs_url = data.get('cs_url', setting_item.cs_url)
                setting_item.number_of_screens = data.get('number_of_screens', setting_item.number_of_screens)
                setting_item.background_image = data.get('background_image', setting_item.background_image)
                setting_item.language = data.get('language', setting_item.language)
                setting_item.save()
                return JsonResponse({
                    'message': 'Settings updated successfully.', 
                    'settings': model_to_dict(setting_item)
                })
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            new_settings = Settings.objects.create(
                cs_url = data.get('cs_url', 'http://default-content-server.com'),
                number_of_screens = data.get('number_of_screens', 4),
                background_image = data.get('background_image', ''),
                language = data.get('language', 'en')
            )
            return JsonResponse({
                'message': 'Settings created successfully.', 
                'settings': model_to_dict(new_settings)
            })

@method_decorator(csrf_exempt, name='dispatch')
class ModeratorView(View): 

    def patch(self, request):
        data = json.loads(request.body)

        channel_layer = get_channel_layer()
        group_name = f'moderator'
        data = json.loads(request.body)
    
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_moderator_message', 
                'payload': data
            }
        )
        return JsonResponse({"status": "success", "message": "Moderator updated"})
