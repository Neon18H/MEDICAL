from rest_framework import serializers
from .models import Attempt, Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class AttemptSerializer(serializers.ModelSerializer):
    procedure_title = serializers.CharField(source='procedure.title', read_only=True)
    events = EventSerializer(many=True, read_only=True)

    class Meta:
        model = Attempt
        fields = [
            'id',
            'user',
            'procedure',
            'procedure_title',
            'started_at',
            'ended_at',
            'duration_ms',
            'score_total',
            'subscores',
            'feedback',
            'algo_version',
            'events',
        ]
