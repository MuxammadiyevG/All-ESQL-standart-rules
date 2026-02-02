// Charts Management with Chart.js

// Chart instances
let timelineChart = null;
let severityChart = null;
let topRulesChart = null;
let topSourcesChart = null;

// Color schemes
const colors = {
    purple: '#7c3aed',
    pink: '#ec4899',
    blue: '#3b82f6',
    cyan: '#06b6d4',
    green: '#10b981',
    red: '#ef4444',
    orange: '#f59e0b',
    yellow: '#eab308'
};

const severityColors = {
    critical: colors.red,
    high: colors.orange,
    medium: colors.yellow,
    low: colors.blue
};

// Load all charts
async function loadCharts() {
    try {
        await Promise.all([
            loadTimelineChart(),
            loadSeverityChart(),
            loadTopRulesChart(),
            loadTopSourcesChart()
        ]);
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

// Timeline Chart
async function loadTimelineChart() {
    try {
        const response = await fetch('/api/charts/timeline');
        const data = await response.json();

        const ctx = document.getElementById('timeline-chart').getContext('2d');

        // Destroy existing chart
        if (timelineChart) {
            timelineChart.destroy();
        }

        // Prepare data
        const labels = data.map(d => {
            const date = new Date(d.timestamp);
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        });
        const values = data.map(d => d.count);

        // Create chart
        timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Alerts',
                    data: values,
                    borderColor: colors.purple,
                    backgroundColor: `${colors.purple}33`,
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: colors.pink,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: colors.purple,
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8',
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error loading timeline chart:', error);
    }
}

// Severity Distribution Chart
async function loadSeverityChart() {
    try {
        const response = await fetch('/api/charts/severity');
        const data = await response.json();

        const ctx = document.getElementById('severity-chart').getContext('2d');

        // Destroy existing chart
        if (severityChart) {
            severityChart.destroy();
        }

        // Prepare data
        const labels = data.labels || [];
        const values = data.values || [];
        const backgroundColors = labels.map(label => severityColors[label] || colors.blue);

        // Create chart
        severityChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors,
                    borderWidth: 2,
                    borderColor: '#0a0e27'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f1f5f9',
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: colors.purple,
                        borderWidth: 1,
                        padding: 12
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error loading severity chart:', error);
    }
}

// Top Rules Chart
async function loadTopRulesChart() {
    try {
        const response = await fetch('/api/charts/top-rules');
        const data = await response.json();

        const ctx = document.getElementById('top-rules-chart').getContext('2d');

        // Destroy existing chart
        if (topRulesChart) {
            topRulesChart.destroy();
        }

        // Prepare data
        const labels = (data.labels || []).map(label => {
            // Truncate long labels
            return label.length > 30 ? label.substring(0, 30) + '...' : label;
        });
        const values = data.values || [];

        // Create chart
        topRulesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Alerts',
                    data: values,
                    backgroundColor: colors.cyan,
                    borderColor: colors.blue,
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: colors.cyan,
                        borderWidth: 1,
                        padding: 12
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8',
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error loading top rules chart:', error);
    }
}

// Top Sources Chart
async function loadTopSourcesChart() {
    try {
        const response = await fetch('/api/charts/top-sources');
        const data = await response.json();

        const ctx = document.getElementById('top-sources-chart').getContext('2d');

        // Destroy existing chart
        if (topSourcesChart) {
            topSourcesChart.destroy();
        }

        // Prepare data
        const labels = data.labels || [];
        const values = data.values || [];

        // Create gradient colors
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, colors.pink);
        gradient.addColorStop(1, colors.purple);

        // Create chart
        topSourcesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Alerts',
                    data: values,
                    backgroundColor: gradient,
                    borderColor: colors.pink,
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: colors.pink,
                        borderWidth: 1,
                        padding: 12
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8',
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error loading top sources chart:', error);
    }
}
