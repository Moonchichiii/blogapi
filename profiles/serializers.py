from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from accounts.models import CustomUser
from profiles.models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'birth_date']
        read_only_fields = ['user']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'profile_name', 'password', 'password2', 'profile', 'is_staff', 'is_superuser')
        read_only_fields = ['id', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'email': {'required': True},
            'profile_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        profile_data = validated_data.pop('profile', {})
        user = CustomUser.objects.create_user(**validated_data)
        Profile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            profile_serializer = ProfileSerializer(instance.profile, data=profile_data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()

        instance.profile_name = validated_data.get('profile_name', instance.profile_name)
        instance.save()
        return instance