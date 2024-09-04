from rest_framework import serializers
from profiles.models import Profile
from accounts.models import CustomUser

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'birth_date']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'profile_name', 'profile', 'is_staff', 'is_superuser']
