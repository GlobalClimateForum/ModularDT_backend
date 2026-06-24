from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Format(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
class Event(models.Model):
    eventID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    n_groups = models.IntegerField(default=3)
    monitors = models.ManyToManyField('Monitor', related_name='events')
    scenes = models.ManyToManyField('Scene', through='EventScene', related_name='events')
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
    
    
class Scene(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
    
class Group(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Slide(models.Model):
    
    class Layout(models.TextChoices):
        FULL = 'full', 'Full Screen'
        LEFT = 'half-left', 'Half Left'
        RIGHT = 'half-right', 'Half Right'
    
    name = models.CharField(max_length=255)
    markdown = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    layout = models.CharField(max_length=20, choices=Layout.choices, default=Layout.FULL)
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

class EventScene(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("event", "scene")

    def __str__(self):
        return f"{self.event} -> {self.scene} ({self.order})"
