# Generated by Django 5.0.6 on 2024-09-26 17:34

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0002_remove_comment_is_approved'),
        ('posts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['post', '-created_at'], name='comments_co_post_id_3d4abc_idx'),
        ),
    ]
