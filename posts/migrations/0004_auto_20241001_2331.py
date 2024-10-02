from django.db import migrations
from django.utils.text import slugify
import itertools

def generate_unique_slugs(apps, schema_editor):
    Post = apps.get_model('posts', 'Post')
    for post in Post.objects.all():
        if not post.slug:  # If slug is empty, generate one
            base_slug = slugify(post.title)
            slug = base_slug
            for i in itertools.count(1):
                if not Post.objects.filter(slug=slug).exists():
                    break
                slug = f"{base_slug}-{i}"
            post.slug = slug
            post.save()

class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0003_alter_post_options_post_slug_and_more'),
    ]
    operations = [
        migrations.RunPython(generate_unique_slugs),
    ]
