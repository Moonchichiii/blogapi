from django.db import IntegrityError, transaction
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
        
        

    def validate(self, data):
        """Ensure the passwords match and validate email/profile_name uniqueness."""
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
    
        # Validate email uniqueness
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
    
        # Validate profile_name uniqueness
        if CustomUser.objects.filter(profile_name=data['profile_name']).exists():
            raise serializers.ValidationError({"profile_name": "This profile name is already taken."})
    
        return data


    @transaction.atomic
    def create(self, validated_data):
        """Create a new user with validated data, ensuring uniqueness."""
        try:
            user, created = CustomUser.objects.get_or_create(
                profile_name=validated_data['profile_name'],
                email=validated_data['email'],
                defaults={'password': validated_data['password1']}
            )
            if not created:
                raise ValidationError("A user with this email or profile name already exists.")
        except IntegrityError:
            raise ValidationError("A user with this email or profile name already exists.")
        return user



class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'profile_name', 'profile', 'is_staff']
        extra_kwargs = {'email': {'write_only': True}}
