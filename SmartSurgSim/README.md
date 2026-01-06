# SmartSurgSim

Simulador Quirúrgico Inteligente (MVP web) con evaluación automática basada en reglas y analítica.

## Setup local (sin Docker)

```bash
cd SmartSurgSim/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver
```

## Credenciales seed

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| ADMIN | admin | Admin123! |
| INSTRUCTOR | instructor | Instructor123! |
| STUDENT | student | Student123! |

## URLs principales

- Landing/Login: http://127.0.0.1:8000/
- Student dashboard: http://127.0.0.1:8000/app/student/dashboard
- Simulación: http://127.0.0.1:8000/app/student/procedures/<id>/simulate
- Reporte de intento: http://127.0.0.1:8000/app/student/attempts/<id>
- Instructor dashboard: http://127.0.0.1:8000/app/instructor/dashboard
- Instructor procedimientos: http://127.0.0.1:8000/app/instructor/procedures
- Instructor analítica: http://127.0.0.1:8000/app/instructor/analytics

## Endpoints API (DRF)

- POST `/api/auth/register`
- POST `/api/auth/login`
- POST `/api/auth/refresh`
- GET `/api/auth/me`
- GET `/api/procedures`
- GET `/api/procedures/<id>`
- POST `/api/attempts/start`
- POST `/api/attempts/<id>/event`
- POST `/api/attempts/<id>/finish`
- GET `/api/attempts/me`
- GET `/api/attempts/<id>`
- Admin/Instructor:
  - POST/PUT/DELETE `/api/admin/procedures`
  - GET `/api/admin/analytics`
  - GET `/api/admin/export/csv?procedure_id=...`

## WebSockets (Channels)

`ws://<host>/ws/attempts/<attempt_id>/`

Mensajes:

```json
{"t_ms":123,"type":"move","payload":{"x":10,"y":20}}
```

## Arquitectura

- **apps/accounts**: autenticación JWT, roles, seeds.
- **apps/procedures**: catálogo de procedimientos (JSONField para steps, zones, rubric).
- **apps/simulation**: attempts, events, streaming WS + fallback REST, simulador canvas.
- **apps/scoring**: motor de evaluación por reglas (`rules_v1`).
- **apps/analytics**: analítica básica, export CSV, CRUD instructor.

## Features implementadas

- Login JWT y roles (STUDENT, INSTRUCTOR, ADMIN).
- Catálogo de procedimientos con 3 seeds.
- Simulación en HTML5 Canvas con zonas objetivo/prohibida.
- Registro de eventos con WebSocket + fallback REST.
- Scoring automático y feedback textual.
- Dashboards para estudiante e instructor.
- Analítica y export CSV.
- Tests básicos de auth y scoring.
