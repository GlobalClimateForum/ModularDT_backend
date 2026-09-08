from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator, MaxValueValidator


class Settings(models.Model):
    cs_url = models.CharField(max_length=255)
    number_of_screens = models.IntegerField(default=4)
    background_image = models.CharField(max_length=255)
    language = models.CharField(max_length=255)
    theme = models.CharField(max_length=50, default='system')  # 'light', 'dark', or 'system'
    palette = models.CharField(max_length=50, default='indigo')  # e.g., 'indigo', 'blue', 'red', etc.

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
    
class Participant(models.Model):
    name = models.CharField(max_length=255)
    seat = models.PositiveSmallIntegerField(
        unique=True,
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    interactions = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.seat} – {self.name}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(seat__gte=1, seat__lte=99),
                name="seat_range",
            )
        ]
    
