from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"procedures", views.ProcedureViewSet, basename="procedure")
router.register(r"attempts", views.AttemptViewSet, basename="attempt")
router.register(r"events", views.EventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
    path("analytics/", views.analytics_overview, name="analytics_overview"),
    path("export/csv/", views.export_attempts_csv, name="export_attempts_csv"),
    path("reports/<int:attempt_id>/", views.attempt_report, name="attempt_report"),
]
