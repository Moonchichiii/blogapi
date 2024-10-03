# Generated by Django 5.0.6 on 2024-10-03 10:20

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_remove_post_unique_post_slug_remove_post_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=cloudinary.models.CloudinaryField(blank=True, default='default.webp', max_length=255, null=True, verbose_name='image'),
        ),
    ]
