from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import CustomUser
from profiles.serializers import ProfileSerializer

from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                # Fetch the user directly
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # If user doesn't exist, raise a generic error
                raise serializers.ValidationError("Invalid email or password.")

            # Check if the password is correct
            if not user.check_password(password):
                raise serializers.ValidationError("Invalid email or password.")

            # Check if the user is active
            if not user.is_active:
                raise serializers.ValidationError("Account is not activated.")

            data['user'] = user
            return data
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer."""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    profile_name = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'profile_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            profile_name=validated_data['profile_name'],
            password=validated_data['password']
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    """CustomUser model serializer."""
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'profile_name', 'profile')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request', None)
        if request and request.user != instance:
            data.pop('email', None)
        return data
