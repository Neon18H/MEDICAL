from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)

    def is_instructor(self):
        return self.role in {self.Roles.INSTRUCTOR, self.Roles.ADMIN}

    def is_admin(self):
        return self.role == self.Roles.ADMIN
