# Generated by Django 5.0.6 on 2024-09-26 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='average_rating',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='total_ratings',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
