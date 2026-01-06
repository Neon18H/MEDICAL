from rest_framework import serializers

from .models import Attempt, Event, Procedure


class ProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procedure
        fields = "__all__"


class AttemptSerializer(serializers.ModelSerializer):
    procedure_detail = ProcedureSerializer(source="procedure", read_only=True)
    procedure_id = serializers.IntegerField(source="procedure.id", read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id",
            "user",
            "procedure",
            "procedure_detail",
            "status",
            "started_at",
            "ended_at",
            "duration_seconds",
            "score_total",
            "subscores",
            "feedback",
            "score_breakdown",
            "algorithm_version",
            "ai_used",
            "ai_provider",
            "ai_model",
            "ai_feedback",
        ]
        read_only_fields = [
            "user",
            "status",
            "started_at",
            "ended_at",
            "score_total",
            "subscores",
            "feedback",
            "score_breakdown",
            "algorithm_version",
            "ai_used",
            "ai_provider",
            "ai_model",
            "ai_feedback",
        ]


class AttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ["id", "procedure"]


class AttemptStartSerializer(serializers.Serializer):
    procedure_id = serializers.IntegerField(required=False)
    procedure = serializers.PrimaryKeyRelatedField(queryset=Procedure.objects.all(), required=False)

    def validate(self, attrs):
        procedure = attrs.get("procedure")
        procedure_id = attrs.pop("procedure_id", None)
        if not procedure and procedure_id is not None:
            try:
                procedure = Procedure.objects.get(pk=procedure_id)
            except Procedure.DoesNotExist as exc:
                raise serializers.ValidationError({"procedure_id": "Procedimiento inválido."}) from exc
            attrs["procedure"] = procedure
        if not procedure:
            raise serializers.ValidationError({"procedure_id": "procedure_id is required"})
        return attrs


class EventSerializer(serializers.ModelSerializer):
    attempt_id = serializers.PrimaryKeyRelatedField(
        source="attempt", queryset=Attempt.objects.all(), write_only=True, required=False
    )
    t_ms = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Event
        fields = [
            "id",
            "attempt",
            "attempt_id",
            "event_type",
            "payload",
            "timestamp_ms",
            "t_ms",
            "created_at",
        ]
        read_only_fields = ["created_at", "attempt"]

    def validate(self, attrs):
        if "timestamp_ms" not in attrs:
            t_ms = attrs.pop("t_ms", None)
            if t_ms is not None:
                attrs["timestamp_ms"] = t_ms
        return attrs
