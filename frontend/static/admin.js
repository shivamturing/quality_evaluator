/**
 * RLToolUseEval Admin Dashboard
 */

const adminSummary = document.getElementById('admin-summary');
const adminTable = document.getElementById('admin-table');
const adminGrouped = document.getElementById('admin-grouped');
const refreshAdminBtn = document.getElementById('refresh-admin-btn');
const downloadAdminJsonBtn = document.getElementById('download-admin-json-btn');

document.addEventListener('DOMContentLoaded', initAdmin);

function initAdmin() {
    if (refreshAdminBtn) {
        refreshAdminBtn.addEventListener('click', loadAdminResults);
    }
    if (downloadAdminJsonBtn) {
        downloadAdminJsonBtn.addEventListener('click', downloadAdminJson);
    }
    loadAdminResults();
}

async function loadAdminResults() {
    if (!adminTable || !adminSummary) return;
    adminSummary.textContent = 'Loading...';
    adminTable.innerHTML = '';

    try {
        const res = await apiFetch('/api/admin/results');
        if (!res.ok) {
            adminSummary.textContent = 'Unable to load results.';
            adminTable.innerHTML = '<p class="empty-state">Not authorized or no results.</p>';
            return;
        }
        const data = await res.json();
        const results = Array.isArray(data.results) ? data.results : [];
        renderAdminResults(results);
    } catch (e) {
        adminSummary.textContent = 'Error loading results.';
        adminTable.innerHTML = '<p class="empty-state">Unable to load results.</p>';
    }
}

function renderAdminResults(results) {
    if (!results || results.length === 0) {
        adminSummary.textContent = 'No evaluations yet';
        adminTable.innerHTML = '<p class="empty-state">No evaluations found.</p>';
        if (adminGrouped) {
            adminGrouped.innerHTML = '';
        }
        return;
    }

    adminSummary.textContent = `${results.length} evaluations recorded`;

    if (adminGrouped) {
        adminGrouped.innerHTML = renderGroupedByReviewer(results);
    }

    const rows = results.map(result => {
        const taskId = escapeHtml(String(result.task_id || 'Unknown'));
        const reviewer = escapeHtml(String(result.reviewer_email || 'Unknown'));
        const reviewedAt = formatDate(result.reviewed_at);
        const flagsCount = (result.detected_flags || []).length;

        return `
            <tr>
                <td>${taskId}</td>
                <td>${reviewer}</td>
                <td>${reviewedAt}</td>
                <td>${flagsCount}</td>
            </tr>
        `;
    }).join('');

    adminTable.innerHTML = `
        <div class="admin-table-wrapper">
            <table class="admin-results-table">
                <thead>
                    <tr>
                        <th>Task ID</th>
                        <th>Reviewer Email</th>
                        <th>Reviewed At</th>
                        <th>Flags</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

function renderGroupedByReviewer(results) {
    const grouped = results.reduce((acc, item) => {
        const reviewer = (item.reviewer_email || 'Unknown').trim() || 'Unknown';
        if (!acc[reviewer]) acc[reviewer] = [];
        acc[reviewer].push(item);
        return acc;
    }, {});

    const groups = Object.entries(grouped)
        .sort((a, b) => b[1].length - a[1].length)
        .map(([reviewer, items]) => {
            const count = items.length;
            const taskItems = items.map(item => {
                const taskId = escapeHtml(String(item.task_id || 'Unknown'));
                const reviewedAt = formatDate(item.reviewed_at);
                return `<li><span class="task-id-chip">${taskId}</span><span class="task-date">${reviewedAt}</span></li>`;
            }).join('');

            return `
                <details class="reviewer-group">
                    <summary>
                        <span class="reviewer-name">${escapeHtml(reviewer)}</span>
                        <span class="reviewer-count">${count} tasks</span>
                    </summary>
                    <ul class="reviewer-task-list">
                        ${taskItems}
                    </ul>
                </details>
            `;
        }).join('');

    return `
        <div class="admin-grouped-card">
            <div class="section-title">Reviewer summary</div>
            ${groups}
        </div>
    `;
}

function downloadAdminJson() {
    window.location.href = '/api/download/json';
}

function formatDate(value) {
    if (!value) return 'Unknown';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Unknown';
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function apiFetch(url, options = {}) {
    const headers = { ...(options.headers || {}), 'ngrok-skip-browser-warning': '1' };
    return fetch(url, { ...options, headers });
}
