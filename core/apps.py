from django.apps import AppConfig as DjangoAppConfig


class CoreConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
