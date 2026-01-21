/**
 * RLToolUseEval Frontend Application
 * Handles file upload, API communication, and results rendering with KPI display
 */

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const resultsSection = document.getElementById('results-section');

const reviewerEmailInput = document.getElementById('reviewer-email');
const reviewerEmailGroup = document.getElementById('reviewer-email-group');
const reviewerEmailError = document.getElementById('reviewer-email-error');
const reviewerEmailSaved = document.getElementById('reviewer-email-saved');
const reviewerEmailSavedText = document.getElementById('reviewer-email-saved-text');
const saveEmailBtn = document.getElementById('save-email-btn');
const changeEmailBtn = document.getElementById('change-email-btn');
const emailModal = document.getElementById('email-modal');
const modalEmailInput = document.getElementById('modal-email-input');
const modalEmailError = document.getElementById('modal-email-error');
const modalSaveEmailBtn = document.getElementById('modal-save-email-btn');
const taskIdInput = document.getElementById('task-id-input');
const taskIdError = document.getElementById('task-id-error');
const fetchTaskBtn = document.getElementById('fetch-task-btn');
const taskPreview = document.getElementById('task-preview');
const taskPreviewBody = document.getElementById('task-preview-body');
const evaluateBtn = document.getElementById('evaluate-btn');
const progress = document.getElementById('progress');

const scoreSummary = document.getElementById('score-summary');
const flagsSection = document.getElementById('flags-section');
const flagsList = document.getElementById('flags-list');
const dimensionsGrid = document.getElementById('dimensions-grid');
const taskIdDisplay = document.getElementById('task-id-display');
const reviewerEmailDisplay = document.getElementById('reviewer-email-display');

const downloadJsonBtn = document.getElementById('download-json-btn');
const downloadCsvBtn = document.getElementById('download-csv-btn');
const newEvalBtn = document.getElementById('new-eval-btn');

// State
let currentResults = null;
let currentTaskData = null;
let isEvaluating = false;
const REVIEWER_EMAIL_KEY = 'rltooluseeval_reviewer_email';
const REVIEWER_EMAIL_DOMAIN = '@turing.com';

// Quality Dimensions (in display order)
const DIMENSION_ORDER = [
    'Prompt Quality',
    'Manual Tool Execution (Happy Path)',
    'SQL Verifier Quality',
    'Model Benchmarking Analysis'
];

const DIMENSION_SHORT_NAMES = {
    'Prompt Quality': 'Prompt',
    'Manual Tool Execution (Happy Path)': 'Happy Path',
    'SQL Verifier Quality': 'SQL Verifier',
    'Model Benchmarking Analysis': 'Benchmarking'
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupEventListeners();
    checkHealth();
    fetchEnvironments();
    const savedEmail = loadReviewerEmail();
    updateReviewerEmailUI(savedEmail);
    if (!savedEmail) {
        openEmailModal();
    }
}

async function fetchEnvironments() {
    const select = document.getElementById('domain-select');
    try {
        const res = await apiFetch('/api/environments');
        const data = await res.json();

        if (data.environments && data.environments.length > 0) {
            data.environments.forEach(env => {
                const option = document.createElement('option');
                option.value = env;
                option.textContent = env.charAt(0).toUpperCase() + env.slice(1); // Capitalize
                select.appendChild(option);
            });
        }
    } catch (e) {
        console.error("Failed to load environments", e);
    }
}

function setupEventListeners() {
    taskIdInput.addEventListener('input', clearTaskIdError);
    fetchTaskBtn.addEventListener('click', handleFetchTask);

    // Form submit
    document.getElementById('upload-form').addEventListener('submit', handleEvaluate);

    // Buttons
    downloadJsonBtn.addEventListener('click', handleDownloadJson);
    downloadCsvBtn.addEventListener('click', handleDownloadCsv);
    newEvalBtn.addEventListener('click', resetToUpload);

    reviewerEmailInput.addEventListener('input', clearReviewerEmailError);
    saveEmailBtn.addEventListener('click', handleSaveEmailClick);
    changeEmailBtn.addEventListener('click', () => openEmailModal(reviewerEmailInput.value.trim()));
    modalEmailInput.addEventListener('input', clearModalEmailError);
    modalSaveEmailBtn.addEventListener('click', handleModalSaveEmail);
}

// Health Check
async function checkHealth() {
    const badge = document.getElementById('health-status');
    if (!badge) {
        return;
    }
    try {
        const res = await apiFetch('/api/health');
        const data = await res.json();

        if (data.status === 'healthy' && data.api_configured) {
            badge.textContent = `✓ ${data.provider.toUpperCase()} Ready`;
            badge.className = 'status-badge healthy';
        } else {
            badge.textContent = '⚠ API Key Not Set';
            badge.className = 'status-badge error';
        }
    } catch (e) {
        badge.textContent = '✗ Server Error';
        badge.className = 'status-badge error';
    }
}

// Evaluation
async function handleEvaluate(e) {
    e.preventDefault();

    const taskId = taskIdInput.value.trim();
    const reviewerEmail = getReviewerEmail();

    if (!taskId) {
        showTaskIdError('Please enter a task ID');
        return;
    }
    if (!reviewerEmail) {
        openEmailModal();
        return;
    }
    persistReviewerEmail(reviewerEmail);

    // Show progress
    isEvaluating = true;
    updateEvaluateButtonState();
    progress.classList.remove('hidden');
    document.querySelector('.progress-text').textContent = 'Evaluating 4 dimensions...';

    try {
        const domain = document.getElementById('domain-select').value;
        const res = await apiFetch('/api/evaluate_task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: taskId,
                reviewer_email: reviewerEmail,
                domain: domain || null
            })
        });

        const data = await res.json();

        if (res.ok) {
            currentResults = data;
            displayResults(data);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (e) {
        alert(`Error: ${e.message}`);
    } finally {
        isEvaluating = false;
        updateEvaluateButtonState();
        progress.classList.add('hidden');
    }
}

// Display Results
function displayResults(data) {
    // Show results section
    uploadSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    // Task Info
    taskIdDisplay.textContent = `Task ID: ${data.task_id || 'Unknown'}`;
    reviewerEmailDisplay.textContent = data.reviewer_email ? `Reviewer: ${data.reviewer_email}` : '';

    // Render KPI Score Summary
    renderScoreSummary(data.evaluation_results || {});

    // Flags
    if (data.detected_flags && data.detected_flags.length > 0) {
        flagsSection.classList.remove('hidden');
        flagsList.innerHTML = data.detected_flags.map(f => `
            <div class="flag-item">
                <strong>${formatFlagType(f.flag_type)}:</strong> 
                ${Array.isArray(f.details) ? f.details.join(', ') : JSON.stringify(f.details)}
            </div>
        `).join('');
    } else {
        flagsSection.classList.add('hidden');
    }

    // Dimension Details
    renderDimensionResults(data.evaluation_results || {});

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// KPI Score Summary
function renderScoreSummary(results) {
    scoreSummary.innerHTML = DIMENSION_ORDER
        .map(name => {
            const result = results[name];
            const response = result ? (result.response || result) : null;
            const score = extractScore(response);
            const scoreClass = getScoreClass(score);
            const scoreStyle = getScoreStyle(score);
            const shortName = DIMENSION_SHORT_NAMES[name] || name;

            return `
                <div class="score-card">
                    <div class="score-value ${scoreClass}" ${scoreStyle}>${formatScore(score)}</div>
                    <div class="score-label">${shortName}</div>
                </div>
            `;
        }).join('');
}

// Dimension Results
function renderDimensionResults(results) {
    dimensionsGrid.innerHTML = DIMENSION_ORDER
        .filter(name => results[name])
        .map(name => {
            const result = results[name];
            const response = result.response || result;
            const score = extractScore(response);
            const scoreClass = getScoreClass(score);
            const scoreStyle = getScoreStyle(score);
            const parsed = parseResponseJSON(response);
            const contentHtml = parsed
                ? renderEvaluationView(parsed, response)
                : `<div class="dimension-response">${escapeHtml(String(response || ''))}</div>`;

            return `
                <div class="dimension-card">
                    <div class="dimension-header" onclick="toggleDimension(this)">
                        <div class="dimension-info">
                            <span class="dimension-score ${scoreClass}" ${scoreStyle}>${formatScore(score)}</span>
                            <span class="dimension-name">${name}</span>
                        </div>
                        <div class="dimension-toggle">▼</div>
                    </div>
                    <div class="dimension-content">
                        ${contentHtml}
                    </div>
                </div>
            `;
        }).join('');
}

// Score Extraction (from LLM JSON response)
function extractScore(response) {
    if (!response) return null;

    // Try to parse JSON from response
    const jsonMatch = response.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
        try {
            const parsed = JSON.parse(jsonMatch[1]);
            if (parsed.overall_score !== undefined) {
                return normalizeScoreValue(parsed.overall_score);
            }
            if (parsed.score !== undefined) {
                return normalizeScoreValue(parsed.score);
            }
        } catch (e) { /* continue */ }
    }

    // Try direct JSON parse
    try {
        const parsed = JSON.parse(response);
        if (parsed.overall_score !== undefined) {
            return normalizeScoreValue(parsed.overall_score);
        }
        if (parsed.score !== undefined) {
            return normalizeScoreValue(parsed.score);
        }
    } catch (e) { /* continue */ }

    // Check for pass/fail keywords
    const lower = response.toLowerCase();
    if (lower.includes('"overall_score": "pass"') || lower.includes('"overall_score":"pass"')) {
        return 'PASS';
    }
    if (lower.includes('"overall_score": "fail"') || lower.includes('"overall_score":"fail"')) {
        return 'FAIL';
    }

    // Regex for numeric scores
    const patterns = [
        /"score"\s*:\s*"?(\d+(?:\.\d+)?)"?/,
        /score:\s*(\d+(?:\.\d+)?)/i
    ];

    for (const pattern of patterns) {
        const match = response.match(pattern);
        if (match) {
            return parseFloat(match[1]);
        }
    }

    return null;
}

function normalizeScoreValue(value) {
    if (value === null || value === undefined) return null;
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
        const lower = value.toLowerCase();
        if (lower === 'pass') return 'PASS';
        if (lower === 'fail') return 'FAIL';
        const parsed = parseFloat(value);
        if (!Number.isNaN(parsed)) return parsed;
    }
    return null;
}

function parseResponseJSON(response) {
    if (!response) return null;
    if (typeof response === 'object') return response;
    if (typeof response !== 'string') return null;

    const jsonMatch = response.match(/```json\s*([\s\S]*?)\s*```/);
    const raw = jsonMatch ? jsonMatch[1] : response;

    try {
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

function renderEvaluationView(data, rawResponse) {
    const overallScore = normalizeScoreValue(data.overall_score);
    const overallPass = typeof data.overall_pass === 'boolean' ? data.overall_pass : null;
    const summary = data.summary ? escapeHtml(String(data.summary)) : '';
    const flags = Array.isArray(data.flags) ? data.flags : [];

    const overallClass = getScoreClass(overallScore);
    const overallStyle = getScoreStyle(overallScore);
    const overallLabel = overallPass === null ? '' : (overallPass ? 'PASS' : 'FAIL');
    const overallBadgeClass = overallPass === null ? '' : (overallPass ? 'status-pill pass' : 'status-pill fail');

    const metricRows = Object.entries(data)
        .filter(([key, value]) => !['overall_score', 'overall_pass', 'summary', 'flags'].includes(key))
        .filter(([, value]) => value && typeof value === 'object' && !Array.isArray(value) && value.score !== undefined)
        .map(([key, value]) => {
            const score = normalizeScoreValue(value.score);
            const scoreClass = getScoreClass(score);
            const scoreStyle = getScoreStyle(score);
            const reasoning = value.reasoning ? escapeHtml(String(value.reasoning)) : '';
            const label = formatLabel(key);
            const extras = renderMetricExtras(value);

            return `
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-title">${label}</span>
                        <span class="metric-score ${scoreClass}" ${scoreStyle}>${formatScore(score)}</span>
                    </div>
                    ${reasoning ? `<div class="metric-reasoning">${reasoning}</div>` : ''}
                    ${extras}
                </div>
            `;
        }).join('');

    const flagsHtml = flags.length
        ? `<div class="evaluation-flags">
                <div class="section-title">Flags</div>
                <ul>${flags.map(flag => `<li>${escapeHtml(String(flag))}</li>`).join('')}</ul>
           </div>`
        : '';

    const rawHtml = rawResponse
        ? `<details class="raw-response">
                <summary>Raw response</summary>
                <pre>${escapeHtml(String(rawResponse))}</pre>
           </details>`
        : '';

    return `
        <div class="evaluation-view">
            <div class="evaluation-summary">
                <div class="summary-score">
                    <div class="score-value ${overallClass}" ${overallStyle}>${formatScore(overallScore)}</div>
                    ${overallLabel ? `<span class="${overallBadgeClass}">${overallLabel}</span>` : ''}
                </div>
                <div class="summary-text">${summary || 'No summary provided.'}</div>
            </div>
            ${metricRows ? `<div class="evaluation-metrics">${metricRows}</div>` : ''}
            ${flagsHtml}
            ${rawHtml}
        </div>
    `;
}

function renderMetricExtras(value) {
    let extrasHtml = '';
    if (Array.isArray(value.misclassified_runs) && value.misclassified_runs.length > 0) {
        const items = value.misclassified_runs.map(run => {
            const runId = escapeHtml(String(run.run_id ?? ''));
            const claimed = escapeHtml(String(run.claimed ?? ''));
            const actual = escapeHtml(String(run.actual ?? ''));
            const reasoning = escapeHtml(String(run.reasoning ?? ''));
            return `<li>Run ${runId}: ${claimed} → ${actual}${reasoning ? ` (${reasoning})` : ''}</li>`;
        }).join('');
        extrasHtml += `
            <div class="metric-extras">
                <div class="section-title">Misclassified runs</div>
                <ul>${items}</ul>
            </div>
        `;
    }
    if (Array.isArray(value.fake_passes_detected) && value.fake_passes_detected.length > 0) {
        const items = value.fake_passes_detected.map(item => `<li>${escapeHtml(String(item))}</li>`).join('');
        extrasHtml += `
            <div class="metric-extras">
                <div class="section-title">Fake passes detected</div>
                <ul>${items}</ul>
            </div>
        `;
    }
    return extrasHtml;
}

function formatLabel(value) {
    return value
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
}

function getScoreClass(score) {
    if (score === null) return 'score-na';
    if (score === 'PASS') return 'score-pass';
    if (score === 'FAIL') return 'score-fail';
    if (typeof score === 'number') {
        return 'score-gradient';
    }
    return 'score-na';
}

function getScoreStyle(score) {
    if (typeof score !== 'number' || Number.isNaN(score)) return '';
    const clamped = Math.max(0, Math.min(5, score));
    const hue = (clamped / 5) * 120;
    const color = `hsl(${hue}, 70%, 50%)`;
    return `style="--score-color: ${color}"`;
}

function formatScore(score) {
    if (score === null) return 'N/A';
    if (score === 'PASS') return '✓ PASS';
    if (score === 'FAIL') return '✗ FAIL';
    if (typeof score === 'number') return score.toFixed(1);
    return score;
}

function formatFlagType(type) {
    return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Download Functions
function handleDownloadJson() {
    if (!currentResults) return;

    const blob = new Blob([JSON.stringify(currentResults, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evaluation_${currentResults.task_id || 'results'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function handleDownloadCsv() {
    if (!currentResults) return;

    // Build CSV
    const headers = ['Task ID', 'Reviewed At', 'Reviewer Email', ...DIMENSION_ORDER, 'Flags'];
    const row = [
        currentResults.task_id || '',
        currentResults.reviewed_at || '',
        currentResults.reviewer_email || '',
        ...DIMENSION_ORDER.map(dim => {
            const result = currentResults.evaluation_results?.[dim];
            const score = extractScore(result?.response || result || '');
            return formatScore(score);
        }),
        (currentResults.detected_flags || []).length + ' flags'
    ];

    const csv = [headers.join(','), row.map(v => `"${v}"`).join(',')].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evaluation_${currentResults.task_id || 'results'}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Tab Navigation
function resetToUpload() {
    currentResults = null;
    currentTaskData = null;
    taskIdInput.value = '';
    if (taskPreview) {
        taskPreview.classList.add('hidden');
    }
    if (taskPreviewBody) {
        taskPreviewBody.textContent = '';
    }

    uploadSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    reviewerEmailDisplay.textContent = '';
}

// Utilities
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

function apiFetch(url, options = {}) {
    const headers = { ...(options.headers || {}), 'ngrok-skip-browser-warning': '1' };
    return fetch(url, { ...options, headers });
}

window.toggleDimension = function (header) {
    const card = header.closest('.dimension-card');
    card.classList.toggle('expanded');
};

function getReviewerEmail() {
    const inputValue = reviewerEmailInput ? reviewerEmailInput.value.trim() : '';
    if (inputValue) return inputValue;
    return loadReviewerEmail();
}

function loadReviewerEmail() {
    const saved = localStorage.getItem(REVIEWER_EMAIL_KEY);
    return saved ? saved.trim() : null;
}

function persistReviewerEmail(value) {
    const normalized = value.trim();
    localStorage.setItem(REVIEWER_EMAIL_KEY, normalized);
    if (reviewerEmailInput) reviewerEmailInput.value = normalized;
    updateReviewerEmailUI(normalized);
}

function isValidReviewerEmail(value) {
    if (!value) return false;
    return value.toLowerCase().endsWith(REVIEWER_EMAIL_DOMAIN);
}

function updateReviewerEmailUI(email) {
    const hasEmail = Boolean(email);
    if (hasEmail && reviewerEmailInput) {
        reviewerEmailInput.value = email;
    }
    if (reviewerEmailGroup && reviewerEmailSaved) {
        reviewerEmailGroup.classList.toggle('hidden', hasEmail);
        reviewerEmailSaved.classList.toggle('hidden', !hasEmail);
    }
    if (reviewerEmailSavedText) {
        reviewerEmailSavedText.textContent = hasEmail ? `Reviewer: ${email}` : '';
    }
    updateEvaluateButtonState(hasEmail);
}

function updateEvaluateButtonState(hasEmail = Boolean(getReviewerEmail())) {
    if (isEvaluating) {
        evaluateBtn.disabled = true;
        return;
    }
    evaluateBtn.disabled = !hasEmail;
}

function handleSaveEmailClick() {
    const value = reviewerEmailInput.value.trim();
    if (!isValidReviewerEmail(value)) {
        showReviewerEmailError(`Email must end with ${REVIEWER_EMAIL_DOMAIN}`);
        return;
    }
    persistReviewerEmail(value);
}

function handleModalSaveEmail() {
    const value = modalEmailInput.value.trim();
    if (!isValidReviewerEmail(value)) {
        showModalEmailError(`Email must end with ${REVIEWER_EMAIL_DOMAIN}`);
        return;
    }
    persistReviewerEmail(value);
    closeEmailModal();
}

function openEmailModal(prefill = '') {
    if (!emailModal || !modalEmailInput) return;
    modalEmailInput.value = prefill || getReviewerEmail() || '';
    clearModalEmailError();
    emailModal.classList.remove('hidden');
}

function closeEmailModal() {
    if (!emailModal) return;
    emailModal.classList.add('hidden');
}

function showReviewerEmailError(message) {
    if (!reviewerEmailError) return;
    reviewerEmailError.textContent = message;
    reviewerEmailError.classList.remove('hidden');
}

function clearReviewerEmailError() {
    if (!reviewerEmailError) return;
    reviewerEmailError.textContent = '';
    reviewerEmailError.classList.add('hidden');
}

async function handleFetchTask() {
    const taskId = taskIdInput.value.trim();
    if (!taskId) {
        showTaskIdError('Please enter a task ID');
        return;
    }
    clearTaskIdError();
    const originalLabel = fetchTaskBtn.textContent;
    fetchTaskBtn.disabled = true;
    fetchTaskBtn.classList.add('loading');
    fetchTaskBtn.textContent = 'Fetching...';

    try {
        const configRes = await apiFetch(`/api/tasks/${encodeURIComponent(taskId)}/config`);
        if (!configRes.ok) {
            const err = await safeReadError(configRes);
            showTaskIdError(err || 'Unable to fetch config');
            return;
        }
        const configData = await configRes.json();

        const resultsRes = await apiFetch(`/api/tasks/${encodeURIComponent(taskId)}/download`);
        if (!resultsRes.ok) {
            const err = await safeReadError(resultsRes);
            showTaskIdError(err || 'Unable to fetch results');
            return;
        }
        const resultsData = await resultsRes.json();

        currentTaskData = { config: configData, results: resultsData };
        renderTaskPreview(configData, resultsData);
    } catch (e) {
        showTaskIdError(`Fetch failed: ${e.message}`);
    } finally {
        fetchTaskBtn.disabled = false;
        fetchTaskBtn.classList.remove('loading');
        fetchTaskBtn.textContent = originalLabel;
    }
}

function renderTaskPreview(configData, resultsData) {
    if (!taskPreview || !taskPreviewBody) return;
    const taskId = configData.task_id || 'Unknown';
    const taskName = configData.task_name || configData.description || '';
    const prompt = configData?.scenario_config?.prompt || '';
    const models = (resultsData?.task_metadata?.models_to_test || []).map(m => m.model_name).join(', ');
    const showTaskName = taskName && taskName !== prompt;

    taskPreviewBody.innerHTML = `
        <div><strong>Task ID:</strong> ${escapeHtml(String(taskId))}</div>
        ${showTaskName ? `<div><strong>Task Name:</strong> ${escapeHtml(String(taskName))}</div>` : ''}
        ${prompt ? `<div><strong>Prompt:</strong> ${escapeHtml(String(prompt))}</div>` : ''}
        ${models ? `<div><strong>Models:</strong> ${escapeHtml(String(models))}</div>` : ''}
    `;
    taskPreview.classList.remove('hidden');
}

function showTaskIdError(message) {
    if (!taskIdError) return;
    taskIdError.textContent = message;
    taskIdError.classList.remove('hidden');
}

function clearTaskIdError() {
    if (!taskIdError) return;
    taskIdError.textContent = '';
    taskIdError.classList.add('hidden');
}

async function safeReadError(response) {
    try {
        const data = await response.json();
        return data.error || response.statusText;
    } catch (e) {
        return response.statusText;
    }
}

function showModalEmailError(message) {
    if (!modalEmailError) return;
    modalEmailError.textContent = message;
    modalEmailError.classList.remove('hidden');
}

function clearModalEmailError() {
    if (!modalEmailError) return;
    modalEmailError.textContent = '';
    modalEmailError.classList.add('hidden');
}
