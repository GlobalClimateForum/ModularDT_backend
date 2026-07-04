from unittest import result

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

import json

from dtbackend import settings

from .models import Event, Group, Presentation, Slide, Scene, SlideSection, Settings, SlideInScenePosition 
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

        event = Event.objects.create(
            name=event_name,
            description=event_description,
            date=event_date,
            n_groups=n_groups,
        )
        return HttpResponse(f"Event '{event_name}' created successfully.")
    
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
    
    def post(self, request, event_id):
        try:
            event = Event.objects.get(eventID=event_id)
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Event not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        monitor_name = data.get('name')
        aspect_ratio = data.get('aspect', '16:9')

        if not monitor_name:
            return JsonResponse({'error': 'Monitor name is required'}, status=400)

        monitor = event.monitors.create(name=monitor_name, aspect=aspect_ratio)
        return JsonResponse({'message': f'Monitor "{monitor_name}" added to event "{event.name}".', 'monitor_id': monitor.id})
  
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
class SceneView(View): 
    
    def get(self, request):
        # Wir prefetchen die Zwischentabelle (sortiert nach Position) 
        # und holen direkt die A-Objekte samt ihren Sections mit.
        prefetch_through = Prefetch(
            'slideinsceneposition_set',  # Django-Standardname für die Rückbeziehung der Zwischentabelle
            queryset=SlideInScenePosition.objects.select_related('slide').prefetch_related('slide__sections')
        )
        
        scenes = Scene.objects.prefetch_related(prefetch_through).all()

        scene_list = []
        for scene in scenes:
            # Tags splitten wie bisher
            raw_tags = scene.tags or ''
            tag_list = [t.strip() for t in raw_tags.split(',') if t.strip()]
        
            slide_list = []
            for line in scene.slideinsceneposition_set.all():
                slide = line.slide  # Das eigentliche A-Objekt
            
                # Sections vom verknüpften A-Objekt holen
                section_list = list(slide.sections.all().values())
            
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
                    # Exception?
                    pass

        return JsonResponse({"message": f"Scene '{scene.name}' created successfully.", "scene_id": scene.id})


@method_decorator(csrf_exempt, name='dispatch')    
class SceneDetailView(View):
            
    def get(self, request, scene_id):
        try:
            scene = Scene.objects.get(id=scene_id).prefetch_related('slides')
            #sections = list(SlideSection.objects.filter(scene_id=scene['id']))
            response_data = {
                'id': scene.id,
                'name': scene.name,
                'created_at': scene.created_at,
                'updated_at': scene.updated_at,
                'tags': scene.tag_list,
                'slides': list(scene.slides.all())
            }

            return JsonResponse(response_data)
        except Scene.DoesNotExist:
            return JsonResponse({'error': 'Scene not found', 'status': 'error'}, status=404)

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
        # old code: very unperfoment (N+1 queries if N slides)
        #slides = list(Slide.objects.values('id', 'name', 'updated_at', 'created_at', 'width', 'height', 'tags'))
        #for slide in slides:
        #    tags = slide.pop('tags') or ''
        #    slide['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        #    sections = SlideSection.objects.filter(slide_id=slide['id']).values()
        #    slide['sections'] = list(sections)
        
        #return JsonResponse(slides, safe=False)
    
        #Only 2 queries, independent of the number of slides, because of prefetch_related
        slides_queryset = Slide.objects.prefetch_related('sections').all()
    
        result = []
        for slide in slides_queryset:
            # Greift auf die bereits im Cache liegenden Sektionen zu
            sections_data = list(slide.sections.all().values())
        
            result.append({
                'id': slide.id,
                'name': slide.name,
                'updated_at': slide.updated_at,
                'created_at': slide.created_at,
                'width': slide.width,
                'height': slide.height,
                'tags': slide.tag_list,  # Nutzt dein vorhandenes Property!
                'sections': sections_data
            })
        
        return JsonResponse(result, safe=False)

    def post(self, request, *args, **kwargs):
        try:
            
            data = json.loads(request.body)
            sections = data.get('sections', [])
            
            # Create the slide
            slide = Slide.objects.create(
                name=data.get('name', 'Untitled Slide'),
                width=data.get('width', 1920),
                height=data.get('height', 1080),
                tags=', '.join(data.get('tags', []))
            )
            
            # Create sections for the slide
            for section_data in sections:
                SlideSection.objects.create(
                    slide=slide,
                    view_type=section_data.get('view_type'),
                    content=section_data.get('content'),
                    content_path=section_data.get('content_path'),
                    width_fraction=section_data.get('width_fraction', 1.0)
                )
                
            return JsonResponse({'message': f'Slide "{slide.name}" created successfully.', 'slide_id': slide.id})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        print(data)

@method_decorator(csrf_exempt, name='dispatch')    
class SlideDetailView(View):
            
    def get(self, request, slide_id):
        try:
            slide = Slide.objects.get(id=slide_id)
            sections = list(SlideSection.objects.filter(slide_id=slide['id']))
            response_data = {
                'id': slide.id,
                'name': slide.name,
                'created_at': slide.created_at,
                'updated_at': slide.updated_at,
                'tags': slide.tag_list,
                'width': slide.width,
                'height': slide.height,
                'sections': [{'id': section.id, 'width_fraction': section.width_fraction, 'view_type': section.view_type, 'content': section.content, 'content_path': section.content_path} for section in sections]
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
        slide.markdown = data.get('markdown', slide.markdown)
        slide.tags = ', '.join(data.get('tags', slide.tag_list))
        slide.updated_at = timezone.now()
        
        try:
            slide.full_clean()
            slide.save()
            return JsonResponse({'status': 'success', 'id': slide.id, 'name': slide.name, 'markdown': slide.markdown, 
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
            sections = SlideSection.objects.filter(slide_id=slide_id)
            sections_data = [{
                'id': section.id,
                'slide_id': section.id,
                'view_type': section.view_type,
                'content': section.content,
                'content_path': section.content_path, 
                'width_fraction': section.width_fraction
            } for section in sections]
            return JsonResponse(sections_data, safe=False)
        
        except SlideSection.DoesNotExist:
            return JsonResponse({'error': 'Slide sections not found for the provided Slide ID', 'status': 'error'}, status=404)
    
    def post(self, request, slide_id): 
        
        try: 
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status': 'error'}, status=400)
        
        view_type = data.get('view_type')
        content = data.get('content', '')
        content_path = data.get('content_path', '')
        slide = Slide.objects.get(id=slide_id)
        width_fraction = data.get('width_fraction', 1.0)
        
        section = SlideSection.objects.create(
            slide=slide,
            view_type=view_type,
            content=content,
            content_path=content_path,
            width_fraction=width_fraction
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

