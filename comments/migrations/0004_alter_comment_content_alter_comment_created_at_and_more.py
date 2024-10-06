# Generated by Django 5.0.6 on 2024-10-04 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0003_comment_comments_co_post_id_3d4abc_idx'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(help_text='Content of the comment.'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, help_text='Time when the comment was created.'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Time when the comment was last updated.'),
        ),
    ]