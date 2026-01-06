from django.db import models


class Procedure(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=50)
    steps = models.JSONField(default=list)
    rubric = models.JSONField(default=dict)
    zones = models.JSONField(default=dict)
    instruments = models.JSONField(default=list)

    def __str__(self):
        return self.title
