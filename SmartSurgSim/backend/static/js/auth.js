const API_BASE = '/api';

function saveTokens(data) {
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
}

function getAccessToken() {
    return localStorage.getItem('access');
}

function logout() {
    localStorage.clear();
    window.location.href = '/';
}

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!response.ok) {
        alert('Credenciales inválidas');
        return;
    }
    const data = await response.json();
    saveTokens(data);
    await loadCurrentUser();
    redirectByRole();
}

async function loadCurrentUser() {
    const response = await apiFetch(`${API_BASE}/auth/me`);
    if (response) {
        localStorage.setItem('role', response.role);
        localStorage.setItem('username', response.username);
    }
}

function redirectByRole() {
    const role = localStorage.getItem('role');
    if (role === 'INSTRUCTOR' || role === 'ADMIN') {
        window.location.href = '/app/instructor/dashboard';
        return;
    }
    window.location.href = '/app/student/dashboard';
}

function requireAuth(requiredRole) {
    const token = getAccessToken();
    if (!token) {
        window.location.href = '/';
        return;
    }
    if (requiredRole) {
        const role = localStorage.getItem('role');
        if (!role) {
            loadCurrentUser();
            return;
        }
        if (requiredRole === 'INSTRUCTOR' && role === 'STUDENT') {
            alert('Acceso restringido.');
            window.location.href = '/app/student/dashboard';
        }
    }
}

async function apiFetch(url, options = {}) {
    const token = getAccessToken();
    const headers = options.headers || {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        logout();
        return null;
    }
    if (response.headers.get('content-type')?.includes('application/json')) {
        return await response.json();
    }
    return response;
}

async function loadStudentDashboard() {
    const procedures = await apiFetch(`${API_BASE}/procedures`);
    const attempts = await apiFetch(`${API_BASE}/attempts/me`);
    const list = document.getElementById('procedure-list');
    list.innerHTML = '';
    procedures.forEach(proc => {
        const card = document.createElement('div');
        card.className = 'col-md-6';
        card.innerHTML = `
            <div class="card shadow-sm">
                <div class="card-body">
                    <h5>${proc.title}</h5>
                    <p class="small text-muted">${proc.description}</p>
                    <button class="btn btn-primary btn-sm" onclick="startAttempt(${proc.id})">Iniciar</button>
                </div>
            </div>
        `;
        list.appendChild(card);
    });
    const attemptList = document.getElementById('attempt-list');
    attemptList.innerHTML = '';
    attempts.forEach(att => {
        const item = document.createElement('li');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        item.innerHTML = `<span>${att.procedure_title || att.procedure}</span><a href="/app/student/attempts/${att.id}" class="btn btn-sm btn-outline-primary">Ver</a>`;
        attemptList.appendChild(item);
    });
}

async function startAttempt(procedureId) {
    const response = await apiFetch(`${API_BASE}/attempts/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ procedure_id: procedureId })
    });
    window.location.href = `/app/student/procedures/${procedureId}/simulate?attempt_id=${response.attempt_id}`;
}

async function loadInstructorProcedures() {
    const procedures = await apiFetch(`${API_BASE}/procedures`);
    const list = document.getElementById('procedure-admin-list');
    list.innerHTML = '';
    procedures.forEach(proc => {
        const item = document.createElement('a');
        item.className = 'list-group-item list-group-item-action';
        item.href = `/app/instructor/procedures/${proc.id}/edit`;
        item.textContent = proc.title;
        list.appendChild(item);
    });
}

async function createProcedure() {
    const title = document.getElementById('proc-title').value;
    const description = document.getElementById('proc-description').value;
    const difficulty = document.getElementById('proc-difficulty').value;
    await apiFetch(`${API_BASE}/admin/procedures`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title,
            description,
            difficulty,
            steps: [],
            rubric: {},
            zones: {},
            instruments: []
        })
    });
    loadInstructorProcedures();
}

async function updateProcedure(id) {
    const payload = {
        id,
        title: document.getElementById('edit-title').value,
        description: document.getElementById('edit-description').value,
        difficulty: document.getElementById('edit-difficulty').value,
        steps: JSON.parse(document.getElementById('edit-steps').value || '[]'),
        zones: JSON.parse(document.getElementById('edit-zones').value || '{}'),
        rubric: JSON.parse(document.getElementById('edit-rubric').value || '{}'),
    };
    await apiFetch(`${API_BASE}/admin/procedures`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    alert('Guardado');
}

async function deleteProcedure(id) {
    await apiFetch(`${API_BASE}/admin/procedures`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    });
    window.location.href = '/app/instructor/procedures';
}

async function loadAnalytics() {
    const data = await apiFetch(`${API_BASE}/admin/analytics`);
    const tbody = document.querySelector('#avg-table tbody');
    tbody.innerHTML = '';
    data.procedure_stats.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${item.procedure__title}</td><td>${Math.round(item.avg_score || 0)}</td><td>${item.total_attempts}</td>`;
        tbody.appendChild(row);
    });
    const errorList = document.getElementById('error-list');
    errorList.innerHTML = '';
    data.error_counts.forEach(err => {
        const li = document.createElement('li');
        li.textContent = JSON.stringify(err.payload);
        errorList.appendChild(li);
    });
    drawTrendChart();
}

function drawTrendChart() {
    const canvas = document.getElementById('trend-chart');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#0d6efd';
    ctx.beginPath();
    const points = [60, 62, 70, 65, 75, 80, 82];
    points.forEach((value, index) => {
        const x = (index / (points.length - 1)) * (canvas.width - 40) + 20;
        const y = canvas.height - (value / 100) * (canvas.height - 40) - 20;
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
}
