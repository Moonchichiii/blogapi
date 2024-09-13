from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from profiles.serializers import ProfileSerializer

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True) 
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'profile_name', 'profile', 'is_staff', 'is_superuser', 'password', 'password2')
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'email']

    def to_representation(self, instance):
        """ Remove password fields when retrieving user data. """
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user != instance:
            data.pop('email', None)
        data.pop('password', None)
        data.pop('password2', None)
        return data

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            profile_name=validated_data['profile_name']
        )
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.profile_name = validated_data.get('profile_name', instance.profile_name)
        instance.save()
        return instance
