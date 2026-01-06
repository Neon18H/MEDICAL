from django.core.management.base import BaseCommand
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

        instrument_set = [
            {"name": "Bisturí", "tool": "SCALPEL"},
            {"name": "Pinza", "tool": "FORCEPS"},
            {"name": "Porta-agujas", "tool": "NEEDLE_DRIVER"},
            {"name": "Cauterio", "tool": "CAUTERY"},
        ]

        procedures = [
            {
                "name": "Apendicectomía",
                "specialty": "Cirugía general",
                "difficulty": "Intermedia",
                "procedure_type": "Abierta",
                "duration_estimated_minutes": 45,
                "description": "Resección controlada del apéndice con enfoque didáctico.",
                "steps": [
                    {
                        "id": 1,
                        "title": "Incisión y acceso",
                        "objectives": "Exponer la región apendicular.",
                        "risks": ["Lesión de vasos epigástricos"],
                        "tips": ["Usa plano anatómico correcto."],
                        "instruments": ["SCALPEL"],
                        "actions": ["CUT"],
                    },
                    {
                        "id": 2,
                        "title": "Identificar apéndice",
                        "objectives": "Localizar el apéndice inflamado.",
                        "risks": ["Confundir estructuras vecinas"],
                        "tips": ["Sigue taenia coli."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                    {
                        "id": 3,
                        "title": "Ligadura y resección",
                        "objectives": "Control vascular y resección segura.",
                        "risks": ["Sangrado por ligadura incompleta"],
                        "tips": ["Verifica hemostasia antes de cortar."],
                        "instruments": ["NEEDLE_DRIVER"],
                        "actions": ["SUTURE"],
                    },
                    {
                        "id": 4,
                        "title": "Cierre por planos",
                        "objectives": "Restituir la pared abdominal.",
                        "risks": ["Cierre bajo tensión"],
                        "tips": ["Distribuye puntos equidistantes."],
                        "instruments": ["NEEDLE_DRIVER"],
                        "actions": ["SUTURE"],
                    },
                ],
                "instruments": instrument_set,
                "zones": {
                    "target": {"x": 0.35, "y": 1.15, "z": 0.45, "radius": 0.35},
                    "forbidden": {"x": -0.4, "y": 1.1, "z": 0.15, "radius": 0.3},
                },
                "checklist": [
                    {"code": "STERILE", "label": "Campo estéril"},
                    {"code": "IDENTIFY", "label": "Apéndice identificado"},
                ],
                "rubric": {
                    "version": "rules_v2",
                    "expected_time_seconds": 900,
                    "penalties": {
                        "forbidden_hit": 8,
                        "wrong_action": 5,
                        "step_omitted": 7,
                        "time_over": 1,
                        "wrong_instrument": 4,
                        "erratic_move": 1,
                    },
                },
                "prompt_base": "Guía clínica para apendicectomía educativa.",
                "is_playable": True,
            },
            {
                "name": "Sutura de laceración",
                "specialty": "Trauma/Emergencias",
                "difficulty": "Básica",
                "procedure_type": "Abierta",
                "duration_estimated_minutes": 20,
                "description": "Cierre de laceración con técnica de sutura simple.",
                "steps": [
                    {
                        "id": 1,
                        "title": "Preparación del campo",
                        "objectives": "Asepsia y anestesia local.",
                        "risks": ["Contaminación"],
                        "tips": ["Asegura hemostasia previa."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                    {
                        "id": 2,
                        "title": "Sutura por planos",
                        "objectives": "Alinear bordes y cerrar.",
                        "risks": ["Tensión excesiva"],
                        "tips": ["Mantén nudos seguros."],
                        "instruments": ["NEEDLE_DRIVER"],
                        "actions": ["SUTURE"],
                    },
                ],
                "instruments": instrument_set,
                "zones": {
                    "target": {"x": 0.2, "y": 1.25, "z": 0.4, "radius": 0.3},
                    "forbidden": {"x": -0.35, "y": 1.05, "z": 0.2, "radius": 0.25},
                },
                "checklist": [
                    {"code": "CLEAN", "label": "Herida limpia"},
                    {"code": "ALIGN", "label": "Bordes alineados"},
                ],
                "rubric": {
                    "version": "rules_v2",
                    "expected_time_seconds": 300,
                    "penalties": {
                        "forbidden_hit": 6,
                        "wrong_action": 4,
                        "step_omitted": 6,
                        "time_over": 1,
                        "wrong_instrument": 3,
                        "erratic_move": 1,
                    },
                },
                "prompt_base": "Guía de sutura para laceraciones.",
                "is_playable": True,
            },
            {
                "name": "Incisión y drenaje de absceso",
                "specialty": "Cirugía general",
                "difficulty": "Intermedia",
                "procedure_type": "Abierta",
                "duration_estimated_minutes": 25,
                "description": "Drenaje controlado con irrigación y empaquetamiento.",
                "steps": [
                    {
                        "id": 1,
                        "title": "Desinfección",
                        "objectives": "Reducir carga bacteriana.",
                        "risks": ["Contaminación"],
                        "tips": ["Usa irrigación abundante."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                    {
                        "id": 2,
                        "title": "Incisión",
                        "objectives": "Acceder a cavidad del absceso.",
                        "risks": ["Incisión profunda"],
                        "tips": ["Controla la profundidad."],
                        "instruments": ["SCALPEL"],
                        "actions": ["CUT"],
                    },
                    {
                        "id": 3,
                        "title": "Drenaje e irrigación",
                        "objectives": "Evacuar contenido y limpiar cavidad.",
                        "risks": ["Cierre prematuro"],
                        "tips": ["Irriga hasta limpiar."],
                        "instruments": ["FORCEPS"],
                        "actions": ["IRRIGATE"],
                    },
                ],
                "instruments": instrument_set,
                "zones": {
                    "target": {"x": 0.3, "y": 1.1, "z": 0.4, "radius": 0.32},
                    "forbidden": {"x": -0.3, "y": 1.2, "z": 0.1, "radius": 0.28},
                },
                "checklist": [
                    {"code": "DRAIN", "label": "Drenaje completo"},
                    {"code": "IRRIGATE", "label": "Irrigación final"},
                ],
                "rubric": {
                    "version": "rules_v2",
                    "expected_time_seconds": 360,
                    "penalties": {
                        "forbidden_hit": 6,
                        "wrong_action": 4,
                        "step_omitted": 6,
                        "time_over": 1,
                        "wrong_instrument": 4,
                        "erratic_move": 1,
                    },
                },
                "prompt_base": "Guía para incisión y drenaje.",
                "is_playable": True,
            },
            {
                "name": "Artroscopia: navegación básica",
                "specialty": "Ortopedia",
                "difficulty": "Intermedia",
                "procedure_type": "Endoscópica",
                "duration_estimated_minutes": 30,
                "description": "Orientación artroscópica con navegación controlada.",
                "steps": [
                    {
                        "id": 1,
                        "title": "Ingreso artroscópico",
                        "objectives": "Acceder a la cavidad articular.",
                        "risks": ["Lesión de cartílago"],
                        "tips": ["Mantén ángulo de entrada."],
                        "instruments": ["SCALPEL"],
                        "actions": ["CUT"],
                    },
                    {
                        "id": 2,
                        "title": "Exploración sistemática",
                        "objectives": "Revisar compartimentos.",
                        "risks": ["Desorientación espacial"],
                        "tips": ["Sigue referencias anatómicas."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                ],
                "instruments": instrument_set,
                "zones": {
                    "target": {"x": 0.25, "y": 1.25, "z": 0.35, "radius": 0.3},
                    "forbidden": {"x": -0.3, "y": 1.2, "z": 0.15, "radius": 0.25},
                },
                "checklist": [
                    {"code": "PORTAL", "label": "Portal correcto"},
                    {"code": "VISION", "label": "Visión clara"},
                ],
                "rubric": {
                    "version": "rules_v2",
                    "expected_time_seconds": 420,
                    "penalties": {
                        "forbidden_hit": 7,
                        "wrong_action": 4,
                        "step_omitted": 6,
                        "time_over": 1,
                        "wrong_instrument": 4,
                        "erratic_move": 1,
                    },
                },
                "prompt_base": "Guía artroscópica básica.",
                "is_playable": True,
            },
            {
                "name": "Cesárea simplificada",
                "specialty": "Ginecología",
                "difficulty": "Avanzada",
                "procedure_type": "Abierta",
                "duration_estimated_minutes": 60,
                "description": "Simulación educativa de apertura uterina y extracción fetal.",
                "steps": [
                    {
                        "id": 1,
                        "title": "Incisión uterina",
                        "objectives": "Acceso controlado al útero.",
                        "risks": ["Lesión fetal"],
                        "tips": ["Controla profundidad del corte."],
                        "instruments": ["SCALPEL"],
                        "actions": ["CUT"],
                    },
                    {
                        "id": 2,
                        "title": "Extracción y hemostasia",
                        "objectives": "Extracción segura y control de sangrado.",
                        "risks": ["Hemorragia"],
                        "tips": ["Coordina con el equipo."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                    {
                        "id": 3,
                        "title": "Cierre uterino",
                        "objectives": "Cerrar por planos.",
                        "risks": ["Cierre insuficiente"],
                        "tips": ["Verifica sutura continua."],
                        "instruments": ["NEEDLE_DRIVER"],
                        "actions": ["SUTURE"],
                    },
                ],
                "instruments": instrument_set,
                "zones": {
                    "target": {"x": 0.35, "y": 1.05, "z": 0.3, "radius": 0.33},
                    "forbidden": {"x": -0.25, "y": 1.2, "z": 0.2, "radius": 0.28},
                },
                "checklist": [
                    {"code": "FETAL", "label": "Extracción segura"},
                    {"code": "HEMOSTASIS", "label": "Hemostasia confirmada"},
                ],
                "rubric": {
                    "version": "rules_v2",
                    "expected_time_seconds": 900,
                    "penalties": {
                        "forbidden_hit": 9,
                        "wrong_action": 5,
                        "step_omitted": 8,
                        "time_over": 1,
                        "wrong_instrument": 5,
                        "erratic_move": 2,
                    },
                },
                "prompt_base": "Guía educativa para cesárea.",
                "is_playable": True,
            },
            {
                "name": "Toracostomía con tubo",
                "specialty": "Trauma/Emergencias",
                "difficulty": "Intermedia",
                "procedure_type": "Abierta",
                "duration_estimated_minutes": 25,
                "description": "Inserción de tubo torácico para drenaje.",
                "steps": [
                    {
                        "id": 1,
                        "title": "Identificar sitio seguro",
                        "objectives": "Localizar espacio intercostal.",
                        "risks": ["Lesión pulmonar"],
                        "tips": ["Palpa referencias óseas."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                    {
                        "id": 2,
                        "title": "Incisión y disección",
                        "objectives": "Crear trayecto seguro.",
                        "risks": ["Sangrado intercostal"],
                        "tips": ["Controla profundidad."],
                        "instruments": ["SCALPEL"],
                        "actions": ["CUT"],
                    },
                    {
                        "id": 3,
                        "title": "Colocación del tubo",
                        "objectives": "Asegurar drenaje.",
                        "risks": ["Posición incorrecta"],
                        "tips": ["Fija el tubo."],
                        "instruments": ["FORCEPS"],
                        "actions": ["GRAB"],
                    },
                ],
                "instruments": instrument_set,
                "zones": {
                    "target": {"x": 0.3, "y": 1.3, "z": 0.35, "radius": 0.3},
                    "forbidden": {"x": -0.35, "y": 1.1, "z": 0.25, "radius": 0.3},
                },
                "checklist": [
                    {"code": "POSITION", "label": "Posición correcta"},
                    {"code": "FIX", "label": "Fijación segura"},
                ],
                "rubric": {
                    "version": "rules_v2",
                    "expected_time_seconds": 420,
                    "penalties": {
                        "forbidden_hit": 8,
                        "wrong_action": 5,
                        "step_omitted": 7,
                        "time_over": 1,
                        "wrong_instrument": 4,
                        "erratic_move": 1,
                    },
                },
                "prompt_base": "Guía de toracostomía.",
                "is_playable": True,
            },
        ]

        template_procedures = [
            ("Hernioplastia inguinal", "Cirugía general"),
            ("Colecistectomía laparoscópica", "Cirugía general"),
            ("Artroplastia de rodilla", "Ortopedia"),
            ("Fijación de fractura de radio", "Ortopedia"),
            ("Histerectomía laparoscópica", "Ginecología"),
            ("Laparoscopia diagnóstica", "Ginecología"),
            ("Craneotomía básica", "Neuro"),
            ("Evacuación de hematoma subdural", "Neuro"),
            ("Resección transuretral (TURP)", "Urología"),
            ("Nefrostomía percutánea", "Urología"),
            ("Esternotomía media", "Cardiotorácica"),
            ("Toracotomía exploratoria", "Cardiotorácica"),
        ]

        for name, specialty in template_procedures:
            procedures.append(
                {
                    "name": name,
                    "specialty": specialty,
                    "difficulty": "Avanzada",
                    "procedure_type": "Plantilla",
                    "duration_estimated_minutes": 60,
                    "description": "Plantilla editable por instructor para completar el flujo clínico.",
                    "steps": [
                        {
                            "id": 1,
                            "title": "Paso preliminar",
                            "objectives": "Definir objetivo quirúrgico.",
                            "risks": ["Riesgo a completar"],
                            "tips": ["Tip a completar"],
                            "instruments": ["SCALPEL"],
                            "actions": ["CUT"],
                        }
                    ],
                    "instruments": instrument_set,
                    "zones": {
                        "target": {"x": 0.3, "y": 1.2, "z": 0.3, "radius": 0.3},
                        "forbidden": {"x": -0.3, "y": 1.1, "z": 0.2, "radius": 0.3},
                    },
                    "checklist": [{"code": "PLACEHOLDER", "label": "Checklist por completar"}],
                    "rubric": {
                        "version": "rules_v2",
                        "expected_time_seconds": 600,
                        "penalties": {
                            "forbidden_hit": 8,
                            "wrong_action": 5,
                            "step_omitted": 7,
                            "time_over": 1,
                            "wrong_instrument": 4,
                            "erratic_move": 1,
                        },
                    },
                    "prompt_base": "Plantilla base para instructores.",
                    "is_playable": False,
                }
            )

        for procedure_data in procedures:
            procedure, created = Procedure.objects.get_or_create(
                name=procedure_data["name"], defaults=procedure_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created procedure {procedure.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Procedure {procedure.name} already exists"))
