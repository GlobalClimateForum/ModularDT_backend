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
    carto_api_key = models.CharField(max_length=255, blank=True, null=True)  # Optional Carto API key
    avatar_style = models.CharField(max_length=50, default='glyphs')  # e.g., 'glyphs', 'avatars', etc. 
    event = models.ForeignKey('Event', on_delete=models.SET_NULL, null=True, blank=True)  # Optional link to an Event
    dev_mode = models.BooleanField(default=False)  # Development mode toggle
    moderator_pin = models.CharField(max_length=128,  blank = False, null = False) # hashed pin for moderator access
    pin_length = models.PositiveIntegerField(default=4, validators=[MinValueValidator(4), MaxValueValidator(10)])  # Length of the pin
    
    def set_pin(self, raw_pin):
            self.moderator_pin = make_password(raw_pin)
            self.save()
            
    def check_pin(self, raw_pin):
        # If no pin is set, allow access
        if not self.moderator_pin:
            return True
        return check_password(raw_pin, self.moderator_pin)
    
    def has_pin(self):
        return bool(self.moderator_pin)
    
    def reset_pin(self): 
        self.moderator_pin = None
        self.save()
    
class Event(models.Model):
    eventID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    monitors = models.ManyToManyField('Monitor', related_name='events')
    
    def nmonitors(self) -> int: 
        return self.monitors.count()
    
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
    
