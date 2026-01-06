from rest_framework import serializers

from .models import Attempt, Event, Procedure


class ProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procedure
        fields = "__all__"


class AttemptSerializer(serializers.ModelSerializer):
    procedure_detail = ProcedureSerializer(source="procedure", read_only=True)

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
            "algorithm_version",
        ]
        read_only_fields = [
            "user",
            "status",
            "started_at",
            "ended_at",
            "score_total",
            "subscores",
            "feedback",
            "algorithm_version",
        ]


class AttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ["id", "procedure"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "attempt", "event_type", "payload", "timestamp_ms", "created_at"]
        read_only_fields = ["created_at"]
