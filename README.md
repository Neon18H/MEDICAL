# SmartSurgSim – Simulador Quirúrgico Inteligente

MVP web educativo para practicar procedimientos quirúrgicos simulados en Canvas, registrar eventos en tiempo real y evaluar el desempeño con un motor de scoring basado en reglas clínicas.

## Stack
- Backend: Django 5.x + Django REST Framework
- Realtime: Django Channels (WebSockets)
- Base de datos: SQLite
- Frontend: HTML + CSS + JavaScript vanilla + Bootstrap 5 (CDN)
- Autenticación: JWT (SimpleJWT)

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_initial
python manage.py runserver
```

## Credenciales seed
- **Admin**: `admin` / `Admin123!`
- **Instructor**: `instructor` / `Instructor123!`
- **Student**: `student` / `Student123!`

## URLs principales
- Landing: http://localhost:8000/
- Dashboard: http://localhost:8000/dashboard/
- Panel instructor: http://localhost:8000/instructor/
- Panel admin: http://localhost:8000/admin-panel/
- Admin Django: http://localhost:8000/admin/

## Flujo funcional del simulador
1. El estudiante inicia un intento desde el dashboard.
2. Se genera un `Attempt` y el simulador Canvas inicia el tracking.
3. Los eventos (`move`, `action`, `hit`, `step_completed`, `error`) se envían por WebSocket o REST fallback.
4. Al finalizar el intento se ejecuta el scoring y se guarda el reporte.

## Motor de scoring
El motor se encuentra en `simulator/scoring.py` y calcula:
- Score total (0–100)
- Subscores: precisión, eficiencia, seguridad y adherencia al protocolo
- Penalizaciones por zona prohibida, acciones incorrectas, pasos omitidos y tiempo excedido
- Feedback automático (3–8 recomendaciones)

## Endpoints clave
- `POST /api/auth/register/` registro
- `POST /api/auth/token/` login JWT
- `POST /api/auth/token/refresh/` refresh token
- `GET /api/procedures/` catálogo
- `POST /api/attempts/` iniciar intento
- `POST /api/attempts/{id}/complete/` finalizar intento y scoring
- `POST /api/events/` fallback de eventos
- `GET /api/reports/{id}/` reporte detallado

## Ejecutar tests
```bash
python manage.py test
```
