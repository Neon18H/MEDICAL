# SmartSurgSim – Simulador Quirúrgico Inteligente REALISTA

Plataforma web profesional para entrenamiento quirúrgico con simulación 3D, guía por IA, evaluación avanzada y reportes clínicos en PDF.

## Stack
- Backend: Django 5.x + Django REST Framework
- Realtime: Django Channels (WebSockets)
- Base de datos: SQLite
- Frontend: HTML + CSS + JavaScript vanilla + Bootstrap 5 (CDN)
- 3D: Three.js (CDN)
- Charts: Chart.js (CDN)
- PDF: ReportLab
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
- Simulación: http://localhost:8000/simulator/<procedure_id>/
- Reporte: http://localhost:8000/reports/<attempt_id>/
- Panel instructor: http://localhost:8000/instructor/
- Panel admin: http://localhost:8000/admin-panel/
- Admin Django: http://localhost:8000/admin/

## Flujo funcional del simulador
1. El estudiante inicia un intento desde el dashboard.
2. Se genera un `Attempt` y el simulador 3D inicia el tracking.
3. Los eventos (`tool_select`, `move`, `action`, `hit`, `step_completed`, `error`) se envían por WebSocket o REST fallback.
4. El backend responde con warnings/hints en tiempo real.
5. Al finalizar el intento se ejecuta el scoring y se guarda el reporte (PDF disponible).

## Motor de scoring
El motor se encuentra en `simulator/scoring.py` y calcula:
- Score total (0–100)
- Subscores: precisión, eficiencia, seguridad, adherencia y manejo instrumental
- Penalizaciones por zona prohibida, instrumento incorrecto, acciones erróneas, pasos omitidos y tiempo excedido
- Feedback automático por reglas o por IA

## Endpoints clave
- `POST /api/auth/register/` registro
- `POST /api/auth/login/` login JWT
- `POST /api/auth/refresh/` refresh token
- `GET /api/procedures/` catálogo con filtros
- `POST /api/attempts/start/` iniciar intento
- `POST /api/attempts/{id}/finish/` finalizar intento y scoring
- `POST /api/attempts/{id}/event/` fallback de eventos
- `GET /api/attempts/me/` mis intentos
- `GET /api/reports/{id}/` reporte detallado
- `GET /api/reports/{id}/pdf/` PDF profesional
- `GET/PUT /api/auth/ai/settings/` configuración IA
- `POST /api/auth/ai/test/` test IA
- `POST /api/ai/guide/` guía IA
- `POST /api/ai/chat/` chat IA
- Instructor/Admin:
  - `/api/admin/procedures/`
  - `/api/admin/analytics/`
  - `/api/admin/export/csv/`

## IA Settings
1. Ve al Dashboard → AI Settings.
2. Selecciona proveedor (OpenAI o Gemini).
3. Ingresa tu API Key y modelo.
4. Activa el toggle “Usar IA en simulación”.
5. Ejecuta “Test Connection”.

## Modelos 3D glTF/GLB
- Reemplaza los placeholders agregando URLs de modelos en el JSON de `Procedure` (`zones` + `instruments`).
- El pipeline de Three.js ya está listo para cargar modelos reales.

## Ejecutar tests
```bash
python manage.py test
```
