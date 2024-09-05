from rest_framework import serializers
from profiles.models import Profile
from accounts.models import CustomUser

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'birth_date']
        read_only_fields = ['user']  # We shouldn't allow users to change the associated user

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'profile_name', 'profile', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'is_staff', 'is_superuser']

    def update(self, instance, validated_data):
        # Handle profile updates within the user serializer
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            profile_serializer = ProfileSerializer(instance.profile, data=profile_data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()

        # Handle user fields like 'profile_name'
        instance.profile_name = validated_data.get('profile_name', instance.profile_name)
        instance.save()
        return instance
