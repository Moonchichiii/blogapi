from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['get_profile_name', 'bio', 'location', 'birth_date']
    search_fields = ['user__profile_name', 'location']

    def get_profile_name(self, obj):
        return obj.user.profile_name
    get_profile_name.short_description = 'Profile Name'