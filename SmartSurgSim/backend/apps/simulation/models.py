from django.conf import settings
from django.db import models
from apps.procedures.models import Procedure


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    score_total = models.IntegerField(null=True, blank=True)
    subscores = models.JSONField(default=dict, blank=True)
    feedback = models.TextField(blank=True)
    algo_version = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.procedure.title}"


class Event(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='events')
    t_ms = models.PositiveIntegerField()
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
