from profiles.models import CustomUser
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'address', 'phone_number', 'password1', 'password2']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            address=validated_data['address'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password1']
        )
        return user
