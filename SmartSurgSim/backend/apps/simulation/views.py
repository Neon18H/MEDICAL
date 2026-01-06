import json
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.procedures.models import Procedure
from apps.scoring.engine import evaluate_attempt
from .models import Attempt, Event
from .serializers import AttemptSerializer, EventSerializer


def student_dashboard(request):
    return render(request, 'student/dashboard.html')


def simulator_view(request, procedure_id):
    procedure = get_object_or_404(Procedure, id=procedure_id)
    procedure_payload = {
        'id': procedure.id,
        'title': procedure.title,
        'description': procedure.description,
        'difficulty': procedure.difficulty,
        'steps': procedure.steps,
        'rubric': procedure.rubric,
        'zones': procedure.zones,
        'instruments': procedure.instruments,
    }
    return render(request, 'student/simulator.html', {'procedure': json.dumps(procedure_payload)})


def attempt_report(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id)
    events = list(attempt.events.order_by('t_ms').values('t_ms', 'event_type', 'payload'))
    return render(request, 'student/report.html', {'attempt': attempt, 'events': json.dumps(events)})


class AttemptStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        procedure_id = request.data.get('procedure_id')
        procedure = get_object_or_404(Procedure, id=procedure_id)
        attempt = Attempt.objects.create(user=request.user, procedure=procedure)
        return Response({'attempt_id': attempt.id})


class AttemptEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
        data = request.data
        serializer = EventSerializer(data={
            'attempt': attempt.id,
            't_ms': data.get('t_ms', 0),
            'event_type': data.get('type'),
            'payload': data.get('payload', {}),
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'ok'})


class AttemptFinishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
        attempt.ended_at = timezone.now()
        attempt.duration_ms = int(request.data.get('duration_ms', attempt.duration_ms or 0))
        result = evaluate_attempt(attempt, attempt.procedure)
        attempt.score_total = result['score_total']
        attempt.subscores = result['subscores']
        attempt.feedback = result['feedback']
        attempt.algo_version = result['algo_version']
        attempt.save()
        return Response({'attempt_id': attempt.id, 'result': result})


class AttemptListView(generics.ListAPIView):
    serializer_class = AttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user).order_by('-started_at')


class AttemptDetailView(generics.RetrieveAPIView):
    serializer_class = AttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user)
