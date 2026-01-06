from django.contrib import admin

from .models import Attempt, Event, Procedure


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "procedure", "status", "score_total")
    list_filter = ("status",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("attempt", "event_type", "timestamp_ms")
