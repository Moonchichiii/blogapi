from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from profiles.serializers import ProfileSerializer
from django.db.utils import IntegrityError

# ------------------------------
# Custom Registration Serializer
# ------------------------------


class CustomRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['profile_name', 'email', 'password1', 'password2']

    def validate(self, data):
        # Check if passwords match
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "The two password fields didn't match."})

        # Ensure the email is unique
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})

        # Ensure the profile_name is unique
        if CustomUser.objects.filter(profile_name=data['profile_name']).exists():
            raise serializers.ValidationError({"profile_name": "This profile name is already taken."})

        return data

    def create(self, validated_data):
        try:
            user = CustomUser(
                email=validated_data['email'],
                profile_name=validated_data['profile_name']
            )
            user.set_password(validated_data['password1'])
            user.save()
            return user
        except IntegrityError:
            raise serializers.ValidationError({"profile_name": "This profile name is already taken."})

# ------------------------------
# User Serializer
# ------------------------------
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'profile_name', 'profile', 'is_staff']
        extra_kwargs = {'email': {'write_only': True}}
