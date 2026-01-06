const App = (() => {
  const apiBase = '/api';
  const authBase = '/api/auth';
  const simulationState = {
    active: false,
    attemptId: null,
    locked: false,
  };
  let cachedUser = null;
  let shellBootstrapped = false;

  // Auth flow (JWT):
  // - Tokens live in localStorage as access_token / refresh_token.
  // - apiFetch attaches Bearer access_token to every request.
  // - If a request returns 401, we attempt ONE refresh, persist new access, and retry once.
  // - If refresh fails or retry still 401, we clear tokens and redirect to login.
  const getToken = () => localStorage.getItem('access_token');
  const getRefreshToken = () => localStorage.getItem('refresh_token');
  const setTokens = (access, refresh) => {
    if (access) localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  };
  const clearTokens = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  let isRefreshing = false;
  let refreshPromise = null;

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
    if (response.status !== 401) {
      return response;
    }

    if (options._retry || !getRefreshToken()) {
      handleLogout();
      return response;
    }

    const refreshed = await refreshToken();
    if (!refreshed) {
      handleLogout();
      return response;
    }
    return apiFetch(url, { ...options, _retry: true });
  };

  const refreshToken = async () => {
    const refresh = getRefreshToken();
    if (!refresh) return false;
    if (isRefreshing && refreshPromise) {
      return refreshPromise;
    }
    isRefreshing = true;
    refreshPromise = (async () => {
      const response = await fetch(`${authBase}/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!response.ok) {
        return false;
      }
      const data = await response.json();
      if (!data.access) {
        return false;
      }
      setTokens(data.access, refresh);
      return true;
    })();
    const result = await refreshPromise;
    isRefreshing = false;
    refreshPromise = null;
    return result;
  };

  const handleLogout = async () => {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await fetch(`${authBase}/logout/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        });
      }
    } finally {
      clearTokens();
      if (simulationState.active) {
        showSimulationOverlay(
          'Sesión expirada',
          'Tu sesión finalizó durante la simulación. Guarda el progreso y vuelve a iniciar sesión.'
        );
        return;
      }
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      }
    }
  };

  const showSimulationOverlay = (title, message) => {
    let overlay = document.getElementById('simulationOverlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'simulationOverlay';
      overlay.className = 'simulator-overlay';
      overlay.innerHTML = `
        <div class="simulator-overlay-card">
          <h5 class="fw-bold mb-2" id="simulationOverlayTitle"></h5>
          <p class="text-muted small mb-3" id="simulationOverlayMessage"></p>
          <div class="d-grid gap-2">
            <button class="btn btn-primary btn-sm" id="simulationOverlayExit">Salir a login</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
      overlay.querySelector('#simulationOverlayExit').addEventListener('click', () => {
        window.location.href = '/';
      });
    }
    overlay.querySelector('#simulationOverlayTitle').textContent = title;
    overlay.querySelector('#simulationOverlayMessage').textContent = message;
    overlay.classList.add('show');
  };

  const initAuth = () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (getToken()) {
      window.location.href = '/dashboard/';
      return;
    }

    if (loginForm) {
      loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(loginForm));
        const response = await fetch(`${authBase}/login/`, {
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

  const loadShell = async (options = {}) => {
    if (shellBootstrapped && cachedUser) {
      return cachedUser;
    }
    const meResponse = await apiFetch(`${authBase}/me/`);
    if (!meResponse.ok) {
      if (!options.allowFailure) {
        handleLogout();
      }
      return null;
    }
    const me = await meResponse.json();
    cachedUser = me;
    const nameEl = document.getElementById('userProfileName');
    const roleEl = document.getElementById('userProfileRole');
    if (nameEl) nameEl.textContent = me.username;
    if (roleEl) roleEl.textContent = me.role;
    const instructorNav = document.getElementById('navInstructor');
    const adminNav = document.getElementById('navAdmin');
    if (instructorNav) instructorNav.style.display = me.role === 'STUDENT' ? 'none' : 'block';
    if (adminNav) adminNav.style.display = me.role === 'ADMIN' ? 'block' : 'none';

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        await handleLogout();
      });
    }

    const aiStatus = document.getElementById('aiStatusBadge');
    if (aiStatus) {
      const aiResponse = await apiFetch(`${authBase}/ai/settings/`);
      if (aiResponse.ok) {
        const aiSettings = await aiResponse.json();
        aiStatus.textContent = aiSettings.use_ai ? 'IA: ON' : 'IA: OFF';
        aiStatus.className = aiSettings.use_ai
          ? 'badge bg-success-subtle text-success'
          : 'badge bg-secondary-subtle text-secondary';
      }
    }
    shellBootstrapped = true;
    return me;
  };

  const loadDashboard = async () => {
    const me = await loadShell();
    if (!me) return;

    const proceduresResponse = await apiFetch(`${apiBase}/procedures/`);
    const procedures = proceduresResponse.ok ? await proceduresResponse.json() : [];
    const proceduresList = document.getElementById('proceduresList');

    const searchInput = document.getElementById('procedureSearch');
    const filterSpecialty = document.getElementById('filterSpecialty');
    const filterDifficulty = document.getElementById('filterDifficulty');
    const specialties = [...new Set(procedures.map((proc) => proc.specialty))].sort();
    const difficulties = [...new Set(procedures.map((proc) => proc.difficulty))].sort();
    if (filterSpecialty) {
      filterSpecialty.innerHTML += specialties
        .map((item) => `<option value="${item}">${item}</option>`)
        .join('');
    }
    if (filterDifficulty) {
      filterDifficulty.innerHTML += difficulties
        .map((item) => `<option value="${item}">${item}</option>`)
        .join('');
    }

    const renderProcedures = () => {
      const query = (searchInput?.value || '').toLowerCase();
      const specialty = filterSpecialty?.value || '';
      const difficulty = filterDifficulty?.value || '';
      const filtered = procedures.filter((proc) => {
        const matchesQuery = proc.name.toLowerCase().includes(query);
        const matchesSpecialty = specialty ? proc.specialty === specialty : true;
        const matchesDifficulty = difficulty ? proc.difficulty === difficulty : true;
        return matchesQuery && matchesSpecialty && matchesDifficulty;
      });
      proceduresList.innerHTML = filtered
        .map(
          (proc) => `
          <div class="col-md-6">
            <div class="card h-100 shadow-sm border-0">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h6 class="fw-bold">${proc.name}</h6>
                    <div class="text-muted small">${proc.specialty} · ${proc.procedure_type}</div>
                  </div>
                  <span class="badge bg-primary-subtle text-primary">${proc.difficulty}</span>
                </div>
                <p class="text-muted small mt-2">${proc.description}</p>
                <div class="d-flex justify-content-between align-items-center">
                  <span class="small text-muted">${proc.duration_estimated_minutes} min</span>
                  <button class="btn btn-primary btn-sm" data-procedure="${proc.id}" ${
                    proc.is_playable ? '' : 'disabled'
                  }>
                    ${proc.is_playable ? 'Iniciar simulación' : 'Plantilla'}
                  </button>
                </div>
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
    };

    searchInput?.addEventListener('input', renderProcedures);
    filterSpecialty?.addEventListener('change', renderProcedures);
    filterDifficulty?.addEventListener('change', renderProcedures);
    renderProcedures();

    const attemptsResponse = await apiFetch(`${apiBase}/attempts/me/`);
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

    await initAISettings();
  };

  const initAISettings = async () => {
    const form = document.getElementById('aiSettingsForm');
    if (!form) return;
    const message = document.getElementById('aiSettingsMessage');
    const testBtn = document.getElementById('testAiBtn');
    const aiResponse = await apiFetch(`${authBase}/ai/settings/`);
    if (aiResponse.ok) {
      const settings = await aiResponse.json();
      form.use_ai.checked = settings.use_ai || false;
      if (settings.has_key) {
        form.api_key.placeholder = '••••••••';
      }
    }
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form));
      data.use_ai = form.use_ai.checked;
      if (!data.api_key) {
        delete data.api_key;
      }
      const response = await apiFetch(`${authBase}/ai/settings/`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      if (response.ok) {
        message.textContent = 'Configuración guardada.';
        message.className = 'text-success small mt-2';
      } else {
        message.textContent = 'No se pudo guardar.';
        message.className = 'text-danger small mt-2';
      }
    });

    testBtn.addEventListener('click', async () => {
      const response = await apiFetch(`${authBase}/ai/test/`, { method: 'POST' });
      if (response.ok) {
        message.textContent = 'Conexión exitosa con IA.';
        message.className = 'text-success small mt-2';
      } else {
        message.textContent = 'Fallo en la conexión IA.';
        message.className = 'text-danger small mt-2';
      }
    });
  };

  const startSimulator = async (procedureId) => {
    const me = await loadShell({ allowFailure: false });
    if (!me) return;

    const topbarTitle = document.querySelector('.topbar-title');
    if (topbarTitle) topbarTitle.textContent = 'Simulación quirúrgica';

    const procedureResponse = await apiFetch(`${apiBase}/procedures/${procedureId}/`);
    if (!procedureResponse.ok) {
      showSimulationOverlay(
        'No se pudo cargar el procedimiento',
        'Verifica tu conexión o intenta nuevamente desde el dashboard.'
      );
      return;
    }
    const procedure = await procedureResponse.json();

    const attemptResponse = await apiFetch(`${apiBase}/attempts/start/`, {
      method: 'POST',
      body: JSON.stringify({ procedure: procedureId }),
    });
    if (!attemptResponse.ok) {
      showSimulationOverlay(
        'No se pudo iniciar el intento',
        'El servidor no pudo crear el intento. Intenta nuevamente desde el panel.'
      );
      return;
    }
    const attempt = await attemptResponse.json();
    simulationState.active = true;
    simulationState.attemptId = attempt.id;
    simulationState.locked = true;
    window.history.replaceState({}, '', `?attempt=${attempt.id}`);

    const title = document.getElementById('procedureTitle');
    const meta = document.getElementById('procedureMeta');
    title.textContent = procedure.name;
    meta.textContent = `${procedure.specialty} · ${procedure.difficulty}`;

    const stepsList = document.getElementById('stepsList');
    stepsList.innerHTML = procedure.steps
      .map(
        (step, index) => `
        <div class="step-item" data-step-index="${index}">
          <div class="fw-semibold">${step.title}</div>
          <div class="small text-muted">${step.objectives || ''}</div>
        </div>`
      )
      .join('');

    const checklist = document.getElementById('checklist');
    checklist.innerHTML = procedure.checklist
      .map((item) => `<div class="text-muted">• ${item.label}</div>`)
      .join('');

    const instrumentList = document.getElementById('instrumentList');
    const instruments = (procedure.instruments || []).map((item) =>
      typeof item === 'string' ? { name: item, tool: item.toUpperCase() } : item
    );
    if (!instruments.length) {
      instruments.push(
      { name: 'Bisturí', tool: 'SCALPEL' },
      { name: 'Pinza', tool: 'FORCEPS' },
      { name: 'Porta-agujas', tool: 'NEEDLE_DRIVER' },
      { name: 'Cauterio', tool: 'CAUTERY' }
      );
    }
    instrumentList.innerHTML = instruments
      .map(
        (instrument, index) => `
        <button class="btn btn-outline-primary instrument-btn" data-tool="${instrument.tool}" data-index="${index}">
          ${instrument.name}
        </button>`
      )
      .join('');

    const stepObjective = document.getElementById('stepObjective');
    const stepInstrument = document.getElementById('stepInstrument');
    const stepRisks = document.getElementById('stepRisks');
    const stepTips = document.getElementById('stepTips');
    const currentStepLabel = document.getElementById('currentStepLabel');
    const errorCountEl = document.getElementById('errorCount');
    const progressLabel = document.getElementById('progressLabel');
    const zoneStatus = document.getElementById('zoneStatus');

    let stepIndex = 0;
    let errors = [];
    let startTime = Date.now();
    let socket;
    let socketOpen = false;
    let selectedTool = instruments[0]?.tool || 'SCALPEL';
    let activeAction = 'CUT';
    let updateInstrumentVisual = () => {};
    let flushContactDuration = async () => {};
    const toolActionMap = {
      SCALPEL: 'CUT',
      FORCEPS: 'GRAB',
      NEEDLE_DRIVER: 'SUTURE',
      CAUTERY: 'COAGULATE',
    };

    const syncActionForTool = (tool) => {
      const mapped = toolActionMap[tool];
      if (mapped) {
        activeAction = mapped;
        document.querySelectorAll('.action-btn').forEach((btn) => {
          btn.classList.toggle('active', btn.getAttribute('data-action') === activeAction);
        });
      }
    };

    const updateStepPanel = () => {
      const step = procedure.steps[stepIndex];
      document.querySelectorAll('.step-item').forEach((el) => {
        const index = Number(el.dataset.stepIndex);
        el.classList.toggle('active', index === stepIndex);
      });
      if (!step) return;
      currentStepLabel.textContent = step.title;
      stepObjective.textContent = step.objectives || 'Controlar la zona quirúrgica.';
      stepInstrument.textContent = (step.instruments || [selectedTool]).join(', ') || 'Instrumento disponible';
      stepRisks.innerHTML = (step.risks || []).map((risk) => `<li>${risk}</li>`).join('');
      stepTips.innerHTML = (step.tips || []).map((tip) => `<li>${tip}</li>`).join('');
      const totalSteps = procedure.steps.length || 1;
      const progress = Math.round((stepIndex / totalSteps) * 100);
      progressLabel.textContent = `${progress}%`;
      requestAIGuidance(step);
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
      errorCountEl.textContent = errors.length;
      const li = document.createElement('li');
      li.textContent = message;
      errorList.appendChild(li);
    };

    const connectSocket = () => {
      const token = getToken();
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${wsProtocol}://${window.location.host}/ws/attempts/${attempt.id}/?token=${token}`;
      socket = new WebSocket(wsUrl);
      socket.onopen = () => {
        socketOpen = true;
      };
      socket.onclose = () => {
        socketOpen = false;
      };
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.warning) {
          pushLiveAlert(`⚠️ ${data.warning}`);
        }
        if (data.hint) {
          pushLiveAlert(`💡 ${data.hint}`);
        }
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
      await apiFetch(`${apiBase}/attempts/${attempt.id}/event/`, {
        method: 'POST',
        body: JSON.stringify(event),
      });
    };

    const liveAlerts = document.getElementById('liveAlerts');
    const pushLiveAlert = (message) => {
      const entry = document.createElement('div');
      entry.textContent = message;
      liveAlerts.prepend(entry);
    };

    document.querySelectorAll('.instrument-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        document.querySelectorAll('.instrument-btn').forEach((el) => el.classList.remove('active'));
        btn.classList.add('active');
        selectedTool = btn.dataset.tool;
        updateInstrumentVisual(selectedTool);
        syncActionForTool(selectedTool);
        updateStepPanel();
        await sendEvent('tool_select', { tool: selectedTool });
      });
    });
    document.querySelector('.instrument-btn')?.classList.add('active');
    syncActionForTool(selectedTool);

    document.querySelectorAll('.action-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        document.querySelectorAll('.action-btn').forEach((el) => el.classList.remove('active'));
        btn.classList.add('active');
        activeAction = btn.getAttribute('data-action');
        await sendEvent('action_select', { action: activeAction, tool: selectedTool });
      });
    });

    document.getElementById('finishAttempt').addEventListener('click', async () => {
      const durationSeconds = Math.floor((Date.now() - startTime) / 1000);
      await flushContactDuration();
      await apiFetch(`${apiBase}/attempts/${attempt.id}/finish/`, {
        method: 'POST',
        body: JSON.stringify({ duration_seconds: durationSeconds }),
      });
      simulationState.active = false;
      simulationState.locked = false;
      window.location.href = `/reports/${attempt.id}/`;
    });

    document.getElementById('resetView').addEventListener('click', () => {
      if (window.simControls && window.simCamera) {
        window.simCamera.position.set(0, 2.2, 4.2);
        window.simControls.target.set(0, 1, 0);
        window.simControls.update();
      }
    });

    const aiAskBtn = document.getElementById('aiAskBtn');
    aiAskBtn.addEventListener('click', async () => {
      const question = document.getElementById('aiQuestion').value.trim();
      if (!question) return;
      const response = await apiFetch(`${apiBase}/ai/chat/`, {
        method: 'POST',
        body: JSON.stringify({
          question,
          context: {
            procedure: procedure.name,
            step: procedure.steps[stepIndex]?.title,
            tool: selectedTool,
          },
        }),
      });
      const aiAnswer = document.getElementById('aiAnswer');
      if (response.ok) {
        const data = await response.json();
        aiAnswer.textContent = data.answer;
      } else {
        aiAnswer.textContent = 'No se pudo obtener respuesta.';
      }
    });

    const requestAIGuidance = async (step) => {
      const response = await apiFetch(`${apiBase}/ai/guide/`, {
        method: 'POST',
        body: JSON.stringify({
          procedure,
          step,
          context: {
            tool: selectedTool,
            errors: errors.length,
            elapsed_seconds: Math.floor((Date.now() - startTime) / 1000),
          },
        }),
      });
      if (!response.ok) return;
      const data = await response.json();
      document.getElementById('aiNextStep').textContent = data.next_step_suggestion;
      document.getElementById('aiWarnings').innerHTML = data.risk_warnings
        .map((warning) => `<li>${warning}</li>`)
        .join('');
      document.getElementById('aiChecklist').innerHTML = data.checklist
        .map((item) => `<li>${item}</li>`)
        .join('');
    };

    const initThreeScene = () => {
      const container = document.getElementById('threeContainer');
      const width = container.clientWidth;
      const height = container.clientHeight || 460;
      container.innerHTML = '';
      const scene = new THREE.Scene();
      scene.background = new THREE.Color('#0b1120');
      const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 50);
      camera.position.set(0, 2.4, 4.6);

      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(window.devicePixelRatio || 1);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      container.appendChild(renderer.domElement);

      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.minDistance = 2.5;
      controls.maxDistance = 7;
      controls.target.set(0, 1.1, 0);
      controls.update();

      const ambient = new THREE.AmbientLight(0xffffff, 0.25);
      scene.add(ambient);
      const hemi = new THREE.HemisphereLight(0xbdd7ff, 0x111827, 0.6);
      scene.add(hemi);
      const keyLight = new THREE.SpotLight(0xffffff, 1.3, 15, Math.PI / 5, 0.4, 1);
      keyLight.position.set(2.8, 4.4, 1.5);
      keyLight.castShadow = true;
      keyLight.shadow.mapSize.set(1024, 1024);
      scene.add(keyLight);
      const fillLight = new THREE.SpotLight(0xc7d2fe, 0.8, 15, Math.PI / 6, 0.3, 1);
      fillLight.position.set(-2.2, 4, 1.2);
      fillLight.castShadow = true;
      scene.add(fillLight);

      const floor = new THREE.Mesh(
        new THREE.PlaneGeometry(10, 10),
        new THREE.MeshStandardMaterial({ color: '#0f172a', roughness: 0.9, metalness: 0.1 })
      );
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = 0;
      floor.receiveShadow = true;
      scene.add(floor);

      const tableGroup = new THREE.Group();
      const tableTop = new THREE.Mesh(
        new THREE.BoxGeometry(3.2, 0.18, 1.6),
        new THREE.MeshStandardMaterial({ color: '#1e293b', roughness: 0.4 })
      );
      tableTop.position.set(0, 0.8, 0);
      tableTop.receiveShadow = true;
      tableTop.castShadow = true;
      tableGroup.add(tableTop);
      const tableBase = new THREE.Mesh(
        new THREE.CylinderGeometry(0.35, 0.45, 0.6, 16),
        new THREE.MeshStandardMaterial({ color: '#0f172a', metalness: 0.3 })
      );
      tableBase.position.set(0, 0.4, 0);
      tableBase.castShadow = true;
      tableGroup.add(tableBase);
      scene.add(tableGroup);

      const patientGroup = new THREE.Group();
      const torsoGeometry = new THREE.CapsuleGeometry(0.8, 1.4, 8, 16);
      const torsoMaterial = new THREE.MeshStandardMaterial({ color: '#e2e8f0', roughness: 0.6 });
      const torso = new THREE.Mesh(torsoGeometry, torsoMaterial);
      torso.castShadow = true;
      torso.receiveShadow = true;
      torso.position.set(0, 1.2, 0);
      patientGroup.add(torso);
      const head = new THREE.Mesh(
        new THREE.SphereGeometry(0.26, 16, 16),
        new THREE.MeshStandardMaterial({ color: '#e2e8f0', roughness: 0.6 })
      );
      head.position.set(0, 1.9, -0.6);
      head.castShadow = true;
      patientGroup.add(head);
      const pelvis = new THREE.Mesh(
        new THREE.SphereGeometry(0.45, 18, 18),
        new THREE.MeshStandardMaterial({ color: '#dbeafe', roughness: 0.5 })
      );
      pelvis.position.set(0, 0.75, 0.5);
      pelvis.castShadow = true;
      patientGroup.add(pelvis);
      const drape = new THREE.Mesh(
        new THREE.CylinderGeometry(1.2, 1.1, 0.2, 32),
        new THREE.MeshStandardMaterial({ color: '#0ea5e9', roughness: 0.8 })
      );
      drape.position.set(0, 1.05, 0.1);
      drape.receiveShadow = true;
      patientGroup.add(drape);
      scene.add(patientGroup);

      const target = procedure.zones?.target || { x: 0.3, y: 1.25, z: 0.25, radius: 0.32 };
      const forbidden = procedure.zones?.forbidden || { x: -0.35, y: 1.15, z: 0.2, radius: 0.28 };

      const organ = new THREE.Mesh(
        new THREE.SphereGeometry(target.radius, 28, 28),
        new THREE.MeshStandardMaterial({
          color: '#22c55e',
          emissive: '#0f766e',
          emissiveIntensity: 0.6,
          opacity: 0.9,
          transparent: true,
        })
      );
      organ.position.set(target.x, target.y, target.z);
      organ.castShadow = true;
      scene.add(organ);

      const danger = new THREE.Mesh(
        new THREE.SphereGeometry(forbidden.radius, 24, 24),
        new THREE.MeshStandardMaterial({ color: '#ef4444', opacity: 0.25, transparent: true })
      );
      danger.position.set(forbidden.x, forbidden.y, forbidden.z);
      scene.add(danger);

      const fieldRing = new THREE.Mesh(
        new THREE.RingGeometry(0.45, 0.65, 40),
        new THREE.MeshBasicMaterial({ color: '#38bdf8', side: THREE.DoubleSide, opacity: 0.6, transparent: true })
      );
      fieldRing.position.set(target.x, target.y, target.z);
      fieldRing.rotation.x = Math.PI / 2;
      scene.add(fieldRing);

      const instrumentGroup = new THREE.Group();
      instrumentGroup.position.set(0, 1.2, 1.2);
      scene.add(instrumentGroup);

      const buildInstrument = (type) => {
        const group = new THREE.Group();
        if (type === 'SCALPEL') {
          const handle = new THREE.Mesh(
            new THREE.CylinderGeometry(0.03, 0.05, 0.5, 12),
            new THREE.MeshStandardMaterial({ color: '#94a3b8', metalness: 0.6 })
          );
          handle.rotation.z = Math.PI / 2;
          const blade = new THREE.Mesh(
            new THREE.BoxGeometry(0.24, 0.02, 0.08),
            new THREE.MeshStandardMaterial({ color: '#e2e8f0', metalness: 0.8 })
          );
          blade.position.set(0.32, 0, 0);
          group.add(handle, blade);
        } else if (type === 'FORCEPS') {
          const arm1 = new THREE.Mesh(
            new THREE.BoxGeometry(0.4, 0.02, 0.04),
            new THREE.MeshStandardMaterial({ color: '#cbd5f5', metalness: 0.7 })
          );
          const arm2 = arm1.clone();
          arm1.position.set(0.2, 0.02, 0.02);
          arm2.position.set(0.2, -0.02, -0.02);
          group.add(arm1, arm2);
        } else if (type === 'NEEDLE_DRIVER') {
          const shaft = new THREE.Mesh(
            new THREE.CylinderGeometry(0.03, 0.03, 0.5, 10),
            new THREE.MeshStandardMaterial({ color: '#94a3b8', metalness: 0.6 })
          );
          shaft.rotation.z = Math.PI / 2;
          const ring = new THREE.Mesh(
            new THREE.TorusGeometry(0.08, 0.02, 12, 20),
            new THREE.MeshStandardMaterial({ color: '#e2e8f0', metalness: 0.8 })
          );
          ring.position.set(-0.25, 0, 0);
          group.add(shaft, ring);
        } else if (type === 'CAUTERY') {
          const handle = new THREE.Mesh(
            new THREE.CylinderGeometry(0.04, 0.04, 0.6, 12),
            new THREE.MeshStandardMaterial({ color: '#0ea5e9', metalness: 0.4 })
          );
          handle.rotation.z = Math.PI / 2;
          const tip = new THREE.Mesh(
            new THREE.ConeGeometry(0.04, 0.12, 12),
            new THREE.MeshStandardMaterial({ color: '#f97316', emissive: '#f97316', emissiveIntensity: 0.6 })
          );
          tip.position.set(0.34, 0, 0);
          tip.rotation.z = Math.PI / 2;
          group.add(handle, tip);
        }
        group.visible = false;
        return group;
      };

      const instrumentMeshes = {
        SCALPEL: buildInstrument('SCALPEL'),
        FORCEPS: buildInstrument('FORCEPS'),
        NEEDLE_DRIVER: buildInstrument('NEEDLE_DRIVER'),
        CAUTERY: buildInstrument('CAUTERY'),
      };
      Object.values(instrumentMeshes).forEach((mesh) => instrumentGroup.add(mesh));
      updateInstrumentVisual = (tool) => {
        Object.entries(instrumentMeshes).forEach(([key, mesh]) => {
          mesh.visible = key === tool;
        });
      };
      updateInstrumentVisual(selectedTool);

      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      let lastMove = 0;
      let lastZoneHit = null;
      let zoneContactStart = null;
      let actionStart = null;
      let pointerInside = false;
      let lastScreen = null;

      flushContactDuration = async () => {
        if (zoneContactStart && lastZoneHit) {
          await sendEvent('contact_duration', {
            zone: lastZoneHit,
            duration_ms: Date.now() - zoneContactStart,
          });
        }
        zoneContactStart = null;
        lastZoneHit = null;
      };

      const updateZoneStatus = (status, isDanger = false) => {
        if (!zoneStatus) return;
        zoneStatus.textContent = status;
        zoneStatus.classList.toggle('text-danger', isDanger);
        zoneStatus.classList.toggle('text-success', status === 'Objetivo');
      };

      const interactionMeshes = [torso, pelvis];

      const onPointerMove = (event) => {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(interactionMeshes, true);
        if (intersects.length) {
          pointerInside = true;
          const point = intersects[0].point;
          instrumentGroup.position.copy(point);
          lastScreen = { x: (mouse.x + 1) / 2, y: (1 - mouse.y) / 2 };
          const now = Date.now();
          if (now - lastMove > 80) {
            sendEvent('move', {
              x: point.x,
              y: point.y,
              z: point.z,
              tool: selectedTool,
              screen: lastScreen,
            });
            lastMove = now;
          }
          const distTarget = point.distanceTo(organ.position);
          const distForbidden = point.distanceTo(danger.position);
          if (distForbidden < forbidden.radius) {
            updateZoneStatus('Peligro', true);
            danger.material.opacity = 0.6;
            if (lastZoneHit !== 'forbidden') {
              zoneContactStart = Date.now();
              sendEvent('hit', {
                zone: 'forbidden',
                x: point.x,
                y: point.y,
                z: point.z,
                severity: 'high',
                screen: lastScreen,
              });
              addError('Contacto con zona prohibida');
              sendEvent('error', { code: 'FORBIDDEN_ZONE', x: point.x, y: point.y, z: point.z });
            }
            lastZoneHit = 'forbidden';
          } else if (distTarget < target.radius) {
            updateZoneStatus('Objetivo');
            danger.material.opacity = 0.25;
            if (lastZoneHit !== 'target') {
              zoneContactStart = Date.now();
              sendEvent('hit', {
                zone: 'target',
                x: point.x,
                y: point.y,
                z: point.z,
                severity: 'low',
                screen: lastScreen,
              });
            }
            lastZoneHit = 'target';
          } else {
            updateZoneStatus('Estable');
            danger.material.opacity = 0.25;
            if (zoneContactStart && lastZoneHit) {
              sendEvent('contact_duration', {
                zone: lastZoneHit,
                duration_ms: Date.now() - zoneContactStart,
              });
            }
            zoneContactStart = null;
            lastZoneHit = null;
          }
        } else if (pointerInside) {
          pointerInside = false;
          updateZoneStatus('Estable');
        }
      };

      const onPointerDown = () => {
        if (!pointerInside) return;
        actionStart = Date.now();
      };

      const onPointerUp = async () => {
        if (!actionStart) return;
        const duration = Date.now() - actionStart;
        const intensity = Number(document.getElementById('intensitySlider').value);
        const actionPayload = {
          type: activeAction,
          intensity,
          tool: selectedTool,
          duration,
          screen: lastScreen,
        };
        await sendEvent('action', actionPayload);
        const step = procedure.steps[stepIndex];
        if (step && step.actions?.includes(activeAction)) {
          await sendEvent('step_completed', { step_id: step.id });
          stepIndex = Math.min(stepIndex + 1, procedure.steps.length);
          updateStepPanel();
        }
        actionStart = null;
      };

      renderer.domElement.addEventListener('pointermove', onPointerMove);
      renderer.domElement.addEventListener('pointerdown', onPointerDown);
      renderer.domElement.addEventListener('pointerup', onPointerUp);

      const loader = new THREE.GLTFLoader();
      loader.load(
        '/static/models/patient_torso.glb',
        (gltf) => {
          const model = gltf.scene;
          model.traverse((node) => {
            if (node.isMesh) {
              node.castShadow = true;
              node.receiveShadow = true;
            }
          });
          model.position.set(0, 0.6, 0);
          model.scale.set(1.2, 1.2, 1.2);
          scene.add(model);
          patientGroup.visible = false;
        },
        undefined,
        () => {}
      );

      const animate = () => {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
      };
      animate();
      window.simControls = controls;
      window.simCamera = camera;
    };

    connectSocket();
    initThreeScene();
    updateStepPanel();
    setInterval(updateTimer, 1000);
  };

  const loadReport = async (attemptId) => {
    await loadShell();
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
        <div>Manejo instrumental: ${attempt.subscores.instrument_handling ?? 0}</div>
      </div>
      <div class="mt-3">
        <h6 class="fw-bold">Feedback</h6>
        <ul>${(attempt.feedback || []).map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
      <div class="mt-3 small text-muted">
        IA usada: ${attempt.ai_used ? 'Sí' : 'No'}
      </div>
    `;

    const timeline = document.getElementById('timeline');
    timeline.innerHTML = data.events
      .slice(0, 60)
      .map((event) => {
        const detail = event.payload?.tool ? `(${event.payload.tool})` : '';
        const action = event.payload?.type ? `: ${event.payload.type}` : '';
        return `<li class="timeline-item">${event.event_type}${action} ${detail} - ${event.timestamp_ms}ms</li>`;
      })
      .join('');

    const heatmap = document.getElementById('heatmap');
    const ctx = heatmap.getContext('2d');
    ctx.clearRect(0, 0, heatmap.width, heatmap.height);
    ctx.fillStyle = '#f87171';
    data.events
      .filter((event) => event.event_type === 'error' || event.event_type === 'hit' || event.event_type === 'move')
      .forEach((event) => {
        const screen = event.payload?.screen;
        if (!screen) return;
        const x = screen.x * heatmap.width;
        const y = screen.y * heatmap.height;
        ctx.beginPath();
        ctx.arc(x, y, event.event_type === 'hit' ? 6 : 3, 0, Math.PI * 2);
        ctx.fill();
      });

    const scoreChart = document.getElementById('scoreChart');
    if (scoreChart) {
      new Chart(scoreChart, {
        type: 'radar',
        data: {
          labels: ['Precisión', 'Eficiencia', 'Seguridad', 'Adherencia', 'Instrumental'],
          datasets: [
            {
              label: 'Subscores',
              data: [
                attempt.subscores.precision,
                attempt.subscores.efficiency,
                attempt.subscores.safety,
                attempt.subscores.protocol_adherence,
                attempt.subscores.instrument_handling,
              ],
              backgroundColor: 'rgba(37, 99, 235, 0.2)',
              borderColor: '#2563eb',
            },
          ],
        },
        options: { scales: { r: { beginAtZero: true, max: 100 } } },
      });
    }

    const timelineChart = document.getElementById('timelineChart');
    if (timelineChart) {
      const counts = data.events.reduce((acc, event) => {
        acc[event.event_type] = (acc[event.event_type] || 0) + 1;
        return acc;
      }, {});
      new Chart(timelineChart, {
        type: 'bar',
        data: {
          labels: Object.keys(counts),
          datasets: [{ label: 'Eventos', data: Object.values(counts), backgroundColor: '#0ea5e9' }],
        },
      });
    }

    const stepChecklist = document.getElementById('stepChecklist');
    const completedSteps = data.events
      .filter((event) => event.event_type === 'step_completed')
      .map((event) => event.payload.step_id);
    stepChecklist.innerHTML = (attempt.procedure_detail?.steps || [])
      .map((step) => {
        const checked = completedSteps.includes(step.id) ? '✅' : '⬜';
        return `<li>${checked} ${step.title}</li>`;
      })
      .join('');

    document.getElementById('downloadPdf').addEventListener('click', () => {
      window.open(`${apiBase}/reports/${attemptId}/pdf/`, '_blank');
    });
  };

  const loadInstructorPanel = async () => {
    const me = await loadShell();
    if (!me) return;
    const proceduresResponse = await apiFetch(`${apiBase}/admin/procedures/`);
    const procedures = proceduresResponse.ok ? await proceduresResponse.json() : [];
    const container = document.getElementById('procedureManager');

    const renderProcedures = () => {
      container.innerHTML = `
        <form id="procedureForm" class="mb-3">
          <div class="row g-2">
            <div class="col-md-6"><input class="form-control" name="name" placeholder="Nombre" required></div>
            <div class="col-md-6"><input class="form-control" name="specialty" placeholder="Especialidad" required></div>
            <div class="col-12"><textarea class="form-control" name="description" placeholder="Descripción" required></textarea></div>
          </div>
          <button class="btn btn-primary mt-2" type="submit">Crear procedimiento</button>
        </form>
        <div>${procedures
          .map(
            (proc) => `
            <div class="border rounded p-3 mb-2">
              <div class="fw-semibold">${proc.name}</div>
              <div class="small text-muted">${proc.specialty} · ${proc.difficulty}</div>
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
        difficulty: 'Intermedia',
        procedure_type: 'Abierta',
        duration_estimated_minutes: 30,
        steps: [
          { id: 1, title: 'Paso inicial', objectives: 'Preparación', risks: [], tips: [], instruments: ['Bisturí'], actions: ['CUT'] },
          { id: 2, title: 'Paso técnico', objectives: 'Control', risks: [], tips: [], instruments: ['Pinza'], actions: ['GRAB'] },
        ],
        instruments: [
          { name: 'Bisturí', tool: 'SCALPEL' },
          { name: 'Pinza', tool: 'FORCEPS' },
          { name: 'Porta-agujas', tool: 'NEEDLE_DRIVER' },
          { name: 'Cauterio', tool: 'CAUTERY' },
        ],
        zones: { target: { x: 0.3, y: 1.2, z: 0.4, radius: 0.35 }, forbidden: { x: -0.4, y: 1.1, z: 0.2, radius: 0.3 } },
        checklist: [{ code: 'STERILE', label: 'Campo estéril' }],
        rubric: {
          version: 'rules_v2',
          expected_time_seconds: 240,
          penalties: {
            forbidden_hit: 8,
            wrong_action: 5,
            step_omitted: 6,
            time_over: 1,
            wrong_instrument: 4,
            erratic_move: 1,
          },
        },
        prompt_base: 'Guía clínica estándar para instructores.',
        is_playable: false,
      };
      const response = await apiFetch(`${apiBase}/admin/procedures/`, {
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
        const response = await apiFetch(`${apiBase}/admin/procedures/${id}/`, { method: 'DELETE' });
        if (response.ok || response.status === 204) {
          const index = procedures.findIndex((proc) => String(proc.id) === id);
          if (index > -1) {
            procedures.splice(index, 1);
            renderProcedures();
          }
        }
      }
    });

    const analyticsResponse = await apiFetch(`${apiBase}/admin/analytics/`);
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

    const rankingContainer = document.getElementById('ranking');
    rankingContainer.innerHTML = analytics
      .slice(0, 5)
      .map((item, index) => `<div>${index + 1}. ${item.procedure__name}</div>`)
      .join('');

    const exportBtn = document.getElementById('exportCsvBtn');
    exportBtn.addEventListener('click', () => {
      window.open(`${apiBase}/admin/export/csv/`, '_blank');
    });

    const adminExport = document.getElementById('exportCsvAdmin');
    if (adminExport) {
      adminExport.addEventListener('click', () => {
        window.open(`${apiBase}/admin/export/csv/`, '_blank');
      });
    }
  };

  const loadAdminPanel = async () => {
    await loadShell();
    const adminExport = document.getElementById('exportCsvAdmin');
    if (adminExport) {
      adminExport.addEventListener('click', () => {
        window.open(`${apiBase}/admin/export/csv/`, '_blank');
      });
    }
  };

  return {
    initAuth,
    loadDashboard,
    startSimulator,
    loadReport,
    loadInstructorPanel,
    loadAdminPanel,
  };
})();

window.App = App;
