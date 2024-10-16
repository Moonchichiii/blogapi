# Generated by Django 5.1.2 on 2024-10-16 17:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Follow",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "followed",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="followers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "follower",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="following",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["follower"], name="followers_f_followe_44883f_idx"
                    ),
                    models.Index(
                        fields=["followed"], name="followers_f_followe_bddd97_idx"
                    ),
                    models.Index(
                        fields=["created_at"], name="followers_f_created_320a17_idx"
                    ),
                ],
                "unique_together": {("follower", "followed")},
            },
        ),
    ]
