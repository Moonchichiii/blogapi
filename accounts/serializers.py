from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from django.db.utils import IntegrityError
from rest_framework.validators import UniqueValidator

class CustomRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message="This email is already registered.")]
    )
    
    # Allow profile data during registration
    profile = ProfileSerializer(required=False)

    profile_name = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message="This profile name is already taken.")]
    )
    
    password1 = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['profile_name', 'email', 'password1', 'password2', 'profile']

    def validate(self, data):        
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "The two password fields didn't match."})
        return data

    def create(self, validated_data):
        try:
            # Extract profile data if provided
            profile_data = validated_data.pop('profile', None)

            # Create the user
            user = CustomUser(
                email=validated_data['email'],
                profile_name=validated_data['profile_name']
            )
            user.set_password(validated_data['password1'])
            user.save()

            # Create the profile if profile data is provided, otherwise create an empty profile
            if profile_data:
                Profile.objects.create(user=user, **profile_data)
            else:
                Profile.objects.create(user=user)

            return user
        except IntegrityError:
            raise serializers.ValidationError({"profile_name": "This profile name is already taken."})

# ------------------------------
# User Serializer (for listing users)
# ------------------------------
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'profile_name', 'profile', 'is_staff']
        extra_kwargs = {'email': {'write_only': True}}
