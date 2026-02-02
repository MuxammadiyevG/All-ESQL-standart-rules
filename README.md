# ESQL SIEM Dashboard

A comprehensive Security Information and Event Management (SIEM) dashboard inspired by Wazuh, built with Flask and Elasticsearch.

## Features

✨ **168 Security Detection Rules** across GDPR, NIST, and PCI-DSS frameworks  
🔍 **ES|QL Query Execution** against Elasticsearch logs  
📊 **Interactive Charts** with Chart.js (timeline, severity, top rules, top sources)  
🎨 **Modern Dark UI** with glassmorphism effects  
⚡ **Real-time Alerts** with detailed log matching  
🔧 **Rule Management** with category and severity filtering  

## Quick Start

### 1. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Elasticsearch

Edit `config.py` to set your Elasticsearch credentials:

```python
ES_HOST = 'http://139.28.47.17:9908/'
ES_USERNAME = 'elastic'
ES_PASSWORD = 'elasticpassword'
```

### 3. Enable Rules

**Enable all rules at once:**
```bash
python enable_rules.py enable
```

**Disable all rules:**
```bash
python enable_rules.py disable
```

**Or manually edit individual rule files** in `rules/` directory and change `enabled: false` to `enabled: true`.

### 4. Start the Dashboard

```bash
python app.py
```

The dashboard will be available at **http://localhost:1212/**

### 5. Execute Rules

1. Open the dashboard in your browser
2. Click the **"Execute Rules"** button
3. The system will run all enabled rules against Elasticsearch
4. Alerts will appear in the dashboard with charts populated

## Project Structure

```
.
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── es_client.py           # Elasticsearch client wrapper
├── rule_loader.py         # YAML rule parser
├── rule_engine.py         # Rule execution engine
├── alert_manager.py       # Alert storage and statistics
├── enable_rules.py        # Utility to enable/disable rules
├── requirements.txt       # Python dependencies
├── rules/                 # Security detection rules
│   ├── GDPR_yml/         # GDPR compliance rules (55 rules)
│   ├── NIST_rule_base/   # NIST framework rules (65 rules)
│   └── PCI-DSS_yml/      # PCI-DSS rules (48 rules)
├── templates/            # HTML templates
│   └── index.html        # Dashboard template
└── static/               # Static assets
    ├── css/
    │   └── styles.css    # Dashboard styles
    └── js/
        ├── app.js        # Main application logic
        ├── charts.js     # Chart visualizations
        └── alerts.js     # Alert management
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard page |
| `/api/health` | GET | Health check |
| `/api/rules` | GET | List all rules |
| `/api/rules/<id>` | GET | Get specific rule |
| `/api/execute` | POST | Execute rules |
| `/api/alerts` | GET | Get alerts |
| `/api/alerts/<id>` | GET | Get alert details |
| `/api/stats` | GET | Dashboard statistics |
| `/api/charts/*` | GET | Chart data |

## Rules

### Rule Format

Rules are defined in YAML format with ES|QL queries:

```yaml
name: Rule Name
description: What this rule detects
type: esql
schedule_interval: 5m
index:
  - winlogbeat-*
  - filebeat-*
query: |
  FROM winlogbeat-*
  | WHERE @timestamp >= NOW() - 5 minutes
  | WHERE event.category == "authentication"
  | STATS count = COUNT(*) BY user.name
enabled: true
severity: medium
risk_score: 50
```

### Rule Categories

- **GDPR (55 rules)**: EU General Data Protection Regulation compliance
- **NIST (65 rules)**: NIST Cybersecurity Framework controls
- **PCI-DSS (48 rules)**: Payment Card Industry Data Security Standard

## Utility Scripts

### enable_rules.py

Bulk enable or disable all rules:

```bash
# Enable all rules
python enable_rules.py enable

# Disable all rules
python enable_rules.py disable
```

After changing rules, restart the application:

```bash
pkill -f "python app.py"
python app.py &
```

## Screenshots

Dashboard with statistics, rules, and charts:
![Dashboard](/.gemini/antigravity/brain/6981625e-aff9-44cb-9839-c76184c07e4c/initial_dashboard_load_1770032626744.png)

Rule details modal showing ES|QL query:
![Rule Details](/.gemini/antigravity/brain/6981625e-aff9-44cb-9839-c76184c07e4c/rule_details_modal_1770032678716.png)

## Technology Stack

- **Backend**: Flask 3.0+
- **Database**: Elasticsearch 8.11+ (ES|QL queries)
- **Frontend**: Vanilla JavaScript, Chart.js 4.4
- **Styling**: Custom CSS with dark theme
- **Data Format**: YAML for rule definitions

## Development

Run in debug mode:

```bash
python app.py
```

The application runs on `0.0.0.0:1212` by default. Edit `config.py` to change the port.

## License

This project is for security monitoring and compliance purposes.
