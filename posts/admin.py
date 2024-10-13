from django.contrib import admin
from .models import Post

from django.contrib.admin import ShowFacets

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    show_facets = ShowFacets.ALWAYS