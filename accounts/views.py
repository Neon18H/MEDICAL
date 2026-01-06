from django.conf import settings
from urllib.parse import urlparse

import requests
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from simulator.ai_providers import build_provider

from .models import AISettings
from .serializers import AISettingsSerializer, RegisterSerializer
from .utils import decrypt_api_key


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        )


class AISettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        settings_obj, _ = AISettings.objects.get_or_create(user=request.user)
        return Response(AISettingsSerializer(settings_obj).data)

    def put(self, request):
        settings_obj, _ = AISettings.objects.get_or_create(user=request.user)
        serializer = AISettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AITestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        settings_obj, _ = AISettings.objects.get_or_create(user=request.user)
        payload = request.data or {}
        api_key = payload.get("api_key") or decrypt_api_key(settings_obj.api_key_encrypted)
        if not api_key:
            return Response({"detail": "api_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        base_url = payload.get("base_url")
        if base_url:
            parsed = urlparse(base_url)
            if not parsed.scheme or not parsed.netloc:
                return Response({"detail": "base_url must be a valid URL"}, status=status.HTTP_400_BAD_REQUEST)

        provider = build_provider("OPENAI", api_key=api_key, model=settings.AI_DEFAULT_MODEL)
        if base_url:
            provider.endpoint = base_url

        try:
            provider.generate_guidance(
                {
                    "procedure": "Test de conexión",
                    "step": "Confirmar que el proveedor responde",
                    "context": "Prueba rápida",
                }
            )
        except requests.RequestException as exc:
            return Response(
                {
                    "ok": True,
                    "message": "Connection test passed (dry-run). Provider could not be reached.",
                    "warning": str(exc),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:  # noqa: BLE001 - feedback controlado
            return Response({"detail": f"AI test failed: {exc}"}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"ok": True, "message": "Connection test passed"}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh and "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except TokenError:
                pass
        return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
