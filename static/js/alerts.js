// Alerts Display and Management

// Load and display alerts
async function loadAlerts() {
    try {
        const severity = document.getElementById('alert-severity-filter').value;
        const params = new URLSearchParams();

        if (severity) {
            params.append('severity', severity);
        }

        const response = await fetch(`/api/alerts?${params.toString()}`);
        const data = await response.json();

        state.alerts = data.alerts || [];
        displayAlerts(state.alerts);

    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('alerts-container').innerHTML =
            '<div class="loading">Error loading alerts</div>';
    }
}

// Display alerts in table
function displayAlerts(alerts) {
    const container = document.getElementById('alerts-container');

    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div class="loading">No alerts found. Click "Execute Rules" to start detection.</div>';
        return;
    }

    const tableHTML = `
        <table class="alerts-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Rule</th>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>Matched Logs</th>
                </tr>
            </thead>
            <tbody>
                ${alerts.map(alert => `
                    <tr onclick="showAlertDetails('${alert.id}')">
                        <td>${formatTimestamp(alert.timestamp)}</td>
                        <td>${escapeHtml(alert.rule_name)}</td>
                        <td>
                            <span class="severity-badge severity-${alert.severity}">
                                ${alert.severity}
                            </span>
                        </td>
                        <td>${alert.category}</td>
                        <td>${alert.log_count || 0}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

// Show alert details in modal
async function showAlertDetails(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}`);
        const alert = await response.json();

        if (!alert) {
            showNotification('Alert not found', 'error');
            return;
        }

        // Build matched logs HTML
        let matchedLogsHTML = '';
        if (alert.matched_logs && alert.matched_logs.length > 0) {
            matchedLogsHTML = `
                <h4>Matched Logs (${alert.matched_logs.length})</h4>
                <div style="max-height: 400px; overflow-y: auto;">
                    ${alert.matched_logs.map((log, index) => `
                        <div style="background: var(--secondary-bg); padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid ${severityColors[alert.severity] || colors.blue};">
                            <strong>Log ${index + 1}</strong>
                            <pre style="margin-top: 8px; white-space: pre-wrap; word-break: break-all;">${JSON.stringify(log, null, 2)}</pre>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            matchedLogsHTML = '<p>No detailed log data available.</p>';
        }

        const detailsHTML = `
            <div style="margin-bottom: 20px;">
                <h3 style="color: var(--text-primary); margin-bottom: 15px;">
                    ${escapeHtml(alert.rule_name)}
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                    <div>
                        <strong style="color: var(--text-secondary);">Alert ID:</strong>
                        <p>${alert.id}</p>
                    </div>
                    <div>
                        <strong style="color: var(--text-secondary);">Timestamp:</strong>
                        <p>${formatTimestamp(alert.timestamp)}</p>
                    </div>
                    <div>
                        <strong style="color: var(--text-secondary);">Severity:</strong>
                        <p><span class="severity-badge severity-${alert.severity}">${alert.severity}</span></p>
                    </div>
                    <div>
                        <strong style="color: var(--text-secondary);">Risk Score:</strong>
                        <p>${alert.risk_score}</p>
                    </div>
                    <div>
                        <strong style="color: var(--text-secondary);">Category:</strong>
                        <p>${alert.category}</p>
                    </div>
                    <div>
                        <strong style="color: var(--text-secondary);">Matched Logs:</strong>
                        <p>${alert.log_count || 0}</p>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <strong style="color: var(--text-secondary);">Description:</strong>
                    <p style="margin-top: 8px;">${escapeHtml(alert.description) || 'No description available'}</p>
                </div>
                
                ${alert.tags && alert.tags.length > 0 ? `
                    <div style="margin-bottom: 20px;">
                        <strong style="color: var(--text-secondary);">Tags:</strong>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                            ${alert.tags.map(tag => `
                                <span style="background: rgba(124, 58, 237, 0.2); color: var(--accent-purple); padding: 4px 12px; border-radius: 6px; font-size: 12px;">
                                    ${escapeHtml(tag)}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <hr style="border: none; border-top: 1px solid var(--border-color); margin: 20px 0;">
                
                ${matchedLogsHTML}
            </div>
        `;

        document.getElementById('alert-modal-body').innerHTML = detailsHTML;
        document.getElementById('alert-modal').classList.add('active');

    } catch (error) {
        console.error('Error loading alert details:', error);
        showNotification('Error loading alert details', 'error');
    }
}

// Format timestamp for display
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';

    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        return timestamp;
    }
}
