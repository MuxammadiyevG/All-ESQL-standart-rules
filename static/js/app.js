// Main Dashboard Application Logic

// Global state
const state = {
    rules: [],
    alerts: [],
    stats: null,
    charts: {}
};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function () {
    console.log('Dashboard initializing...');

    // Load initial data
    loadDashboard();

    // Setup event listeners
    setupEventListeners();

    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);
});

// Setup event listeners
function setupEventListeners() {
    // Execute rules button
    document.getElementById('execute-rules-btn').addEventListener('click', executeRules);

    // Clear alerts button
    document.getElementById('clear-alerts-btn').addEventListener('click', clearAlerts);

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadDashboard);

    // Rule filters
    document.getElementById('category-filter').addEventListener('change', filterRules);
    document.getElementById('severity-filter').addEventListener('change', filterRules);

    // Alert filters
    document.getElementById('alert-severity-filter').addEventListener('change', loadAlerts);
}

// Load entire dashboard
async function loadDashboard() {
    console.log('Loading dashboard data...');

    try {
        await Promise.all([
            loadStatistics(),
            loadRules(),
            loadAlerts(),
            loadCharts()
        ]);

        console.log('Dashboard loaded successfully');
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Error loading dashboard data', 'error');
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        state.stats = data;

        // Update stat cards
        document.getElementById('total-rules').textContent = data.rules.total || 0;
        document.getElementById('total-alerts').textContent = data.alerts.total || 0;
        document.getElementById('enabled-rules').textContent = data.rules.enabled || 0;

        // Update Elasticsearch status
        const esStatus = document.getElementById('es-status');
        if (data.elasticsearch_connected) {
            esStatus.innerHTML = '<i class="fas fa-check-circle"></i> Connected';
            esStatus.style.color = 'var(--success)';
        } else {
            esStatus.innerHTML = '<i class="fas fa-times-circle"></i> Disconnected';
            esStatus.style.color = 'var(--danger)';
        }

    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load rules
async function loadRules() {
    try {
        const response = await fetch('/api/rules');
        const data = await response.json();
        state.rules = data.rules || [];

        displayRules(state.rules);
    } catch (error) {
        console.error('Error loading rules:', error);
        document.getElementById('rules-list').innerHTML = '<div class="loading">Error loading rules</div>';
    }
}

// Display rules in sidebar
function displayRules(rules) {
    const rulesList = document.getElementById('rules-list');

    if (!rules || rules.length === 0) {
        rulesList.innerHTML = '<div class="loading">No rules found</div>';
        return;
    }

    rulesList.innerHTML = rules.map(rule => `
        <div class="rule-item" onclick="showRuleDetails('${rule.id}')">
            <div class="rule-item-header">
                <div class="rule-name">${escapeHtml(rule.name)}</div>
                <span class="rule-badge ${rule.enabled ? 'enabled' : 'disabled'}">
                    ${rule.enabled ? 'ON' : 'OFF'}
                </span>
            </div>
            <div class="rule-meta">
                <span class="rule-category">${rule.category}</span>
                <span class="rule-severity">${rule.severity}</span>
            </div>
        </div>
    `).join('');
}

// Filter rules
function filterRules() {
    const category = document.getElementById('category-filter').value;
    const severity = document.getElementById('severity-filter').value;

    let filtered = state.rules;

    if (category) {
        filtered = filtered.filter(r => r.category === category);
    }

    if (severity) {
        filtered = filtered.filter(r => r.severity === severity);
    }

    displayRules(filtered);
}

// Execute rules
async function executeRules() {
    showLoadingOverlay('Executing rules...');

    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                execute_all: true
            })
        });

        const result = await response.json();

        hideLoadingOverlay();

        if (result.success) {
            const summary = result.summary;
            showNotification(
                `Executed ${summary.executed} rules. Generated ${summary.alerts_generated} alerts.`,
                'success'
            );

            // Refresh dashboard
            await loadDashboard();
        } else {
            showNotification('Failed to execute rules', 'error');
        }

    } catch (error) {
        hideLoadingOverlay();
        console.error('Error executing rules:', error);
        showNotification('Error executing rules', 'error');
    }
}

// Clear alerts
async function clearAlerts() {
    if (!confirm('Are you sure you want to clear all alerts?')) {
        return;
    }

    try {
        const response = await fetch('/api/alerts', {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showNotification(`Cleared ${result.cleared} alerts`, 'success');
            await loadDashboard();
        }

    } catch (error) {
        console.error('Error clearing alerts:', error);
        showNotification('Error clearing alerts', 'error');
    }
}

// Show rule details
function showRuleDetails(ruleId) {
    const rule = state.rules.find(r => r.id === ruleId);
    if (!rule) return;

    const details = `
        <h3>${escapeHtml(rule.name)}</h3>
        <p><strong>Category:</strong> ${rule.category}</p>
        <p><strong>Severity:</strong> ${rule.severity}</p>
        <p><strong>Status:</strong> ${rule.enabled ? 'Enabled' : 'Disabled'}</p>
        <p><strong>Description:</strong> ${escapeHtml(rule.description)}</p>
        <p><strong>Query:</strong></p>
        <pre style="background: var(--secondary-bg); padding: 10px; border-radius: 8px; overflow-x: auto;">${escapeHtml(rule.query)}</pre>
    `;

    document.getElementById('alert-modal-body').innerHTML = details;
    document.getElementById('alert-modal').classList.add('active');
}

// Utility functions
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    overlay.querySelector('p').textContent = message;
    overlay.classList.add('active');
}

function hideLoadingOverlay() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);

    // You can enhance this with a toast notification library
    alert(message);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function closeAlertModal() {
    document.getElementById('alert-modal').classList.remove('active');
}

// Close modal on outside click
document.addEventListener('click', function (event) {
    const modal = document.getElementById('alert-modal');
    if (event.target === modal) {
        closeAlertModal();
    }
});
