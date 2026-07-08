from django.db import models
from django.contrib.auth.hashers import make_password, check_password

    
class Presentation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    scenes = models.ManyToManyField('Scene', through='SceneInPresentationPosition', related_name='presentations', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Scene(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slides = models.ManyToManyField('Slide', through='SlideInScenePosition', related_name='scenes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    @property
    def tag_list(self): 
        if not self.tags: 
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
class SceneInPresentationPosition(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()  

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.presentation.name} -> {self.scene.name} on Position {self.position}"

class Slide(models.Model):
    
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    width = models.IntegerField(default=1920)
    height = models.IntegerField(default=1080)
    tags = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (created at {self.created_at})"
    
    @property
    def tag_list(self): 
        if not self.tags: 
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

class SlideSection(models.Model):
    
    class SectionType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'
        CHART = 'chart', 'Chart'
    
    slide = models.ForeignKey(Slide, related_name='sections', on_delete=models.CASCADE)
    width_fraction = models.FloatField(default=1.0)
    view_type = models.CharField(max_length=20, choices=SectionType.choices, default=SectionType.TEXT)
    content = models.TextField(blank=True)
    content_path = models.CharField(max_length=255, blank=True)
    mode = models.CharField(max_length=40, blank=True)

class SlideInScenePosition(models.Model):
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()  

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.scene.name} -> {self.slide.name} on Position {self.position}"

class Settings(models.Model):
    cs_url = models.CharField(max_length=255)
    number_of_screens = models.IntegerField(default=4)
    background_image = models.CharField(max_length=255)
    language = models.CharField(max_length=255)

class Event(models.Model):
    eventID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    n_groups = models.IntegerField(default=3)
    monitors = models.ManyToManyField('Monitor', related_name='events')
    moderator_pin = models.CharField(max_length=128,  blank = True, null = True) # hashed pin for moderator access
    
    def nmonitors(self) -> int: 
        return self.monitors.count()
    
    def set_pin(self, raw_pin):
        self.moderator_pin = make_password(raw_pin)
        
    def check_pin(self, raw_pin):
        # If no pin is set, allow access
        if not self.moderator_pin:
            return True
        return check_password(raw_pin, self.moderator_pin)
    
    def reset_pin(self): 
        self.moderator_pin = None
        self.save()
    
    def __str__(self): 
        return self.name
    
class Monitor(models.Model):
    
    class AspectRatio(models.TextChoices):
        RATIO_16_9 = '16:9', '16:9'
        RATIO_4_3 = '4:3', '4:3'
    
    name = models.CharField(max_length=255)
    aspect = models.CharField(max_length=10, choices=AspectRatio.choices, default=AspectRatio.RATIO_16_9)
    
class Group(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Parameter(models.Model): 
    
    class ParameterType(models.TextChoices):
        STRING = 'string', 'String'
        NUMBER = 'number', 'Number'
        BOOLEAN = 'boolean', 'Boolean'
        SELECT = 'select', 'Select'
    
    parameter_set = models.ForeignKey('ParameterSet', related_name='parameters', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ptype = models.CharField(max_length=20, choices=ParameterType.choices, default=ParameterType.STRING) 
    minimum = models.FloatField(null=True, blank=True)
    maximum = models.FloatField(null=True, blank=True)
    default = models.CharField(max_length=255, blank=True)
    
class ParameterSet(models.Model): 
    section = models.ForeignKey(SlideSection, related_name='parameter_sets', on_delete=models.CASCADE)
    