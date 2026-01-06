import csv
import json
from io import StringIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Avg, Count
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsInstructor
from apps.procedures.models import Procedure
from apps.procedures.serializers import ProcedureSerializer
from apps.simulation.models import Attempt, Event


def instructor_dashboard(request):
    return render(request, 'instructor/dashboard.html')


def instructor_procedures(request):
    return render(request, 'instructor/procedures.html')


def instructor_procedure_edit(request, procedure_id):
    procedure = get_object_or_404(Procedure, id=procedure_id)
    procedure_payload = {
        'id': procedure.id,
        'title': procedure.title,
        'description': procedure.description,
        'difficulty': procedure.difficulty,
        'steps': json.dumps(procedure.steps),
        'zones': json.dumps(procedure.zones),
        'rubric': json.dumps(procedure.rubric),
    }
    return render(request, 'instructor/procedure_edit.html', {'procedure': procedure_payload})


def instructor_analytics(request):
    return render(request, 'instructor/analytics.html')


class AdminProcedureView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def post(self, request):
        serializer = ProcedureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        procedure_id = request.data.get('id')
        procedure = get_object_or_404(Procedure, id=procedure_id)
        serializer = ProcedureSerializer(procedure, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        procedure_id = request.data.get('id')
        procedure = get_object_or_404(Procedure, id=procedure_id)
        procedure.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def get(self, request):
        procedure_stats = Attempt.objects.values('procedure__title').annotate(
            avg_score=Avg('score_total'),
            total_attempts=Count('id'),
        )
        error_counts = Event.objects.filter(event_type='error').values('payload').annotate(total=Count('id'))
        return Response({
            'procedure_stats': list(procedure_stats),
            'error_counts': list(error_counts),
        })


class ExportCsvView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def get(self, request):
        procedure_id = request.GET.get('procedure_id')
        attempts = Attempt.objects.all()
        if procedure_id:
            attempts = attempts.filter(procedure_id=procedure_id)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['attempt_id', 'user', 'procedure', 'score_total', 'duration_ms', 'started_at'])
        for attempt in attempts:
            writer.writerow([
                attempt.id,
                attempt.user.username,
                attempt.procedure.title,
                attempt.score_total,
                attempt.duration_ms,
                attempt.started_at,
            ])
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attempts.csv"'
        return response
