"""
Flask application for SIEM Dashboard
"""
from flask import Flask, render_template, jsonify, request
from config import Config
from es_client import ElasticsearchClient
from rule_loader import RuleLoader
from rule_engine import RuleEngine
from alert_manager import AlertManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
es_client = ElasticsearchClient()
rule_loader = RuleLoader()
alert_manager = AlertManager(max_alerts=Config.MAX_ALERTS_STORED)
rule_engine = RuleEngine(es_client=es_client, alert_manager=alert_manager)

# Load rules on startup
logger.info("Loading rules...")
rules = rule_loader.load_all_rules()
logger.info(f"Loaded {len(rules)} rules")


@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    es_status = es_client.ping()
    return jsonify({
        'status': 'healthy' if es_status else 'degraded',
        'elasticsearch': 'connected' if es_status else 'disconnected',
        'rules_loaded': len(rules)
    })


@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Get all rules"""
    # Optional filters
    category = request.args.get('category')
    severity = request.args.get('severity')
    enabled = request.args.get('enabled')
    
    filtered_rules = rules
    
    if category:
        filtered_rules = [r for r in filtered_rules if r['category'] == category]
    
    if severity:
        filtered_rules = [r for r in filtered_rules if r['severity'] == severity]
    
    if enabled is not None:
        enabled_bool = enabled.lower() == 'true'
        filtered_rules = [r for r in filtered_rules if r['enabled'] == enabled_bool]
    
    return jsonify({
        'total': len(filtered_rules),
        'rules': filtered_rules
    })


@app.route('/api/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """Get a specific rule"""
    rule = rule_loader.get_rule_by_id(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    return jsonify(rule)


@app.route('/api/execute', methods=['POST'])
def execute_rules():
    """Execute rules and generate alerts"""
    try:
        data = request.get_json() or {}
        rule_ids = data.get('rule_ids', [])
        execute_all = data.get('execute_all', True)
        
        if execute_all:
            # Execute all enabled rules
            summary = rule_engine.execute_enabled_rules(rules)
        elif rule_ids:
            # Execute specific rules
            rules_to_execute = [rule_loader.get_rule_by_id(rid) for rid in rule_ids]
            rules_to_execute = [r for r in rules_to_execute if r is not None]
            summary = rule_engine.execute_all_rules(rules_to_execute)
        else:
            return jsonify({'error': 'No rules to execute'}), 400
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error executing rules: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional filtering"""
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', Config.ALERTS_PER_PAGE))
    
    # Filters
    severity = request.args.get('severity')
    rule_id = request.args.get('rule_id')
    
    all_alerts = alert_manager.get_all_alerts()
    
    # Apply filters
    if severity:
        all_alerts = [a for a in all_alerts if a['severity'] == severity]
    
    if rule_id:
        all_alerts = [a for a in all_alerts if a['rule_id'] == rule_id]
    
    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    paginated_alerts = all_alerts[start:end]
    
    return jsonify({
        'total': len(all_alerts),
        'page': page,
        'per_page': per_page,
        'alerts': paginated_alerts
    })


@app.route('/api/alerts/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert with matched logs"""
    alert = alert_manager.get_alert_by_id(alert_id)
    
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    return jsonify(alert)


@app.route('/api/alerts', methods=['DELETE'])
def clear_alerts():
    """Clear all alerts"""
    count = alert_manager.clear_alerts()
    return jsonify({
        'success': True,
        'cleared': count
    })


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get dashboard statistics"""
    rule_stats = rule_loader.get_statistics()
    alert_stats = alert_manager.get_statistics()
    
    return jsonify({
        'rules': rule_stats,
        'alerts': alert_stats,
        'elasticsearch_connected': es_client.ping()
    })


@app.route('/api/charts/timeline', methods=['GET'])
def get_timeline_chart():
    """Get alert timeline data for chart"""
    buckets = int(request.args.get('buckets', Config.TIMELINE_BUCKETS))
    timeline_data = alert_manager.get_timeline_data(buckets)
    
    return jsonify(timeline_data)


@app.route('/api/charts/severity', methods=['GET'])
def get_severity_chart():
    """Get severity distribution for chart"""
    stats = alert_manager.get_statistics()
    severity_data = stats.get('by_severity', {})
    
    # Convert to chart format
    chart_data = {
        'labels': list(severity_data.keys()),
        'values': list(severity_data.values())
    }
    
    return jsonify(chart_data)


@app.route('/api/charts/top-rules', methods=['GET'])
def get_top_rules_chart():
    """Get top triggered rules for chart"""
    limit = int(request.args.get('limit', Config.TOP_ITEMS_LIMIT))
    stats = alert_manager.get_statistics()
    top_rules = stats.get('top_rules', [])[:limit]
    
    # Convert to chart format
    chart_data = {
        'labels': [r[0] for r in top_rules],
        'values': [r[1] for r in top_rules]
    }
    
    return jsonify(chart_data)


@app.route('/api/charts/top-sources', methods=['GET'])
def get_top_sources_chart():
    """Get top source IPs for chart"""
    limit = int(request.args.get('limit', Config.TOP_ITEMS_LIMIT))
    top_sources = alert_manager.get_top_sources(limit)
    
    # Convert to chart format
    chart_data = {
        'labels': [s['source'] for s in top_sources],
        'values': [s['count'] for s in top_sources]
    }
    
    return jsonify(chart_data)


@app.route('/api/charts/categories', methods=['GET'])
def get_categories_chart():
    """Get alert distribution by category"""
    stats = alert_manager.get_statistics()
    category_data = stats.get('by_category', {})
    
    chart_data = {
        'labels': list(category_data.keys()),
        'values': list(category_data.values())
    }
    
    return jsonify(chart_data)


if __name__ == '__main__':
    logger.info(f"Starting SIEM Dashboard on {Config.HOST}:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
