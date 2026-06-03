from django.db import models

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
    
    def __str__(self): 
        return self.name
    
class Scene(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Slide(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class EventScene(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("event", "scene")

    def __str__(self):
        return f"{self.event} -> {self.scene} ({self.order})"