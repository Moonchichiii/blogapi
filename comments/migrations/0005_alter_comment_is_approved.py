# Generated by Django 5.1.2 on 2024-10-15 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0004_alter_comment_is_approved"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="is_approved",
            field=models.BooleanField(default=True),
        ),
    ]
