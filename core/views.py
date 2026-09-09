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
        
@method_decorator(csrf_exempt, name='dispatch')
class EventView(View):

    def get(self, request):
        events = Event.objects.all()
        event_list = [
            {
                "id": event.eventID,
                "name": event.name,
                "description": event.description,
                "date": event.date
            }
            for event in events
        ]
        return JsonResponse(event_list, safe=False)

    def post(self, request, *args, **kwargs):
       
        data = json.loads(request.body)
        event_name = data.get("name", "Untitled Event")
        event_description = data.get("description", "")
        event_date = data.get("date") or timezone.now()
        
        event_id = data.get("id", None)

        if event_id is not None: 
            self._update(request, event_id)
        else:
            event = Event.objects.create(
                name=event_name,
                description=event_description,
                date=event_date,
            )
        return HttpResponse(f"Event '{event_name}' created successfully.")
    
    def _update(self, request, event_id):
        
        try:
            event = Event.objects.get(eventID=event_id)
       
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)
    
            data = json.loads(request.body)
            event.name = data.get("name", event.name)
            event.description = data.get("description", event.description)
            event.date = data.get("date", event.date)
            event.save()
            return JsonResponse({"status": "success", "message": "Event updated"})
        
        

@method_decorator(csrf_exempt, name='dispatch')
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
        })

@method_decorator(csrf_exempt, name='dispatch')
class Authorize(View): 
    
    def get(self, request, pin):
        valid = self._authorize(pin)
        return JsonResponse({'valid': valid, 'message': 'Pin valid' if valid else 'Invalid pin'})

    def post(self, request): 
        
        data = json.loads(request.body)
        old_pin = data.get('pin')
        new_pin = data.get('new_pin')
        
        valid = (self._authorize(old_pin) and new_pin is not None) or (Settings.objects.first().has_pin() is False and new_pin is not None)
       
        if valid: 
            settings = Settings.objects.first()
            settings.set_pin(new_pin)
            return JsonResponse({'success': True, 'message': 'Pin changed successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid pin or new pin not provided'}, status=400)
    
    def _authorize(self, pin):
        try:
            settings = Settings.objects.first()
        except Settings.DoesNotExist:
            return False

        if not settings.moderator_pin or settings.dev_mode:
            return True

        return settings.check_pin(pin)

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
        obj = Settings.objects.first()

        if obj is None:
            return JsonResponse({'message': 'No settings found.', 'settings': None}, status=404)

        fields = [
            'id', 'cs_url', 'number_of_screens', 'background_image',
            'language', 'theme', 'palette', 'carto_api_key',
            'avatar_style', 'event', 'dev_mode',
        ]
        settings_data = {f: getattr(obj, f) for f in fields}
        settings_data['pin_set'] = obj.has_pin()   # <-- computed, not stored

        return JsonResponse({
            'message': 'Settings read successfully.',
            'settings': settings_data,
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
                setting_item.theme = data.get('theme', setting_item.theme)
                setting_item.palette = data.get('palette', setting_item.palette)
                setting_item.carto_api_key = data.get('carto_api_key', setting_item.carto_api_key)
                setting_item.avatar_style = data.get('avatar_style', setting_item.avatar_style)
                setting_item.dev_mode = data.get('dev_mode', setting_item.dev_mode)
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
                dev_mode = data.get('dev_mode', False),
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
