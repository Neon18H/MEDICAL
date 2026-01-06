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
    const response = await fetch(`${authBase}/refresh/`, {
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

  const loadShell = async () => {
    const meResponse = await apiFetch(`${authBase}/me/`);
    if (!meResponse.ok) {
      window.location.href = '/';
      return null;
    }
    const me = await meResponse.json();
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
      logoutBtn.addEventListener('click', () => {
        clearTokens();
        window.location.href = '/';
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
      form.provider.value = settings.provider || 'OPENAI';
      form.model_name.value = settings.model_name || 'gpt-4o-mini';
      form.use_ai.checked = settings.use_ai || false;
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
    const me = await loadShell();
    if (!me) return;

    const procedureResponse = await apiFetch(`${apiBase}/procedures/${procedureId}/`);
    if (!procedureResponse.ok) {
      window.location.href = '/dashboard/';
      return;
    }
    const procedure = await procedureResponse.json();

    const attemptResponse = await apiFetch(`${apiBase}/attempts/start/`, {
      method: 'POST',
      body: JSON.stringify({ procedure: procedureId }),
    });
    if (!attemptResponse.ok) {
      window.location.href = '/dashboard/';
      return;
    }
    const attempt = await attemptResponse.json();

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
    const stepRisks = document.getElementById('stepRisks');
    const stepTips = document.getElementById('stepTips');
    const currentStepLabel = document.getElementById('currentStepLabel');
    const errorCountEl = document.getElementById('errorCount');
    const progressLabel = document.getElementById('progressLabel');

    let stepIndex = 0;
    let errors = [];
    let startTime = Date.now();
    let socket;
    let socketOpen = false;
    let selectedTool = instruments[0]?.tool || 'SCALPEL';

    const updateStepPanel = () => {
      const step = procedure.steps[stepIndex];
      document.querySelectorAll('.step-item').forEach((el) => {
        const index = Number(el.dataset.stepIndex);
        el.classList.toggle('active', index === stepIndex);
      });
      if (!step) return;
      currentStepLabel.textContent = step.title;
      stepObjective.textContent = step.objectives || 'Controlar la zona quirúrgica.';
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
        await sendEvent('tool_select', { tool: selectedTool });
      });
    });
    document.querySelector('.instrument-btn')?.classList.add('active');

    document.querySelectorAll('.action-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const action = btn.getAttribute('data-action');
        const intensity = Number(document.getElementById('intensitySlider').value);
        await sendEvent('action', { type: action, intensity, tool: selectedTool, duration: 500 });
        const step = procedure.steps[stepIndex];
        if (step && step.actions?.includes(action)) {
          await sendEvent('step_completed', { step_id: step.id });
          stepIndex = Math.min(stepIndex + 1, procedure.steps.length);
          updateStepPanel();
        }
      });
    });

    document.getElementById('finishAttempt').addEventListener('click', async () => {
      const durationSeconds = Math.floor((Date.now() - startTime) / 1000);
      await apiFetch(`${apiBase}/attempts/${attempt.id}/finish/`, {
        method: 'POST',
        body: JSON.stringify({ duration_seconds: durationSeconds }),
      });
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
      const height = 420;
      const scene = new THREE.Scene();
      scene.background = new THREE.Color('#0f172a');
      const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
      camera.position.set(0, 2.2, 4.2);

      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(width, height);
      renderer.shadowMap.enabled = true;
      container.appendChild(renderer.domElement);

      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;

      const ambient = new THREE.AmbientLight(0xffffff, 0.5);
      scene.add(ambient);
      const spot = new THREE.DirectionalLight(0xffffff, 1);
      spot.position.set(3, 5, 2);
      spot.castShadow = true;
      scene.add(spot);

      const torsoGeometry = new THREE.CapsuleGeometry(0.9, 1.6, 8, 16);
      const torsoMaterial = new THREE.MeshStandardMaterial({ color: '#cbd5f5', roughness: 0.4 });
      const torso = new THREE.Mesh(torsoGeometry, torsoMaterial);
      torso.castShadow = true;
      torso.receiveShadow = true;
      torso.position.y = 1.0;
      scene.add(torso);

      const target = procedure.zones?.target || { x: 0.3, y: 1.2, z: 0.4, radius: 0.35 };
      const forbidden = procedure.zones?.forbidden || { x: -0.4, y: 1.1, z: 0.2, radius: 0.3 };

      const organ = new THREE.Mesh(
        new THREE.SphereGeometry(target.radius, 24, 24),
        new THREE.MeshStandardMaterial({ color: '#22c55e', emissive: '#16a34a', opacity: 0.9, transparent: true })
      );
      organ.position.set(target.x, target.y, target.z);
      scene.add(organ);

      const danger = new THREE.Mesh(
        new THREE.SphereGeometry(forbidden.radius, 24, 24),
        new THREE.MeshStandardMaterial({ color: '#ef4444', opacity: 0.35, transparent: true })
      );
      danger.position.set(forbidden.x, forbidden.y, forbidden.z);
      scene.add(danger);

      const instrument = new THREE.Mesh(
        new THREE.CylinderGeometry(0.04, 0.04, 0.8, 12),
        new THREE.MeshStandardMaterial({ color: '#38bdf8' })
      );
      instrument.position.set(0, 1.2, 1.2);
      instrument.rotation.z = Math.PI / 2;
      scene.add(instrument);

      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      let lastMove = 0;
      let lastZoneHit = null;

      const onPointerMove = (event) => {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObject(torso, true);
        if (intersects.length) {
          const point = intersects[0].point;
          instrument.position.copy(point);
          const now = Date.now();
          if (now - lastMove > 80) {
            sendEvent('move', { x: point.x, y: point.y, z: point.z, hitObject: 'torso', tool: selectedTool });
            lastMove = now;
          }
          const distTarget = instrument.position.distanceTo(organ.position);
          const distForbidden = instrument.position.distanceTo(danger.position);
          if (distForbidden < forbidden.radius) {
            if (lastZoneHit !== 'forbidden') {
              sendEvent('hit', { zone: 'forbidden', x: point.x, y: point.y, z: point.z, severity: 'high' });
              addError('Contacto con zona prohibida');
              sendEvent('error', { code: 'FORBIDDEN_ZONE', x: point.x, y: point.y, z: point.z });
            }
            lastZoneHit = 'forbidden';
          } else if (distTarget < target.radius) {
            if (lastZoneHit !== 'target') {
              sendEvent('hit', { zone: 'target', x: point.x, y: point.y, z: point.z, severity: 'low' });
            }
            lastZoneHit = 'target';
          } else {
            lastZoneHit = null;
          }
        }
      };

      renderer.domElement.addEventListener('pointermove', onPointerMove);

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
    `;

    const timeline = document.getElementById('timeline');
    timeline.innerHTML = data.events
      .slice(0, 50)
      .map((event) => `<li class="timeline-item">${event.event_type} - ${event.timestamp_ms}ms</li>`)
      .join('');

    const heatmap = document.getElementById('heatmap');
    const ctx = heatmap.getContext('2d');
    ctx.clearRect(0, 0, heatmap.width, heatmap.height);
    ctx.fillStyle = '#f87171';
    data.events
      .filter((event) => event.event_type === 'error' || event.event_type === 'hit')
      .forEach((event) => {
        const { x, y } = event.payload || { x: Math.random() * 320, y: Math.random() * 220 };
        ctx.beginPath();
        ctx.arc(x || Math.random() * 320, y || Math.random() * 220, 6, 0, Math.PI * 2);
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
