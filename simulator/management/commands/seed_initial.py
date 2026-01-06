from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from simulator.models import Procedure


class Command(BaseCommand):
    help = "Seed initial users and procedures"

    def handle(self, *args, **options):
        users_data = [
            {
                "username": "admin",
                "email": "admin@smartsurgsim.local",
                "role": "ADMIN",
                "password": "Admin123!",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "instructor",
                "email": "instructor@smartsurgsim.local",
                "role": "INSTRUCTOR",
                "password": "Instructor123!",
                "is_staff": True,
            },
            {
                "username": "student",
                "email": "student@smartsurgsim.local",
                "role": "STUDENT",
                "password": "Student123!",
            },
        ]

        for user_data in users_data:
            password = user_data.pop("password")
            user, created = User.objects.get_or_create(username=user_data["username"], defaults=user_data)
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user {user.username}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {user.username} already exists"))

        procedures = [
            {
                "name": "Sutura simple",
                "description": "Cierre de tejido con sutura continua simple.",
                "steps": [
                    {"id": 1, "title": "Preparar campo estéril"},
                    {"id": 2, "title": "Alinear bordes"},
                    {"id": 3, "title": "Aplicar sutura"},
                    {"id": 4, "title": "Verificar hemostasia"},
                ],
                "instruments": ["Porta agujas", "Pinzas", "Tijeras"],
                "zones": {
                    "target": {"x": 180, "y": 120, "radius": 60},
                    "forbidden": {"x": 320, "y": 220, "radius": 50},
                },
                "checklist": [
                    {"code": "STERILE", "label": "Campo estéril"},
                    {"code": "ALIGN", "label": "Bordes alineados"},
                ],
                "rubric": {
                    "version": "v1",
                    "expected_time_seconds": 180,
                    "penalties": {"forbidden_hit": 6, "wrong_action": 4, "step_omitted": 5, "time_over": 1},
                },
            },
            {
                "name": "Incisión y drenaje",
                "description": "Apertura controlada y drenaje de absceso superficial.",
                "steps": [
                    {"id": 1, "title": "Desinfectar área"},
                    {"id": 2, "title": "Realizar incisión"},
                    {"id": 3, "title": "Drenar contenido"},
                    {"id": 4, "title": "Irrigar"},
                ],
                "instruments": ["Bisturí", "Pinzas", "Jeringa"],
                "zones": {
                    "target": {"x": 200, "y": 140, "radius": 55},
                    "forbidden": {"x": 340, "y": 200, "radius": 45},
                },
                "checklist": [
                    {"code": "DISINFECT", "label": "Área desinfectada"},
                    {"code": "DRAIN", "label": "Drenaje completo"},
                ],
                "rubric": {
                    "version": "v1",
                    "expected_time_seconds": 210,
                    "penalties": {"forbidden_hit": 6, "wrong_action": 4, "step_omitted": 6, "time_over": 1},
                },
            },
            {
                "name": "Laparoscopia básica",
                "description": "Navegación laparoscópica con control de instrumentos.",
                "steps": [
                    {"id": 1, "title": "Insertar trocar"},
                    {"id": 2, "title": "Explorar cavidad"},
                    {"id": 3, "title": "Identificar estructuras"},
                    {"id": 4, "title": "Retirar instrumental"},
                ],
                "instruments": ["Laparoscopio", "Trocar", "Pinza"],
                "zones": {
                    "target": {"x": 160, "y": 120, "radius": 70},
                    "forbidden": {"x": 300, "y": 240, "radius": 55},
                },
                "checklist": [
                    {"code": "VISUAL", "label": "Visualización adecuada"},
                    {"code": "SAFE_EXIT", "label": "Retiro seguro"},
                ],
                "rubric": {
                    "version": "v1",
                    "expected_time_seconds": 240,
                    "penalties": {"forbidden_hit": 7, "wrong_action": 3, "step_omitted": 6, "time_over": 1},
                },
            },
        ]

        for procedure_data in procedures:
            procedure, created = Procedure.objects.get_or_create(
                name=procedure_data["name"], defaults=procedure_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created procedure {procedure.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Procedure {procedure.name} already exists"))
