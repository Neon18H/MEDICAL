from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from simulator.ai_providers import build_provider

from .models import AISettings
from .serializers import AISettingsSerializer, RegisterSerializer
from .utils import decrypt_api_key


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
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
        serializer = AISettingsSerializer(settings_obj)
        data = serializer.data
        api_key = decrypt_api_key(settings_obj.api_key_encrypted)
        if not api_key:
            return Response({"detail": "API key no configurada."}, status=status.HTTP_400_BAD_REQUEST)
        provider = build_provider(
            data.get("provider", "OPENAI"),
            api_key=api_key,
            model=data.get("model_name", "gpt-4o-mini"),
        )
        try:
            result = provider.generate_guidance(
                {
                    "procedure": "Test de conexión",
                    "step": "Confirmar que el proveedor responde",
                    "context": "Prueba rápida",
                }
            )
        except Exception as exc:  # noqa: BLE001 - feedback controlado
            return Response({"detail": f"Error IA: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "ok", "sample": result})
