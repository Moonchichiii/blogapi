from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db.models import Q
from rest_framework import serializers
import re
from .models import CustomUser
from profiles.serializers import ProfileSerializer
from .messages import STANDARD_MESSAGES

class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""
    
    email = serializers.EmailField(required=True, max_length=254)
    profile = ProfileSerializer(read_only=True)
    profile_name = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    posts_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'profile_name', 'profile', 'is_staff', 'is_superuser',
            'posts_count', 'comments_count', 'ratings_count', 'followers_count', 'following_count',
        )

    def get_posts_count(self, obj):
        return obj.posts.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_ratings_count(self, obj):
        return obj.ratings.count()

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def validate(self, attrs):
        """Ensure password validation when creating or updating."""
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def validate_email(self, value):
        """Validate that the email is unique."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        return value

    def validate_profile_name(self, value):
        """Validate that the profile name is unique and contains only alphanumeric characters and underscores."""
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError({"profile_name": "Profile name can only contain letters, numbers, and underscores."})
        if CustomUser.objects.filter(Q(profile_name__iexact=value)).exists():
            raise serializers.ValidationError({"profile_name": "A user with this profile name already exists."})
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
            if 'unique_profile_name' in error_message or 'duplicate key value violates unique constraint' in error_message:
                raise serializers.ValidationError({'profile_name': "Profile name already exists."})
            elif 'unique_email' in error_message:
                raise serializers.ValidationError({'email': "A user with this email already exists."})
            else:
                raise serializers.ValidationError({'detail': "An error occurred while creating the user."})

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
