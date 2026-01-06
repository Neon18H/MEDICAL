from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AISettings, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "model_name", "use_ai")
    list_filter = ("provider", "use_ai")
