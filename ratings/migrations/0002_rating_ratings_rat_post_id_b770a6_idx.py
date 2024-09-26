# Generated by Django 5.0.6 on 2024-09-26 17:34

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
        ('ratings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['post', 'value'], name='ratings_rat_post_id_b770a6_idx'),
        ),
    ]
