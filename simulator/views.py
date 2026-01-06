from __future__ import annotations

import csv
from datetime import timedelta
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Attempt, Event, Procedure
from .permissions import IsInstructorOrAdmin
from .scoring import evaluate_attempt
from .serializers import AttemptCreateSerializer, AttemptSerializer, EventSerializer, ProcedureSerializer


# ---- Template Views ----

def landing(request):
    return render(request, "landing.html")


def dashboard(request):
    return render(request, "dashboard.html")


def simulator_view(request, procedure_id: int):
    return render(request, "simulator.html", {"procedure_id": procedure_id})


def report_view(request, attempt_id: int):
    return render(request, "report.html", {"attempt_id": attempt_id})


def instructor_panel(request):
    return render(request, "instructor.html")


def admin_panel(request):
    return render(request, "admin_panel.html")


# ---- API Views ----


class ProcedureViewSet(viewsets.ModelViewSet):
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [IsInstructorOrAdmin()]


class AttemptViewSet(viewsets.ModelViewSet):
    queryset = Attempt.objects.select_related("procedure", "user").all()
    serializer_class = AttemptSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"INSTRUCTOR", "ADMIN"}:
            return self.queryset
        return self.queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return AttemptCreateSerializer
        return AttemptSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        attempt = self.get_object()
        if attempt.status == Attempt.Status.COMPLETED:
            return Response({"detail": "Attempt already completed."}, status=status.HTTP_400_BAD_REQUEST)

        duration_seconds = int(request.data.get("duration_seconds", 0))
        attempt.duration_seconds = max(duration_seconds, 0)
        attempt.ended_at = timezone.now()
        attempt.status = Attempt.Status.COMPLETED

        result = evaluate_attempt(attempt)
        attempt.score_total = result.total
        attempt.subscores = result.subscores
        attempt.feedback = result.feedback
        attempt.algorithm_version = result.algorithm_version
        attempt.save()
        return Response(AttemptSerializer(attempt).data)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related("attempt").all()
    serializer_class = EventSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"INSTRUCTOR", "ADMIN"}:
            return self.queryset
        return self.queryset.filter(attempt__user=user)

    def perform_create(self, serializer):
        attempt = serializer.validated_data["attempt"]
        user = self.request.user
        if user.role == "STUDENT" and attempt.user != user:
            raise permissions.PermissionDenied("No puedes registrar eventos de otro usuario.")
        serializer.save()


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def analytics_overview(request):
    if request.user.role not in {"INSTRUCTOR", "ADMIN"}:
        return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
    summary = (
        Attempt.objects.filter(status=Attempt.Status.COMPLETED)
        .values("procedure__name")
        .annotate(avg_score=Avg("score_total"))
    )
    return Response(list(summary))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def export_attempts_csv(request):
    if request.user.role not in {"INSTRUCTOR", "ADMIN"}:
        return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Attempt", "Student", "Procedure", "Score", "Duration (s)"])
    for attempt in Attempt.objects.select_related("user", "procedure").all():
        writer.writerow(
            [
                attempt.id,
                attempt.user.username,
                attempt.procedure.name,
                attempt.score_total or 0,
                attempt.duration_seconds,
            ]
        )

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=attempts.csv"
    return response


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def attempt_report(request, attempt_id: int):
    attempt = get_object_or_404(Attempt.objects.select_related("procedure"), id=attempt_id)
    if request.user.role == "STUDENT" and attempt.user != request.user:
        return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

    events = EventSerializer(attempt.events.all(), many=True).data
    return Response(
        {
            "attempt": AttemptSerializer(attempt).data,
            "events": events,
        }
    )
