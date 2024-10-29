from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import CustomUser
from profiles.serializers import ProfileSerializer

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

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
    """Serializer for user registration."""

    email = serializers.EmailField(
        required=True, 
        validators=[UniqueValidator(
            queryset=CustomUser.objects.all(),
            message="A user with this email already exists."
        )]
    )
    profile_name = serializers.CharField(
        required=True, 
        validators=[UniqueValidator(
            queryset=CustomUser.objects.all(),
            message="This profile name is already taken."
        )]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ("email", "profile_name", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            profile_name=validated_data["profile_name"],
            password=validated_data["password"],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ("id", "email", "profile_name", "profile")
        read_only_fields = ("id", "profile_name")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request", None)
        if request and request.user != instance:
            data.pop("email", None)
        return data