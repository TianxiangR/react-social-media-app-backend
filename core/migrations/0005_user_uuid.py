# Generated by Django 5.0.1 on 2024-02-06 09:08

import uuid
from django.db import migrations, models

def gen_uuid(apps, schema_editor):
    MyModel = apps.get_model("core", "User")
    for row in MyModel.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=["uuid"])

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_user_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=False),
        ),
    ]
