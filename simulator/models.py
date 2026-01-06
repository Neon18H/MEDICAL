from django.conf import settings
from django.db import models


class Procedure(models.Model):
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=120, default="General")
    difficulty = models.CharField(max_length=50, default="Intermedia")
    procedure_type = models.CharField(max_length=50, default="Abierta")
    duration_estimated_minutes = models.IntegerField(default=30)
    description = models.TextField()
    steps = models.JSONField(default=list)
    instruments = models.JSONField(default=list)
    zones = models.JSONField(default=dict)
    checklist = models.JSONField(default=list)
    rubric = models.JSONField(default=dict)
    prompt_base = models.TextField(blank=True)
    is_playable = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    score_total = models.FloatField(null=True, blank=True)
    subscores = models.JSONField(default=dict, blank=True)
    feedback = models.JSONField(default=list, blank=True)
    score_breakdown = models.JSONField(default=dict, blank=True)
    algorithm_version = models.CharField(max_length=20, default="v1")
    ai_used = models.BooleanField(default=False)
    ai_provider = models.CharField(max_length=50, blank=True)
    ai_model = models.CharField(max_length=120, blank=True)
    ai_feedback = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return f"Attempt {self.id} - {self.user}"


class Event(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    timestamp_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.timestamp_ms}"
