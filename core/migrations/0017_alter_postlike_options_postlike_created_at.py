# Generated by Django 4.2.10 on 2024-02-23 21:46

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_post_content_alter_user_location'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='postlike',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='postlike',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
