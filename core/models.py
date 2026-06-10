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
    n_monitor = models.IntegerField(default=1)
    scenes = models.ManyToManyField('Scene', through='EventScene', related_name='events')
    moderator_pin = models.CharField(max_length=128,  blank = True, null = True) # hashed pin for moderator access
    
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
    name = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (created at {self.created_at})"

class EventScene(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("event", "scene")

    def __str__(self):
        return f"{self.event} -> {self.scene} ({self.order})"
