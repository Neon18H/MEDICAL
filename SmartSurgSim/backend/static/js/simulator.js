let simState = {
    attemptId: null,
    startTime: null,
    socket: null,
    errors: 0,
    events: [],
    procedure: null,
    currentStep: 0,
    hits: [],
};

function initSimulator(procedure) {
    simState.procedure = procedure;
    const params = new URLSearchParams(window.location.search);
    simState.attemptId = params.get('attempt_id');
    simState.startTime = performance.now();
    renderSteps();
    setupCanvas();
    setupSocket();
    setupControls();
    tickTimer();
}

function renderSteps() {
    const steps = simState.procedure.steps || [];
    const list = document.getElementById('step-list');
    const checklist = document.getElementById('checklist');
    list.innerHTML = '';
    checklist.innerHTML = '';
    steps.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step.label || step.action;
        list.appendChild(li);
        const check = document.createElement('li');
        check.textContent = step.label || step.action;
        checklist.appendChild(check);
    });
}

function setupCanvas() {
    const canvas = document.getElementById('sim-canvas');
    const ctx = canvas.getContext('2d');
    canvas.addEventListener('mousemove', (event) => {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        drawScene(ctx, x, y);
        sendEvent('move', { x, y });
        detectZones(x, y);
    });
    drawScene(ctx, 0, 0);
}

function drawScene(ctx, x, y) {
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawZones(ctx);
    ctx.strokeStyle = '#0d6efd';
    ctx.beginPath();
    ctx.moveTo(x - 10, y);
    ctx.lineTo(x + 10, y);
    ctx.moveTo(x, y - 10);
    ctx.lineTo(x, y + 10);
    ctx.stroke();
}

function drawZones(ctx) {
    const zones = simState.procedure.zones || {};
    if (zones.objective) {
        drawZone(ctx, zones.objective, 'rgba(25,135,84,0.3)');
    }
    if (zones.prohibited) {
        drawZone(ctx, zones.prohibited, 'rgba(220,53,69,0.3)');
    }
}

function drawZone(ctx, zone, color) {
    ctx.fillStyle = color;
    if (zone.shape === 'circle') {
        ctx.beginPath();
        ctx.arc(zone.x, zone.y, zone.radius, 0, Math.PI * 2);
        ctx.fill();
    } else {
        ctx.fillRect(zone.x, zone.y, zone.width, zone.height);
    }
}

function detectZones(x, y) {
    const zones = simState.procedure.zones || {};
    if (zones.prohibited && isInsideZone(x, y, zones.prohibited)) {
        registerError('Zona prohibida');
        sendEvent('hit', { zone: 'prohibited', x, y });
    }
    if (zones.objective && isInsideZone(x, y, zones.objective)) {
        sendEvent('hit', { zone: 'objective', x, y });
        simState.hits.push({ x, y });
        completeMoveStep();
    }
}

function completeMoveStep() {
    const steps = simState.procedure.steps || [];
    if (simState.currentStep >= steps.length) return;
    const step = steps[simState.currentStep];
    if (step.action === 'MOVE') {
        simState.currentStep += 1;
        document.getElementById('progress').textContent = `${Math.round((simState.currentStep / steps.length) * 100)}%`;
        sendEvent('step_completed', { step_id: step.id });
    }
}

function isInsideZone(x, y, zone) {
    if (zone.shape === 'circle') {
        const dx = x - zone.x;
        const dy = y - zone.y;
        return Math.sqrt(dx * dx + dy * dy) <= zone.radius;
    }
    return x >= zone.x && x <= zone.x + zone.width && y >= zone.y && y <= zone.y + zone.height;
}

function setupControls() {
    document.addEventListener('keydown', (event) => {
        if (event.key.toLowerCase() === 'c') sendAction('CUT');
        if (event.key.toLowerCase() === 's') sendAction('SUTURE');
        if (event.key.toLowerCase() === 'g') sendAction('GRAB');
        if (event.key.toLowerCase() === 'r') sendAction('RELEASE');
    });
}

function sendAction(name) {
    sendEvent('action', { name });
    completeStepIfMatches(name);
}

function completeStepIfMatches(action) {
    const steps = simState.procedure.steps || [];
    if (simState.currentStep >= steps.length) return;
    const step = steps[simState.currentStep];
    if (step.action === action) {
        simState.currentStep += 1;
        document.getElementById('progress').textContent = `${Math.round((simState.currentStep / steps.length) * 100)}%`;
        sendEvent('step_completed', { step_id: step.id });
    } else {
        registerError('Acción incorrecta');
        sendEvent('error', { code: 'action_mismatch' });
    }
}

function registerError(message) {
    simState.errors += 1;
    document.getElementById('error-count').textContent = simState.errors;
    const list = document.getElementById('error-list');
    const item = document.createElement('li');
    item.textContent = message;
    list.appendChild(item);
}

function setupSocket() {
    if (!simState.attemptId) return;
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws/attempts/${simState.attemptId}/`;
    simState.socket = new WebSocket(wsUrl);
    simState.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'warning') {
            registerError(data.message);
        }
    };
    simState.socket.onerror = () => {
        console.warn('WebSocket error, fallback to REST');
    };
}

function sendEvent(type, payload) {
    const t_ms = Math.floor(performance.now() - simState.startTime);
    const event = { t_ms, type, payload };
    simState.events.push(event);
    if (simState.socket && simState.socket.readyState === WebSocket.OPEN) {
        simState.socket.send(JSON.stringify(event));
    } else {
        apiFetch(`/api/attempts/${simState.attemptId}/event`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(event)
        });
    }
}

function tickTimer() {
    const elapsed = Math.floor((performance.now() - simState.startTime) / 1000);
    document.getElementById('timer').textContent = elapsed;
    requestAnimationFrame(tickTimer);
}

async function finishAttempt() {
    const duration_ms = Math.floor(performance.now() - simState.startTime);
    const result = await apiFetch(`/api/attempts/${simState.attemptId}/finish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_ms })
    });
    window.location.href = `/app/student/attempts/${simState.attemptId}`;
}

function renderHeatmap(events) {
    const canvas = document.getElementById('heatmap');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    events.forEach(event => {
        if (event.event_type === 'hit' && event.payload) {
            const x = event.payload.x || 0;
            const y = event.payload.y || 0;
            ctx.fillStyle = event.payload.zone === 'prohibited' ? 'rgba(220,53,69,0.4)' : 'rgba(25,135,84,0.4)';
            ctx.beginPath();
            ctx.arc(x, y, 8, 0, Math.PI * 2);
            ctx.fill();
        }
    });
}
