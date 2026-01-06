from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import AISettings, User
from .utils import encrypt_api_key


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role")

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AISettingsSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_key = serializers.SerializerMethodField()

    class Meta:
        model = AISettings
        fields = ["provider", "model_name", "use_ai", "api_key", "has_key"]

    def get_has_key(self, obj: AISettings) -> bool:
        return bool(obj.api_key_encrypted)

    def update(self, instance: AISettings, validated_data):
        api_key = validated_data.pop("api_key", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if api_key is not None:
            instance.api_key_encrypted = encrypt_api_key(api_key.strip())
        instance.save()
        return instance
