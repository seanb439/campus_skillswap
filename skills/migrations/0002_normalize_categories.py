from django.db import migrations


def normalize_category_value(value):
    if not value:
        return ''
    return ' '.join(value.split()).title()


def normalize_existing_categories(apps, schema_editor):
    Skill = apps.get_model('skills', 'Skill')

    for skill in Skill.objects.all().only('id', 'category'):
        normalized = normalize_category_value(skill.category)
        if normalized != skill.category:
            skill.category = normalized
            skill.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_existing_categories, migrations.RunPython.noop),
    ]
