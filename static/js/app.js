const App = (() => {
  const apiBase = '/api';
  const authBase = '/api/auth';

  const getToken = () => localStorage.getItem('access_token');
  const setTokens = (access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  };
  const clearTokens = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  const apiFetch = async (url, options = {}) => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401 && localStorage.getItem('refresh_token')) {
      await refreshToken();
      return apiFetch(url, options);
    }
    return response;
  };

  const refreshToken = async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return;
    const response = await fetch(`${authBase}/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (response.ok) {
      const data = await response.json();
      setTokens(data.access, refresh);
    } else {
      clearTokens();
      window.location.href = '/';
    }
  };

  const initAuth = () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const logoutBtn = document.getElementById('logoutBtn');

    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        clearTokens();
        window.location.href = '/';
      });
    }

    if (getToken()) {
      window.location.href = '/dashboard/';
      return;
    }

    if (loginForm) {
      loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(loginForm));
        const response = await fetch(`${authBase}/token/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        const message = document.getElementById('loginMessage');
        if (response.ok) {
          const payload = await response.json();
          setTokens(payload.access, payload.refresh);
          window.location.href = '/dashboard/';
        } else {
          message.textContent = 'Credenciales inválidas.';
        }
      });
    }

    if (registerForm) {
      registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(registerForm));
        const response = await fetch(`${authBase}/register/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        const message = document.getElementById('registerMessage');
        if (response.ok) {
          message.textContent = 'Cuenta creada. Ahora inicia sesión.';
          registerForm.reset();
        } else {
          message.textContent = 'No se pudo crear la cuenta.';
        }
      });
    }
  };

  const loadDashboard = async () => {
    const meResponse = await apiFetch(`${authBase}/me/`);
    if (!meResponse.ok) {
      window.location.href = '/';
      return;
    }
    const me = await meResponse.json();

    const proceduresResponse = await apiFetch(`${apiBase}/procedures/`);
    const procedures = proceduresResponse.ok ? await proceduresResponse.json() : [];
    const proceduresList = document.getElementById('proceduresList');
    proceduresList.innerHTML = procedures
      .map(
        (proc) => `
        <div class="col-md-6">
          <div class="card h-100 shadow-sm border-0">
            <div class="card-body">
              <h6 class="fw-bold">${proc.name}</h6>
              <p class="text-muted small">${proc.description}</p>
              <button class="btn btn-primary btn-sm" data-procedure="${proc.id}">Iniciar</button>
            </div>
          </div>
        </div>`
      )
      .join('');

    proceduresList.querySelectorAll('button[data-procedure]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const procedureId = btn.getAttribute('data-procedure');
        window.location.href = `/simulator/${procedureId}/`;
      });
    });

    const attemptsResponse = await apiFetch(`${apiBase}/attempts/`);
    const attempts = attemptsResponse.ok ? await attemptsResponse.json() : [];
    const attemptsList = document.getElementById('attemptsList');
    attemptsList.innerHTML = attempts
      .map(
        (attempt) => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-2">
          <div>
            <div class="fw-semibold">${attempt.procedure_detail?.name || 'Procedimiento'}</div>
            <small class="text-muted">Estado: ${attempt.status}</small>
          </div>
          <div>
            <a class="btn btn-outline-secondary btn-sm" href="/reports/${attempt.id}/">Ver reporte</a>
          </div>
        </div>`
      )
      .join('');

    const roleActions = document.getElementById('roleActions');
    const actions = [];
    if (me.role === 'INSTRUCTOR' || me.role === 'ADMIN') {
      actions.push('<a class="btn btn-outline-primary" href="/instructor/">Panel instructor</a>');
    }
    if (me.role === 'ADMIN') {
      actions.push('<a class="btn btn-outline-dark" href="/admin-panel/">Panel admin</a>');
    }
    roleActions.innerHTML = actions.join('');
  };

  const startSimulator = async (procedureId) => {
    const procedureResponse = await apiFetch(`${apiBase}/procedures/${procedureId}/`);
    if (!procedureResponse.ok) {
      window.location.href = '/dashboard/';
      return;
    }
    const procedure = await procedureResponse.json();
    const attemptResponse = await apiFetch(`${apiBase}/attempts/`, {
      method: 'POST',
      body: JSON.stringify({ procedure: procedureId }),
    });
    if (!attemptResponse.ok) {
      window.location.href = '/dashboard/';
      return;
    }
    const attempt = await attemptResponse.json();

    const title = document.getElementById('procedureTitle');
    title.textContent = procedure.name;
    const stepsList = document.getElementById('stepsList');
    stepsList.innerHTML = procedure.steps
      .map((step) => `<div class="form-check"><input class="form-check-input" type="checkbox" disabled id="step-${step.id}"><label class="form-check-label">${step.title}</label></div>`)
      .join('');

    const checklist = document.getElementById('checklist');
    checklist.innerHTML = procedure.checklist
      .map((item) => `<div class="text-muted">• ${item.label}</div>`)
      .join('');

    const canvas = document.getElementById('simCanvas');
    const ctx = canvas.getContext('2d');
    const targetZone = procedure.zones.target;
    const forbiddenZone = procedure.zones.forbidden;
    let instrument = { x: 80, y: 80 };
    let errors = [];
    let lastMove = 0;
    let stepIndex = 0;
    let startTime = Date.now();
    let socket;
    let socketOpen = false;

    const connectSocket = () => {
      const token = getToken();
      const wsUrl = `ws://${window.location.host}/ws/attempts/${attempt.id}/?token=${token}`;
      socket = new WebSocket(wsUrl);
      socket.onopen = () => {
        socketOpen = true;
      };
      socket.onclose = () => {
        socketOpen = false;
      };
    };

    const sendEvent = async (eventType, payload = {}, timestampMs = null) => {
      const event = {
        event_type: eventType,
        payload,
        timestamp_ms: timestampMs ?? Date.now() - startTime,
      };
      if (socketOpen) {
        socket.send(JSON.stringify(event));
        return;
      }
      await apiFetch(`${apiBase}/events/`, {
        method: 'POST',
        body: JSON.stringify({ ...event, attempt: attempt.id }),
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#d4f7d4';
      ctx.beginPath();
      ctx.arc(targetZone.x, targetZone.y, targetZone.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#f7d4d4';
      ctx.beginPath();
      ctx.arc(forbiddenZone.x, forbiddenZone.y, forbiddenZone.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#0d6efd';
      ctx.beginPath();
      ctx.arc(instrument.x, instrument.y, 10, 0, Math.PI * 2);
      ctx.fill();
    };

    const updateTimer = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const minutes = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const seconds = String(elapsed % 60).padStart(2, '0');
      document.getElementById('timer').textContent = `${minutes}:${seconds}`;
    };

    const errorList = document.getElementById('errors');
    const addError = (message) => {
      errors.push(message);
      const li = document.createElement('li');
      li.textContent = message;
      errorList.appendChild(li);
    };

    canvas.addEventListener('mousemove', (event) => {
      const rect = canvas.getBoundingClientRect();
      instrument.x = ((event.clientX - rect.left) / rect.width) * canvas.width;
      instrument.y = ((event.clientY - rect.top) / rect.height) * canvas.height;
      draw();
      const now = Date.now();
      if (now - lastMove > 60) {
        sendEvent('move', { x: instrument.x, y: instrument.y });
        lastMove = now;
      }
      const dxForbidden = instrument.x - forbiddenZone.x;
      const dyForbidden = instrument.y - forbiddenZone.y;
      if (Math.hypot(dxForbidden, dyForbidden) < forbiddenZone.radius) {
        sendEvent('hit', { zone: 'forbidden', x: instrument.x, y: instrument.y });
        addError('Ingreso en zona prohibida');
        sendEvent('error', { code: 'FORBIDDEN_ZONE', x: instrument.x, y: instrument.y });
      }
      const dxTarget = instrument.x - targetZone.x;
      const dyTarget = instrument.y - targetZone.y;
      if (Math.hypot(dxTarget, dyTarget) < targetZone.radius) {
        sendEvent('hit', { zone: 'target', x: instrument.x, y: instrument.y });
      }
    });

    document.querySelectorAll('.action-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const action = btn.getAttribute('data-action');
        await sendEvent('action', { type: action });
        if (procedure.steps[stepIndex]) {
          const step = procedure.steps[stepIndex];
          document.getElementById(`step-${step.id}`).checked = true;
          await sendEvent('step_completed', { step_id: step.id });
          stepIndex += 1;
        }
      });
    });

    document.addEventListener('keydown', (event) => {
      const keyMap = { c: 'CUT', s: 'SUTURE', g: 'GRAB', r: 'RELEASE' };
      const action = keyMap[event.key.toLowerCase()];
      if (action) {
        document.querySelector(`.action-btn[data-action="${action}"]`).click();
      }
    });

    document.getElementById('finishAttempt').addEventListener('click', async () => {
      const durationSeconds = Math.floor((Date.now() - startTime) / 1000);
      await apiFetch(`${apiBase}/attempts/${attempt.id}/complete/`, {
        method: 'POST',
        body: JSON.stringify({ duration_seconds: durationSeconds }),
      });
      window.location.href = `/reports/${attempt.id}/`;
    });

    connectSocket();
    draw();
    setInterval(updateTimer, 1000);
  };

  const loadReport = async (attemptId) => {
    const response = await apiFetch(`${apiBase}/reports/${attemptId}/`);
    if (!response.ok) {
      window.location.href = '/dashboard/';
      return;
    }
    const data = await response.json();
    const attempt = data.attempt;
    const scoreSummary = document.getElementById('scoreSummary');
    scoreSummary.innerHTML = `
      <div class="d-flex align-items-center justify-content-between">
        <span class="badge bg-primary badge-score">Score ${attempt.score_total ?? 0}</span>
        <span class="text-muted">Duración ${attempt.duration_seconds}s</span>
      </div>
      <div class="mt-2">
        <div>Precision: ${attempt.subscores.precision ?? 0}</div>
        <div>Eficiencia: ${attempt.subscores.efficiency ?? 0}</div>
        <div>Seguridad: ${attempt.subscores.safety ?? 0}</div>
        <div>Adherencia: ${attempt.subscores.protocol_adherence ?? 0}</div>
      </div>
      <div class="mt-3">
        <h6 class="fw-bold">Feedback</h6>
        <ul>${(attempt.feedback || []).map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
    `;

    const timeline = document.getElementById('timeline');
    timeline.innerHTML = data.events
      .slice(0, 50)
      .map((event) => `<li class="timeline-item">${event.event_type} - ${event.timestamp_ms}ms</li>`)
      .join('');

    const heatmap = document.getElementById('heatmap');
    const ctx = heatmap.getContext('2d');
    ctx.clearRect(0, 0, heatmap.width, heatmap.height);
    ctx.fillStyle = '#f7d4d4';
    data.events
      .filter((event) => event.event_type === 'error' || event.event_type === 'hit')
      .forEach((event) => {
        const { x, y } = event.payload || { x: Math.random() * 320, y: Math.random() * 220 };
        ctx.beginPath();
        ctx.arc(x || Math.random() * 320, y || Math.random() * 220, 6, 0, Math.PI * 2);
        ctx.fill();
      });
  };

  const loadInstructorPanel = async () => {
    const proceduresResponse = await apiFetch(`${apiBase}/procedures/`);
    const procedures = proceduresResponse.ok ? await proceduresResponse.json() : [];
    const container = document.getElementById('procedureManager');

    const renderProcedures = () => {
      container.innerHTML = `
        <form id="procedureForm" class="mb-3">
          <div class="mb-2"><input class="form-control" name="name" placeholder="Nombre" required></div>
          <div class="mb-2"><textarea class="form-control" name="description" placeholder="Descripción" required></textarea></div>
          <button class="btn btn-primary" type="submit">Crear procedimiento</button>
        </form>
        <div>${procedures
          .map(
            (proc) => `
            <div class="border rounded p-2 mb-2">
              <div class="fw-semibold">${proc.name}</div>
              <div class="small text-muted">${proc.description}</div>
              <button class="btn btn-outline-danger btn-sm mt-2" data-delete="${proc.id}">Eliminar</button>
            </div>`
          )
          .join('')}</div>
      `;
    };

    renderProcedures();

    const form = document.getElementById('procedureForm');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = Object.fromEntries(new FormData(form));
      const payload = {
        ...formData,
        steps: [{ id: 1, title: 'Paso 1' }],
        instruments: ['Instrumento'],
        zones: { target: { x: 160, y: 120, radius: 50 }, forbidden: { x: 320, y: 200, radius: 40 } },
        checklist: [{ code: 'CHECK', label: 'Checklist' }],
        rubric: {
          version: 'v1',
          expected_time_seconds: 180,
          penalties: { forbidden_hit: 6, wrong_action: 4, step_omitted: 5, time_over: 1 },
        },
      };
      const response = await apiFetch(`${apiBase}/procedures/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const newProc = await response.json();
        procedures.push(newProc);
        renderProcedures();
      }
    });

    container.addEventListener('click', async (event) => {
      const target = event.target;
      if (target.matches('[data-delete]')) {
        const id = target.getAttribute('data-delete');
        const response = await apiFetch(`${apiBase}/procedures/${id}/`, { method: 'DELETE' });
        if (response.ok || response.status === 204) {
          const index = procedures.findIndex((proc) => String(proc.id) === id);
          if (index > -1) {
            procedures.splice(index, 1);
            renderProcedures();
          }
        }
      }
    });

    const analyticsResponse = await apiFetch(`${apiBase}/analytics/`);
    const analytics = analyticsResponse.ok ? await analyticsResponse.json() : [];
    const analyticsContainer = document.getElementById('analytics');
    analyticsContainer.innerHTML = analytics
      .map(
        (item) => `
        <div class="d-flex justify-content-between border-bottom py-2">
          <span>${item.procedure__name}</span>
          <span class="fw-semibold">${Number(item.avg_score || 0).toFixed(1)}</span>
        </div>`
      )
      .join('');
  };

  return {
    initAuth,
    loadDashboard,
    startSimulator,
    loadReport,
    loadInstructorPanel,
  };
})();

window.App = App;
