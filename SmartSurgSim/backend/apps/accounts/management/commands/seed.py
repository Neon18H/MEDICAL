from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.procedures.models import Procedure


class Command(BaseCommand):
    help = 'Seed initial users and procedures'

    def handle(self, *args, **options):
        User = get_user_model()
        users = [
            {'username': 'admin', 'password': 'Admin123!', 'role': 'ADMIN'},
            {'username': 'instructor', 'password': 'Instructor123!', 'role': 'INSTRUCTOR'},
            {'username': 'student', 'password': 'Student123!', 'role': 'STUDENT'},
        ]
        for user_data in users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User(username=user_data['username'], role=user_data['role'])
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user {user.username}"))

        procedures_seed = [
            {
                'title': 'Sutura simple',
                'description': 'Práctica de sutura en tejido simulado.',
                'difficulty': 'Básico',
                'steps': [
                    {'id': 'step1', 'label': 'Preparar zona', 'action': 'GRAB'},
                    {'id': 'step2', 'label': 'Realizar incisión mínima', 'action': 'CUT'},
                    {'id': 'step3', 'label': 'Suturar bordes', 'action': 'SUTURE'},
                    {'id': 'step4', 'label': 'Liberar instrumento', 'action': 'RELEASE'},
                ],
                'instruments': ['needle', 'forceps'],
                'zones': {
                    'objective': {'shape': 'circle', 'x': 450, 'y': 260, 'radius': 60},
                    'prohibited': {'shape': 'rect', 'x': 200, 'y': 120, 'width': 120, 'height': 80},
                },
                'rubric': {'target_time_ms': 60000, 'max_errors': 3},
            },
            {
                'title': 'Incisión y drenaje',
                'description': 'Simulación de incisión para drenaje controlado.',
                'difficulty': 'Intermedio',
                'steps': [
                    {'id': 'step1', 'label': 'Posicionar instrumento', 'action': 'GRAB'},
                    {'id': 'step2', 'label': 'Incisión principal', 'action': 'CUT'},
                    {'id': 'step3', 'label': 'Liberar tejido', 'action': 'RELEASE'},
                ],
                'instruments': ['scalpel', 'clamp'],
                'zones': {
                    'objective': {'shape': 'rect', 'x': 380, 'y': 200, 'width': 140, 'height': 90},
                    'prohibited': {'shape': 'circle', 'x': 620, 'y': 320, 'radius': 50},
                },
                'rubric': {'target_time_ms': 80000, 'max_errors': 4},
            },
            {
                'title': 'Laparoscopia: navegación básica',
                'description': 'Navegación básica con instrumento laparoscópico.',
                'difficulty': 'Intermedio',
                'steps': [
                    {'id': 'step1', 'label': 'Sujetar instrumento', 'action': 'GRAB'},
                    {'id': 'step2', 'label': 'Navegar zona objetivo', 'action': 'MOVE'},
                    {'id': 'step3', 'label': 'Liberar instrumento', 'action': 'RELEASE'},
                ],
                'instruments': ['laparoscope'],
                'zones': {
                    'objective': {'shape': 'circle', 'x': 300, 'y': 250, 'radius': 50},
                    'prohibited': {'shape': 'rect', 'x': 540, 'y': 180, 'width': 100, 'height': 120},
                },
                'rubric': {'target_time_ms': 90000, 'max_errors': 4},
            },
        ]
        for proc_data in procedures_seed:
            if not Procedure.objects.filter(title=proc_data['title']).exists():
                Procedure.objects.create(**proc_data)
                self.stdout.write(self.style.SUCCESS(f"Created procedure {proc_data['title']}"))
