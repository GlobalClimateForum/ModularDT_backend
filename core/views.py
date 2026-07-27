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

from .models import Event, Participant, Presentation, SceneInPresentationPosition, Slide, Scene, SlideSection, Settings, SlideInScenePosition, LivePresentation, Parameter, ParameterSet
#import datetime

def index(request):
    return HttpResponse("Hello, welcome to the Decision Theater backend server.")

def coerce_default(ptype, raw):
    if raw == '' or raw is None:
        return None
    if ptype == 'number':
        return float(raw)
    if ptype == 'boolean':
        return str(raw).lower() == 'true'
    return raw

def serialize_parameters(pset):
    """Turn a ParameterSet into the name-keyed dict the frontend expects."""
    params = {}
    if pset:
        for p in pset.parameters.all():
            params[p.name] = {
                'type': p.ptype,
                'description': p.description,
                'range': {'min': p.minimum, 'max': p.maximum} if p.ptype == 'number' else None,
                'default': coerce_default(p.ptype, p.default),
                'options': p.options,
            }
    return params

def serialize_section(section):
    """Turn a SlideSection into the dict the frontend expects, including its parameters."""
    pset = section.parameter_sets.first()
    return {
        'id': section.id,
        'view_type': section.view_type,
        'width_fraction': section.width_fraction,
        'content': section.content,
        'content_path': section.content_path,
        'mode': section.mode,
        'url_pattern': section.url_pattern,
        'parameters': serialize_parameters(pset),
        'properties': section.properties
    }
    
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
        participant_name = request.POST.get("name")
        participant = Participant.objects.create(name=participant_name)
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

@method_decorator(csrf_exempt, name='dispatch')
class PresentationView(View): 
    
    def get(self, request):
        # Wir prefetchen die Zwischentabelle (sortiert nach Position) 
        # und holen direkt die A-Objekte samt ihren Sections mit.
        prefetch_through = Prefetch(
            'sceneinpresentationposition_set',  # Django-Standardname für die Rückbeziehung der Zwischentabelle
            queryset=SceneInPresentationPosition.objects.select_related('scene')
        )
        
        presentations = Presentation.objects.prefetch_related(prefetch_through).all()

        presentation_list = []
        for presentation in presentations:
            
            scene_list = []
            for line in presentation.sceneinpresentationposition_set.all():
                scene = line.scene  
                      
                scene_list.append({
                    "id": scene.id,
                    "name": scene.name,
                    "created_at": scene.created_at,
                    "updated_at": scene.updated_at,
                    "tags": scene.tag_list,  
                    "position": line.position 
                })

            presentation_list.append({
                "id": presentation.id,
                "name": presentation.name,
                "description": presentation.description,
                "updated_at": presentation.updated_at,
                "created_at": presentation.created_at,
                "scenes": scene_list 
            })

        return JsonResponse({"presentations": presentation_list}, safe=False)


    def post(self, request, *args, **kwargs):
        try: 
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # expected JSON-Format for "as" im POST-Request:
        # "as": [{"id": 1, "position": 1}, {"id": 2, "position": 3}, {"id": 2, "position": 4}]
        presentation_data_list = data.get("as", [])
        
        presentation = Presentation.objects.create(
            name=data.get('name', 'Untitled Presentation'),
            description=data.get('description', '')
        )

        for item in presentation_data_list:
            scene_id = item.get("id")
            position = item.get("position")
            
            if scene_id is not None and position is not None:
                try:
                    scene = Scene.objects.get(id=scene_id)
                    SceneInPresentationPosition.objects.create(
                        presentation=presentation, 
                        scene=scene, 
                        position=position
                    )
                except Scene.DoesNotExist:
                    return JsonResponse({'error': f'Scene with id {scene_id} does not exist'}, status=400)

        return JsonResponse({"message": f"Presentation '{presentation.name}' created successfully.", "presentation_id": presentation.id})


@method_decorator(csrf_exempt, name='dispatch')    
class PresentationDetailView(View):
            
    def get(self, request, presentation_id):
        try:
            presentation = Presentation.objects.prefetch_related('scenes').get(id=presentation_id)
            
            return JsonResponse({
                'id': presentation.id,
                'name': presentation.name,
                'description': presentation.description,
                'created_at': presentation.created_at,
                'updated_at': presentation.updated_at,
                'scenes': [{
                    'id': scene.id,
                    'name': scene.name,
                    'description': scene.description
                } for scene in presentation.scenes.all()]
            })
        except Presentation.DoesNotExist:
            return JsonResponse({'error': 'Presentation not found', 'status': 'error'}, status=404)

    def patch(self, request, presentation_id):
        return self._update(request, presentation_id)
        
    def put(self, request, presentation_id):
        return self._update(request, presentation_id)

    def _update(self, request, presentation_id):
        try:
            presentation = Presentation.objects.get(id=presentation_id)
        except Presentation.DoesNotExist:
            return JsonResponse({'error': 'Presentation not found', 'status': 'error'}, status=404)

        try:
            # JSON-Daten aus dem Vue-Frontend auslesen
            data = json.loads(request.body)
            scenes_data = data.get('scenes', []) # Erwartet: [{"scene_id": "...", "position": 0}, ...]
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data', 'status': 'error'}, status=400)

        # Transaktionsblock: Schützt die DB, falls eine scene_id ungültig ist
        with transaction.atomic():
            # 1. Alle alten Verknüpfungen für diese Präsentation löschen
            SceneInPresentationPosition.objects.filter(presentation=presentation).delete()

            # 2. Neue Positionen vorbereiten und validieren
            new_positions = []
            for item in scenes_data:
                scene_id = item.get('scene_id')
                position = item.get('position')

                if scene_id is None or position is None:
                    return JsonResponse({'error': 'Missing scene_id or position', 'status': 'error'}, status=400)

                try:
                    scene = Scene.objects.get(id=scene_id)
                    new_positions.append(
                        SceneInPresentationPosition(
                            presentation=presentation,
                            scene=scene,
                            position=position
                        )
                    )
                except Scene.DoesNotExist:
                    # Automatischer Rollback durch transaction.atomic()
                    return JsonResponse({'error': f'Scene with ID {scene_id} not found', 'status': 'error'}, status=400)

            # 3. Bulk-Insert für maximale Performance
            SceneInPresentationPosition.objects.bulk_create(new_positions)

        # 4. Erfolgsantwort: Wir geben direkt das aktualisierte Objekt (wie im GET) zurück
        # Dazu holen wir die Präsentation frisch mit den neuen Verknüpfungen aus der DB
        updated_presentation = Presentation.objects.prefetch_related('scenes').get(id=presentation_id)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Order updated successfully',
            'presentation': {
                'id': updated_presentation.id,
                'name': updated_presentation.name,
                'description': updated_presentation.description,
                'created_at': updated_presentation.created_at,
                'updated_at': updated_presentation.updated_at,
                'scenes': [{
                    'id': scene.id,
                    'name': scene.name,
                    'description': scene.description
                } for scene in updated_presentation.scenes.all()]
            }
        }, status=200)
    
    def delete(self, request, presentation_id):
        try:
            presentation = Presentation.objects.get(id=presentation_id)
            presentation.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'Presentation with ID {presentation_id} deleted successfully.'
            }, status=200) 
            
        except Presentation.DoesNotExist:
            return JsonResponse({
                'error': 'Presentation not found', 
                'status': 'error'
            }, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class LivePresentationView(View):
   
    def get(self, request, *args, **kwargs):
        live_presentation = list(LivePresentation.objects.all())       
        live_presentation_list = [live_presentation[0]] if live_presentation else []
        return JsonResponse({
            'message': 'LivePresentation read successfully.', 
            'live_presentation': model_to_dict(live_presentation_list[0]) if live_presentation_list else None
        })
    

    def patch(self, request):
        return self._update(request)
        
    def _update(self, request):
        live_presentation = LivePresentation.objects.first()

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        presentation_id = data.get('presentation')
        is_active = data.get('active', False)
        current_scene = data.get('current_scene', 1)
            
        channel_layer = get_channel_layer()    
        global_group_name = 'all_monitors'
            
        async_to_sync(channel_layer.group_send)(
            global_group_name,
                {
                    'type': 'send_monitor_message', 
                    'payload': {
                        'event_type': 'presentation_start' if is_active else 'presentation_stop',
                        'presentation_id': presentation_id,
                        'current_scene': current_scene,
                        'active': is_active
                    }
                }
            )

        if live_presentation:
            if 'presentation' in data:
                live_presentation.presentation_id = data.get('presentation')
            
            live_presentation.active = data.get('active', live_presentation.active)
            live_presentation.current_scene = data.get('current_scene', live_presentation.current_scene)
            live_presentation.save()
            
            return JsonResponse({
                'message': 'Live presentation updated successfully.', 
                'settings': model_to_dict(live_presentation)
            })
        else:
            presentation_id = data.get('presentation')
            if not presentation_id:
                return JsonResponse({'error': 'presentation id is required to create'}, status=400)

            new_live_presentation = LivePresentation.objects.create(
                presentation_id=presentation_id,
                active=data.get('active', False), 
                current_scene=data.get('current_scene', 0) 
            )
            return JsonResponse({
                'message': 'LivePresentation created successfully.', 
                'settings': model_to_dict(new_live_presentation)
            })

@method_decorator(csrf_exempt, name='dispatch')
class SceneView(View): 
    
    def get(self, request):
        # Wir prefetchen die Zwischentabelle (sortiert nach Position) 
        # und holen direkt die A-Objekte samt ihren Sections mit.
        prefetch_through = Prefetch(
            'slideinsceneposition_set',
            queryset=SlideInScenePosition.objects.select_related('slide')
                .prefetch_related('slide__sections__parameter_sets__parameters')
        )
        
        scenes = Scene.objects.prefetch_related(prefetch_through).all()

        scene_list = []
        for scene in scenes:
            # Tags splitten
            raw_tags = scene.tags or ''
            tag_list = [t.strip() for t in raw_tags.split(',') if t.strip()]
        
            slide_list = []
            for line in scene.slideinsceneposition_set.all():
                slide = line.slide  # Das eigentliche A-Objekt
            
                # Sections vom verknüpften A-Objekt holen
                section_list = [serialize_section(s) for s in slide.sections.all()]
            
                slide_list.append({
                    "id": slide.id,
                    "name": slide.name,
                    "created_at": slide.created_at,
                    "updated_at": slide.updated_at,
                    "width": slide.width,
                    "height": slide.height,
                    "tags": slide.tag_list,  
                    "sections": section_list,
                    "position": line.position 
                })

            scene_list.append({
                "id": scene.id,
                "name": scene.name,
                "description": scene.description,
                "updated_at": scene.updated_at,
                "created_at": scene.created_at,
                "tags": tag_list,
                "slides": slide_list  
            })

        return JsonResponse({"scenes": scene_list}, safe=False)


    def post(self, request, *args, **kwargs):
        try: 
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # expected JSON-Format for "as" im POST-Request:
        # "as": [{"id": 1, "position": 1}, {"id": 2, "position": 3}, {"id": 2, "position": 4}]
        slide_data_list = data.get("as", [])
        
        scene = Scene.objects.create(
            name=data.get('name', 'Untitled Scene'),
            description=data.get('description', ''),
            tags=', '.join(data.get('tags', []))
        )

        for item in slide_data_list:
            slide_id = item.get("id")
            position = item.get("position")
            
            if slide_id is not None and position is not None:
                try:
                    slide = Slide.objects.get(id=slide_id)
                    SlideInScenePosition.objects.create(
                        scene=scene, 
                        slide=slide, 
                        position=position
                    )
                except Slide.DoesNotExist:
                    return JsonResponse({'error': f'Slide with id {slide_id} does not exist'}, status=400)

        return JsonResponse({"message": f"Scene '{scene.name}' created successfully.", "scene_id": scene.id})


@method_decorator(csrf_exempt, name='dispatch')    
class SceneDetailView(View):
            
    def get(self, request, scene_id):
        try:
            scene = Scene.objects.prefetch_related('slides__sections__parameter_sets__parameters').get(id=scene_id)
        except Scene.DoesNotExist:
            return JsonResponse({'error': 'Scene not found', 'status': 'error'}, status=404)
        
        response_data = {
            'id': scene.id,
            'name': scene.name,
            'created_at': scene.created_at,
            'updated_at': scene.updated_at,
            'tags': scene.tag_list,
            'slides': [{
                'id': slide.id,
                'name': slide.name,
                'created_at': slide.created_at,
                'updated_at': slide.updated_at,
                'width': slide.width,
                'height': slide.height,
                'tags': slide.tag_list,
                'sections': [serialize_section(s) for s in slide.sections.all()],
            } for slide in scene.slides.all()],
        }
        return JsonResponse(response_data)

    def patch(self, request, scene_id):
        return self._update(request, scene_id)
        
    def put(self, request, scene_id):
        return self._update(request, scene_id)

    def _update(self, request, scene_id):
        
        try:
            scene = Scene.objects.get(id=scene_id)
        except Scene.DoesNotExist:
            return JsonResponse({'error': 'Scene not found', 'status': 'error'}, status=404)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status': 'error'}, status=400)
        
        scene.name = data.get('name', scene.name)
        scene.tags = ', '.join(data.get('tags', scene.tag_list))
        scene.updated_at = timezone.now()
        slide_ids = data.get("slides", scene.slides.values_list('id', flat=True))
        scene.slides.set(Slide.objects.filter(id__in=slide_ids))

        try:
            scene.full_clean()
            scene.save()
            return JsonResponse({'status': 'success', 'id': scene.id, 'name': scene.name, 'updated_at': scene.updated_at, 'created_at': scene.created_at, 'tags': scene.tags})
       
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict, 'status': 'error'}, status=400)
        
    def delete(self, request, scene_id):
        try:
            scene = Scene.objects.get(id=scene_id)
            scene.delete()
            return JsonResponse({'message': 'Scene deleted successfully', 'status': 'success'})
        except Scene.DoesNotExist:
            return JsonResponse({'error': 'Scene not found', 'status': 'error'}, status=404)

@method_decorator(csrf_exempt, name='dispatch')        
class SceneTagView(View): 
    
    def get(self, request, tag_name): 
        scenes = Scene.objects.filter(tags__icontains=tag_name)
        
        return JsonResponse([{
            'id': scene.id,
            'name': scene.name,
            'created_at': scene.created_at,
            'updated_at': scene.updated_at,
            'tags': scene.tag_list,
        } for scene in scenes], safe=False)
        
    def post(self, request, tag_name, scene_id):
        try: 
            scene = Scene.objects.get(id=scene_id)
            tags = scene.tag_list
            if tag_name not in tags:
                tags.append(tag_name)
                scene.tags = ', '.join(tags)
            scene.save()
            return JsonResponse({'message': 'Tag added successfully', 'status': 'success'})
        except Scene.DoesNotExist:
            return JsonResponse({'error': 'Scene not found', 'status': 'error'}, status=404)
        
    def delete(self, request, tag_name, scene_id):
        try:
            scene = Scene.objects.get(id=scene_id)
            tags = scene.tag_list
            if tag_name in tags:
                tags.remove(tag_name)
                scene.tags = ', '.join(tags)
            scene.save()
            return JsonResponse({'message': 'Tag removed successfully', 'status': 'success'})
        except Scene.DoesNotExist:
            return JsonResponse({'error': 'Scene not found', 'status': 'error'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class SlideView(View):
   
    def get(self, request, *args, **kwargs):

        slides_queryset = Slide.objects.prefetch_related(
            'sections__parameter_sets__parameters'
        ).all()
        
        result = []
        for slide in slides_queryset: 
            result.append({
                'id': slide.id,
                'name': slide.name,
                'created_at': slide.created_at,
                'updated_at': slide.updated_at,
                'width': slide.width,
                'height': slide.height,
                'tags': slide.tag_list, 
                'sections': [serialize_section(s) for s in slide.sections.all()]
            })
    
        return JsonResponse(result, safe=False)
    
    def post(self, request, *args, **kwargs):

        try:
            
            # TODO: Also creates ParameterSet for sections which dont have any paramers.
            # Maybe thats also usefull in the future?
                
            data = json.loads(request.body)
            sections_data = data.get('sections', [])
            
            # If one db transaction fails, the whole operation is rolled back, ensuring data integrity
            with transaction.atomic():

                # Create a new Slide instance
                slide = Slide.objects.create(
                    name=data.get('name', 'Untitled Slide'),
                    width=data.get('width', 1920),
                    height=data.get('height', 1080),
                    tags=', '.join(data.get('tags', []))
                )

                # Create all section instances in bulk
                section_objects = [
                    SlideSection(
                        slide=slide,
                        view_type=section_data.get('view_type'),
                        content=section_data.get('content'),
                        content_path=section_data.get('content_path'),
                        width_fraction=section_data.get('width_fraction', 1.0),
                        mode=section_data.get('mode', ''),
                        url_pattern=section_data.get('url_pattern', ''),
                        properties=section_data.get('properties', {}),
                    )
                    for section_data in sections_data
                ]
                SlideSection.objects.bulk_create(section_objects)

                # Create ParameterSet instances in bulk
                set_objects = [ ParameterSet(section=section_) for section_ in section_objects ]
                ParameterSet.objects.bulk_create(set_objects)

                # Build parameters
                parameters_bulk = []
                for pset, section_data in zip(set_objects, sections_data):
                    
                    # Get the parameters for the section, if any
                    s_params = section_data.get('parameters', {})
                    
                    # parameter name = key, parameter data = values
                    for p_name, p_data in s_params.items():
                        p_type = p_data.get('type', 'string')  # Get the parameter type - defaults to string
                        p_default = p_data.get('default', None) # Get the default value for the parameter - defaults to None
                        # If the default value is None, we set it to an appropriate default based on the parameter type
                        if p_default is None:
                            p_default = "" if p_type in ['string', 'select'] else False if p_type == 'boolean' else 0

                        # Add the parameter to the bulk list for creation
                        parameters_bulk.append(Parameter(
                            parameter_set=pset,
                            name=p_name,
                            description=p_data.get('description', ''),
                            ptype=p_type,
                            minimum=p_data.get('minimum'),
                            maximum=p_data.get('maximum'),
                            default=p_default,
                            options=p_data.get('options', []),
                        ))

                # Create the parameters in bulk if there are any to create
                if parameters_bulk:
                    Parameter.objects.bulk_create(parameters_bulk)

                return JsonResponse({'message': f'Slide "{slide.name}" created successfully.', 'slide_id': slide.id})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')    
class SlideDetailView(View):
            
    def get(self, request, slide_id):
        try:
            slide = Slide.objects.prefetch_related(
                'sections__parameter_sets__parameters'
            ).get(id=slide_id)
            response_data = {
                'id': slide.id,
                'name': slide.name,
                'created_at': slide.created_at,
                'updated_at': slide.updated_at,
                'tags': slide.tag_list,
                'width': slide.width,
                'height': slide.height,
                'sections': [serialize_section(s) for s in slide.sections.all()],
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
        slide.tags = ', '.join(data.get('tags', slide.tag_list))
        slide.updated_at = timezone.now()
        
        try:
            slide.full_clean()
            slide.save()
            return JsonResponse({'status': 'success', 'id': slide.id, 'name': slide.name, 
                                 'updated_at': slide.updated_at, 'created_at': slide.created_at, 'tags': slide.tags})
       
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict, 'status': 'error'}, status=400)
        
    def delete(self, request, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            slide.delete()
            return JsonResponse({'message': 'Slide deleted successfully', 'status': 'success'})
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found', 'status': 'error'}, status=404)
        
@method_decorator(csrf_exempt, name='dispatch')
class SlideSectionView(View):
    
    def get(self, request, slide_id):
        try:
            sections = SlideSection.objects.filter(slide_id=slide_id) \
                .prefetch_related('parameter_sets__parameters')
            sections_data = [serialize_section(s) for s in sections]
            return JsonResponse(sections_data, safe=False)
        
        except SlideSection.DoesNotExist:
            return JsonResponse({'error': 'Slide sections not found for the provided Slide ID', 'status': 'error'}, status=404)
    
    def post(self, request, slide_id):
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status': 'error'}, status=400)

        try:
            slide = Slide.objects.get(id=slide_id)
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found', 'status': 'error'}, status=404)

        section = SlideSection.objects.create(
            slide=slide,
            view_type=data.get('view_type'),
            content=data.get('content', ''),
            content_path=data.get('content_path', ''),
            width_fraction=data.get('width_fraction', 1.0),
            mode=data.get('mode', ''),
            url_pattern=data.get('url_pattern', ''),
            properties=section_data.get('properties', {}),
        )

        return JsonResponse({
            'message': 'Slide section created successfully',
            'status': 'success',
            'section_id': section.id,
        })
        
@method_decorator(csrf_exempt, name='dispatch')        
class SlideTagView(View): 
    
    def get(self, request, tag_name): 
        slides = Slide.objects.filter(tags__icontains=tag_name)
        
        return JsonResponse([{
            'id': slide.id,
            'name': slide.name,
            'created_at': slide.created_at,
            'updated_at': slide.updated_at,
            'tags': slide.tag_list,
        } for slide in slides], safe=False)
        
    def post(self, request, tag_name, slide_id):
        try: 
            slide = Slide.objects.get(id=slide_id)
            tags = slide.tag_list
            if tag_name not in tags:
                tags.append(tag_name)
                slide.tags = ', '.join(tags)
            slide.save()
            return JsonResponse({'message': 'Tag added successfully', 'status': 'success'})
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found', 'status': 'error'}, status=404)
        
    def delete(self, request, tag_name, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            tags = slide.tag_list
            if tag_name in tags:
                tags.remove(tag_name)
                slide.tags = ', '.join(tags)
            slide.save()
            return JsonResponse({'message': 'Tag removed successfully', 'status': 'success'})
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
class ParameterSetView(View):
    
    def get(self, request, section_id):
        try:
            parameter_set = ParameterSet.objects.prefetch_related('parameters').get(section_id=section_id)
        except ParameterSet.DoesNotExist:
            return JsonResponse({'error': 'ParameterSet not found for the provided Section ID', 'status': 'error'}, status=404)

        return JsonResponse({
            'section_id': section_id,
            'parameters': serialize_parameters(parameter_set),
        })
        
class InteractiveSlidesView(View):
    
    def get(self, request):
        interactive_slides = Slide.objects.filter(
            sections__mode='interactive'
        ).distinct().prefetch_related('sections__parameter_sets__parameters')

        return JsonResponse([{
            'id': slide.id,
            'name': slide.name,
            'created_at': slide.created_at,
            'updated_at': slide.updated_at,
            'tags': slide.tag_list,
            'width': slide.width,
            'height': slide.height,
            'sections': [serialize_section(s) for s in slide.sections.all()],
        } for slide in interactive_slides], safe=False)

class InteractivePanelsView(View): 
    
    def get(self, request):
        
        interactive_panels = Slide.objects.filter(
            sections__view_type ='ipanel'
        ).distinct().prefetch_related('sections__parameter_sets__parameters')
        
        return JsonResponse([{
            'id': slide.id,
            'name': slide.name,
            'created_at': slide.created_at,
            'updated_at': slide.updated_at,
            'tags': slide.tag_list,
            'width': slide.width,
            'height': slide.height,
            'sections': [serialize_section(s) for s in slide.sections.all()]
        } for slide in interactive_panels], safe=False)
        
        