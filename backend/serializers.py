from django.db import IntegrityError
from profiles.models import CustomUser
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['profile_name', 'email', 'password1', 'password2']

    def validate_email(self, value):
        """Ensure email is unique."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_profile_name(self, value):
        """Ensure profile_name is unique."""
        if CustomUser.objects.filter(profile_name=value).exists():
            raise serializers.ValidationError("This profile name is already taken.")
        return value

    def validate(self, data):
        """Ensure that the passwords match."""
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        """Create and return a new user instance."""
        try:
            user = CustomUser.objects.create_user(
                profile_name=validated_data['profile_name'],
                email=validated_data['email'],
                password=validated_data['password1']
            )
        except IntegrityError as e:
            raise ValidationError("A user with this email or profile name already exists.")
        return user



class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'profile_name', 'profile', 'is_staff']
        extra_kwargs = {'email': {'write_only': True}}
