# Hand-written state-only migration.
# The 9 content models (Presentation, Scene, Slide, SlideSection,
# SlideInScenePosition, SceneInPresentationPosition, ParameterSet, Parameter,
# LivePresentation) have moved from the `core` app to the `content` app.
#
# content/0001_initial.py already re-declared them in content's state (also
# state-only, no SQL). This migration removes them from core's state so exactly
# one app owns each model. No database_operations run, so the physical core_*
# tables are never touched.
#
# IMPORTANT: update the ('core', '0001_initial') dependency below if core's
# latest migration has a different name.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # core's most recent migration before this one:
        ('core', '0008_remove_participant_identifier_range_and_more'),
        # ensure content re-declares the models before core drops them from state:
        ('content', '0001_initial'),
    ]

    state_operations = [
        # Remove M2M-through fields first (they reference the through models).
        migrations.RemoveField(
            model_name='presentation',
            name='scenes',
        ),
        migrations.RemoveField(
            model_name='scene',
            name='slides',
        ),
        # Then delete the models. Order: dependents before their targets.
        migrations.DeleteModel(name='LivePresentation'),
        migrations.DeleteModel(name='Parameter'),
        migrations.DeleteModel(name='ParameterSet'),
        migrations.DeleteModel(name='SceneInPresentationPosition'),
        migrations.DeleteModel(name='SlideInScenePosition'),
        migrations.DeleteModel(name='SlideSection'),
        migrations.DeleteModel(name='Slide'),
        migrations.DeleteModel(name='Scene'),
        migrations.DeleteModel(name='Presentation'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[],
        ),
    ]