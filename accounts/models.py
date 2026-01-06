from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)

    def is_instructor(self) -> bool:
        return self.role in {self.Roles.INSTRUCTOR, self.Roles.ADMIN}

    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN


class AISettings(models.Model):
    class Providers(models.TextChoices):
        OPENAI = "OPENAI", "OpenAI"
        GEMINI = "GEMINI", "Gemini"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ai_settings")
    provider = models.CharField(max_length=20, choices=Providers.choices, default=Providers.OPENAI)
    model_name = models.CharField(max_length=120, default="gpt-4o-mini")
    api_key_encrypted = models.TextField(blank=True)
    use_ai = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"AISettings({self.user.username})"
