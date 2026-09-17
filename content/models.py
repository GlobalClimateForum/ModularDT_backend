from django.db import models

# Content models: the hierarchical content system of the application.
# Structure:
# Presentation, LivePresentation > SceneInPresentationPosition > Scene
#   > SlideInScenePosition > Slide > SlideSection > ParameterSet > Parameter
#
# NOTE: every cross-model relation uses a STRING reference ('Scene', 'Slide', ...)
# so definition order in this file doesn't matter and there are no import-time
# NameErrors. Each model pins db_table to its existing 'core_*' table so the
# physical tables are untouched when these models are moved.


# -- 1. Presentation --

class Presentation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    scenes = models.ManyToManyField(
        'Scene',
        through='SceneInPresentationPosition',
        related_name='presentations',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_presentation'

# -- 2. SceneInPresentationPosition --
# Connects a Scene to a Presentation with an ordering position.

class SceneInPresentationPosition(models.Model):
    scene = models.ForeignKey('Scene', on_delete=models.CASCADE)
    presentation = models.ForeignKey('Presentation', on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        db_table = 'core_sceneinpresentationposition'
        ordering = ['position']

    def __str__(self):
        return f"{self.presentation.name} -> {self.scene.name} on Position {self.position}"


# -- 3. Scene --

class Scene(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slides = models.ManyToManyField(
        'Slide',
        through='SlideInScenePosition',
        related_name='scenes',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.TextField(blank=True)

    class Meta:
        db_table = 'core_scene'

    def __str__(self):
        return self.name

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


# -- 4. SlideInScenePosition --

class SlideInScenePosition(models.Model):
    slide = models.ForeignKey('Slide', on_delete=models.CASCADE)
    scene = models.ForeignKey('Scene', on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        db_table = 'core_slideinsceneposition'
        ordering = ['position']

    def __str__(self):
        return f"{self.scene.name} -> {self.slide.name} on Position {self.position}"


# -- 5. Slide --

class Slide(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    width = models.IntegerField(default=1920)
    height = models.IntegerField(default=1080)
    tags = models.TextField(blank=True)

    class Meta:
        db_table = 'core_slide'

    def __str__(self):
        return f"{self.name} (created at {self.created_at})"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


# -- 6. SlideSection --

class SlideSection(models.Model):

    class SectionType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'
        CHART = 'chart', 'Chart'
        CUSTOM = 'custom', 'Custom'

    class SectionMode(models.TextChoices):
        STATIC = 'static', 'Static'
        URL = 'url', 'URL'
        INTERACTIVE = 'interactive', 'Interactive'

    slide = models.ForeignKey('Slide', related_name='sections', on_delete=models.CASCADE)
    width_fraction = models.FloatField(default=1.0)
    view_type = models.CharField(max_length=20, choices=SectionType.choices, default=SectionType.TEXT)
    content = models.TextField(blank=True)
    content_path = models.CharField(max_length=255, blank=True)
    mode = models.CharField(max_length=20, choices=SectionMode.choices, blank=True)
    url_pattern = models.CharField(max_length=255, blank=True, default='')
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'core_slidesection'


# -- 7. ParameterSet & Parameter --

class ParameterSnapshot(models.Model): 
    section = models.ForeignKey('SlideSection', related_name='parameter_snapshots', on_delete=models.CASCADE)
    parameters = models.ForeignKey('ParameterSet', related_name='snapshots', on_delete=models.CASCADE)
    # creator = models.ForeignKey('Participant', related_name='parameter_snapshots', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ParameterSet(models.Model):
    section = models.ForeignKey('SlideSection', related_name='parameter_sets', on_delete=models.CASCADE)

    class Meta:
        db_table = 'core_parameterset'


class Parameter(models.Model):

    class ParameterType(models.TextChoices):
        STRING = 'string', 'String'
        NUMBER = 'number', 'Number'
        BOOLEAN = 'boolean', 'Boolean'
        SELECT = 'select', 'Select'
        LOCATION = 'location', 'Location'

    parameter_set = models.ForeignKey('ParameterSet', related_name='parameters', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ptype = models.CharField(max_length=20, choices=ParameterType.choices, default=ParameterType.STRING)
    minimum = models.FloatField(null=True, blank=True)
    maximum = models.FloatField(null=True, blank=True)
    default = models.CharField(max_length=255, blank=True)
    options = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_parameter'
        
# -- 8. Maps --
class Layer(models.Model):
    
    class FileType(models.TextChoices):
        GEOJSON = 'geojson', 'GeoJSON'
        GPKG = 'gpkg', 'GPKG'
    
    class VectorType(models.TextChoices):
        POINT = 'point', 'Point'
        LINE = 'line', 'Line'
        POLYGON = 'polygon', 'Polygon'
        UNKNOWN = 'unknown', 'Unknown'
    
    name = models.CharField(max_length=255)
    filetype = models.CharField(max_length=20, choices=FileType.choices)
    file = models.FileField(upload_to='maplayers/')
    marker = models.JSONField(null=True, blank=True)
    path = models.CharField(max_length=255, blank=True) 
    section = models.ForeignKey('SlideSection', related_name='layers', on_delete=models.CASCADE, null=True, blank=True)
    vector_type = models.CharField(choices=VectorType.choices, max_length=20, default=VectorType.UNKNOWN)

# -- 9. Slideshow --

class Slideshow(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slides = models.ManyToManyField(
        'Slide',
        through='SlideInSlideshowPosition',
        related_name='slideshows',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_slideshow'

    def __str__(self):
        return self.name

# -- 10. SlideInSlideshowPosition --

class SlideInSlideshowPosition(models.Model):
    slide = models.ForeignKey('Slide', on_delete=models.CASCADE)
    slideshow = models.ForeignKey('Slideshow', on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        db_table = 'core_slideinslideshowposition'
        ordering = ['position']

    def __str__(self):
        return f"{self.slideshow.name} -> {self.slide.name} on Position {self.position}"

