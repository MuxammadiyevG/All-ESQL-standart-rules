"""
Alert manager for storing and retrieving security alerts
"""
from datetime import datetime
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertManager:
    """Manage security alerts"""
    
    def __init__(self, max_alerts=1000):
        """Initialize alert manager"""
        self.alerts = []
        self.max_alerts = max_alerts
        self._alert_counter = 0
        
    def add_alert(self, rule, matched_data):
        """
        Add a new alert
        
        Args:
            rule: Rule object that triggered the alert
            matched_data: Data from ES|QL query that matched the rule
        """
        self._alert_counter += 1
        
        alert = {
            'id': f"alert_{self._alert_counter}",
            'timestamp': datetime.utcnow().isoformat(),
            'rule_id': rule['id'],
            'rule_name': rule['name'],
            'severity': rule['severity'],
            'risk_score': rule['risk_score'],
            'category': rule['category'],
            'tags': rule['tags'],
            'description': rule['description'],
            'matched_logs': matched_data,
            'log_count': len(matched_data) if isinstance(matched_data, list) else 1
        }
        
        self.alerts.insert(0, alert)  # Insert at beginning for newest first
        
        # Limit total stored alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[:self.max_alerts]
        
        logger.info(f"Added alert: {alert['id']} - {rule['name']}")
        return alert
    
    def get_all_alerts(self):
        """Get all alerts"""
        return self.alerts
    
    def get_alert_by_id(self, alert_id):
        """Get a specific alert by ID"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                return alert
        return None
    
    def get_alerts_by_severity(self, severity):
        """Get alerts filtered by severity"""
        return [a for a in self.alerts if a['severity'] == severity]
    
    def get_alerts_by_rule(self, rule_id):
        """Get alerts for a specific rule"""
        return [a for a in self.alerts if a['rule_id'] == rule_id]
    
    def get_recent_alerts(self, limit=20):
        """Get most recent alerts"""
        return self.alerts[:limit]
    
    def clear_alerts(self):
        """Clear all alerts"""
        count = len(self.alerts)
        self.alerts = []
        logger.info(f"Cleared {count} alerts")
        return count
    
    def get_statistics(self):
        """Get alert statistics"""
        total = len(self.alerts)
        
        by_severity = defaultdict(int)
        by_category = defaultdict(int)
        by_rule = defaultdict(int)
        
        for alert in self.alerts:
            by_severity[alert['severity']] += 1
            by_category[alert['category']] += 1
            by_rule[alert['rule_name']] += 1
        
        # Get top triggered rules
        top_rules = sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total': total,
            'by_severity': dict(by_severity),
            'by_category': dict(by_category),
            'top_rules': top_rules
        }
    
    def get_timeline_data(self, buckets=24):
        """
        Get alert timeline data for charting
        
        Args:
            buckets: Number of time buckets
            
        Returns:
            List of {timestamp, count} for each bucket
        """
        if not self.alerts:
            return []
        
        # Group alerts by approximate time buckets
        timeline = defaultdict(int)
        
        for alert in self.alerts:
            # Round timestamp to nearest bucket
            timestamp = alert['timestamp'][:16]  # Truncate to minute
            timeline[timestamp] += 1
        
        # Convert to sorted list
        result = [{'timestamp': k, 'count': v} for k, v in sorted(timeline.items())]
        
        return result
    
    def get_top_sources(self, limit=10):
        """
        Get top source IPs from alerts
        
        Returns:
            List of {source, count}
        """
        sources = defaultdict(int)
        
        for alert in self.alerts:
            matched_logs = alert.get('matched_logs', [])
            if isinstance(matched_logs, list):
                for log in matched_logs:
                    if isinstance(log, dict):
                        source_ip = log.get('source.ip') or log.get('source_ip')
                        if source_ip:
                            sources[source_ip] += 1
        
        # Sort and limit
        top = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'source': k, 'count': v} for k, v in top]
