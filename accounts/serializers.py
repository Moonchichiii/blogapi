from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from rest_framework import serializers

from .models import CustomUser
from profiles.serializers import ProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""
    email = serializers.EmailField(required=True)
    profile = ProfileSerializer(read_only=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'profile_name', 'profile', 'is_staff', 'is_superuser', 'password', 'password2'
        )
        read_only_fields = ['id', 'is_staff', 'is_superuser']

    def validate(self, attrs):
        """Ensure password validation when creating or updating."""
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def validate_email(self, value):
        """Validate that the email is unique."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_profile_name(self, value):
        """Validate that the profile name is unique."""
        if CustomUser.objects.filter(profile_name=value).exists():
            raise serializers.ValidationError("This profile name is already taken.")
        return value

    def create(self, validated_data):
        """Create a new CustomUser instance."""
        validated_data.pop('password2', None)
        try:
            user = CustomUser.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                profile_name=validated_data['profile_name']
            )
            return user
        except IntegrityError as e:
            error_message = str(e).lower()
            if 'unique_profile_name' in error_message or \
               'duplicate key value violates unique constraint' in error_message:
                raise serializers.ValidationError(
                    {'profile_name': 'This profile name is already taken.'}
                )
            elif 'unique_email' in error_message:
                raise serializers.ValidationError(
                    {'email': 'A user with that email already exists.'}
                )
            else:
                raise serializers.ValidationError(
                    {'detail': 'An error occurred during registration.'}
                )

    def update(self, instance, validated_data):
        """Update an existing CustomUser instance."""
        password = validated_data.pop('password', None)
        validated_data.pop('password2', None)
        
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        """Remove sensitive fields when retrieving user data."""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user != instance:
            data.pop('email', None)
        data.pop('password', None)
        data.pop('password2', None)
        return data