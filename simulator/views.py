from __future__ import annotations

import csv
from io import BytesIO, StringIO

from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from accounts.models import AISettings
from accounts.utils import decrypt_api_key
from django.conf import settings
from simulator.ai_providers import build_provider
from .models import Attempt, Event, Procedure
from .permissions import IsInstructorOrAdmin
from .scoring import evaluate_attempt
from .serializers import (
    AttemptCreateSerializer,
    AttemptSerializer,
    AttemptStartSerializer,
    EventSerializer,
    ProcedureSerializer,
)


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

    def get_queryset(self):
        queryset = self.queryset
        specialty = self.request.query_params.get("specialty")
        difficulty = self.request.query_params.get("difficulty")
        procedure_type = self.request.query_params.get("type")
        playable = self.request.query_params.get("playable")
        if specialty:
            queryset = queryset.filter(specialty__iexact=specialty)
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)
        if procedure_type:
            queryset = queryset.filter(procedure_type__iexact=procedure_type)
        if playable in {"true", "false"}:
            queryset = queryset.filter(is_playable=(playable == "true"))
        return queryset

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [IsInstructorOrAdmin()]


class AttemptViewSet(viewsets.ModelViewSet):
    queryset = Attempt.objects.select_related("procedure", "user").all()
    serializer_class = AttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

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
        attempt.score_breakdown = result.breakdown
        attempt.feedback = result.feedback
        attempt.algorithm_version = result.algorithm_version

        ai_settings = AISettings.objects.filter(user=attempt.user).first()
        if ai_settings and ai_settings.use_ai and ai_settings.api_key_encrypted:
            api_key = decrypt_api_key(ai_settings.api_key_encrypted)
            if api_key:
                provider = build_provider(ai_settings.provider, api_key=api_key, model=ai_settings.model_name)
                attempt.ai_used = True
                attempt.ai_provider = settings.AI_PROVIDER
                attempt.ai_model = settings.AI_DEFAULT_MODEL
                try:
                    ai_feedback = provider.generate_feedback(
                        {
                            "procedure": attempt.procedure.name,
                            "score": result.total,
                            "subscores": result.subscores,
                            "breakdown": result.breakdown,
                            "duration": attempt.duration_seconds,
                        }
                    )
                    attempt.ai_feedback = ai_feedback
                    attempt.feedback = ai_feedback
                except Exception:
                    attempt.ai_used = False
        attempt.save()
        return Response(
            {
                "attempt_id": attempt.id,
                "score_total": attempt.score_total,
                "subscores": attempt.subscores,
                "feedback": attempt.feedback,
            }
        )

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, pk=None):
        return self.complete(request, pk=pk)

    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        serializer = AttemptStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = Attempt.objects.create(user=request.user, procedure=serializer.validated_data["procedure"])
        data = {
            "attempt_id": attempt.id,
            "status": attempt.status,
            "ws_url": f"/ws/attempts/{attempt.id}/",
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        attempts = (
            Attempt.objects.filter(user=request.user)
            .select_related("procedure")
            .order_by("-started_at")
        )
        return Response(AttemptSerializer(attempts, many=True).data)

    @action(detail=True, methods=["post"], url_path="event")
    def event(self, request, pk=None):
        attempt = self.get_object()
        if request.user.role == "STUDENT" and attempt.user != request.user:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        serializer = EventSerializer(data={**request.data, "attempt_id": attempt.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True}, status=status.HTTP_201_CREATED)


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


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def attempt_start(request):
    serializer = AttemptStartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    attempt = Attempt.objects.create(user=request.user, procedure=serializer.validated_data["procedure"])
    data = {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "ws_url": f"/ws/attempts/{attempt.id}/",
    }
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def attempt_event(request, attempt_id: int):
    attempt = get_object_or_404(Attempt, id=attempt_id)
    if request.user.role == "STUDENT" and attempt.user != request.user:
        return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
    serializer = EventSerializer(data={**request.data, "attempt_id": attempt.id})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"ok": True}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_attempts(request):
    queryset = Attempt.objects.filter(user=request.user).select_related("procedure")
    return Response(AttemptSerializer(queryset, many=True).data)


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
@renderer_classes([JSONRenderer])
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


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def attempt_report_pdf(request, attempt_id: int):
    attempt = get_object_or_404(Attempt.objects.select_related("procedure", "user"), id=attempt_id)
    if request.user.role == "STUDENT" and attempt.user != request.user:
        return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="SmartSurgSim Report")
    styles = {
        "title": ParagraphStyle(name="title", fontSize=18, leading=22, textColor=colors.HexColor("#0F172A")),
        "h2": ParagraphStyle(name="h2", fontSize=12, leading=14, textColor=colors.HexColor("#1E293B")),
        "body": ParagraphStyle(name="body", fontSize=10, leading=12),
    }
    elements = [
        Paragraph("SmartSurgSim – Reporte Clínico Profesional", styles["title"]),
        Spacer(1, 0.2 * inch),
        Paragraph("Centro de Simulación Quirúrgica Inteligente", styles["body"]),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Estudiante: {attempt.user.username}", styles["body"]),
        Paragraph(f"Procedimiento: {attempt.procedure.name}", styles["body"]),
        Paragraph(f"Fecha: {attempt.ended_at or attempt.started_at}", styles["body"]),
        Spacer(1, 0.2 * inch),
        Paragraph("Resumen de desempeño", styles["h2"]),
    ]

    subscores = attempt.subscores or {}
    data = [
        ["Score total", f"{attempt.score_total or 0:.1f}"],
        ["Precisión", subscores.get("precision", 0)],
        ["Eficiencia", subscores.get("efficiency", 0)],
        ["Seguridad", subscores.get("safety", 0)],
        ["Adherencia", subscores.get("protocol_adherence", 0)],
        ["Manejo instrumental", subscores.get("instrument_handling", 0)],
    ]
    table = Table(data, hAlign="LEFT", colWidths=[2.5 * inch, 1.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5F5")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )
    elements.append(table)
    breakdown = attempt.score_breakdown or {}
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Métricas clave", styles["h2"]))
    metrics_table = Table(
        [
            ["Contacto zona prohibida (ms)", breakdown.get("forbidden_contact_ms", 0)],
            ["Acciones intensas", breakdown.get("forceful_actions", 0)],
            ["Movimientos erráticos", breakdown.get("erratic_moves", 0)],
        ],
        hAlign="LEFT",
        colWidths=[2.5 * inch, 1.5 * inch],
    )
    metrics_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5F5")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ]
        )
    )
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Hallazgos principales", styles["h2"]))
    feedback = attempt.feedback or []
    feedback_text = "<br/>".join([f"• {item}" for item in feedback]) or "Sin observaciones críticas."
    elements.append(Paragraph(feedback_text, styles["body"]))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("Recomendaciones", styles["h2"]))
    elements.append(
        Paragraph(
            "Refuerza la técnica con práctica deliberada, priorizando seguridad y secuencia clínica.",
            styles["body"],
        )
    )
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Firma instructor: ____________________", styles["body"]))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=report_attempt_{attempt.id}.pdf"
    return response


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def ai_guidance(request):
    procedure = request.data.get("procedure", {})
    step = request.data.get("step", {})
    context = request.data.get("context", {})
    ai_settings = AISettings.objects.filter(user=request.user).first()
    if not ai_settings or not ai_settings.use_ai or not ai_settings.api_key_encrypted:
        return Response(
            {
                "next_step_suggestion": step.get("title", "Continúa con el paso actual."),
                "risk_warnings": step.get("risks", []),
                "checklist": step.get("tips", []),
                "source": "static",
            }
        )
    api_key = decrypt_api_key(ai_settings.api_key_encrypted)
    provider = build_provider(ai_settings.provider, api_key=api_key, model=ai_settings.model_name)
    try:
        guidance = provider.generate_guidance(
            {
                "procedure": procedure.get("name"),
                "step": step.get("title"),
                "objectives": step.get("objectives"),
                "risks": step.get("risks"),
                "tips": step.get("tips"),
                "context": context,
            }
        )
    except Exception:
        guidance = {
            "next_step_suggestion": step.get("title", "Continúa con el paso actual."),
            "risk_warnings": step.get("risks", []),
            "checklist": step.get("tips", []),
        }
    guidance["source"] = "ai"
    return Response(guidance)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def ai_chat(request):
    question = request.data.get("question", "")
    context = request.data.get("context", {})
    ai_settings = AISettings.objects.filter(user=request.user).first()
    if not ai_settings or not ai_settings.use_ai or not ai_settings.api_key_encrypted:
        return Response({"answer": "IA desactivada. Consulta las recomendaciones del protocolo."})
    api_key = decrypt_api_key(ai_settings.api_key_encrypted)
    provider = build_provider(ai_settings.provider, api_key=api_key, model=ai_settings.model_name)
    try:
        guidance = provider.generate_guidance({"question": question, "context": context})
        answer = guidance.get("next_step_suggestion", "Continúa con el protocolo.")
    except Exception:
        answer = "No fue posible obtener respuesta IA en este momento."
    return Response({"answer": answer, "source": "ai"})
