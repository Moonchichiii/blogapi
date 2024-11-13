from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.db import transaction
from .models import CustomUser
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from popularity.models import PopularityMetrics
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class LoginSerializer(serializers.Serializer):
    """User login serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")

            if not user.check_password(password):
                raise serializers.ValidationError("Invalid email or password.")

            if not user.is_active:
                raise serializers.ValidationError("Account is not activated.")

            data["user"] = user
            return data
        raise serializers.ValidationError("Must include 'email' and 'password'.")

class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=CustomUser.objects.all(),
            message="A user with this email already exists."
        )]
    )
    profile_name = serializers.CharField(
        required=True,
        write_only=True,
        validators=[UniqueValidator(
            queryset=Profile.objects.all(),
            message="This profile name is already taken."
        )]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ("email", "profile_name", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        try:
            profile_name = validated_data.pop('profile_name')
            password = validated_data.pop('password')
            validated_data.pop('password2', None)

            user = CustomUser.objects.create_user(
                email=validated_data["email"],
                password=password
            )

            Profile.objects.create(
                user=user,
                profile_name=profile_name,
                bio=""
            )

            return user
        except Exception as e:
            raise serializers.ValidationError({
                "message": "Registration failed",
                "type": "error",
                "details": str(e)
            })

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    profile = ProfileSerializer(read_only=True)
    verification = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ("id", "email", "profile", "verification", "roles")
        read_only_fields = ("id", "roles")
    
    def get_roles(self, obj):
        return obj.roles

    def get_verification(self, user):
        device = TOTPDevice.objects.filter(
            user=user,
            name="default",
            confirmed=True
        ).exists()
        return {
            "is_verified": user.is_active,
            "has_2fa": device
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.user != instance:
            data.pop("email", None)
        return data
