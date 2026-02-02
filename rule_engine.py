"""
Rule execution engine for running ESQL rules against Elasticsearch
"""
from es_client import ElasticsearchClient
from alert_manager import AlertManager
from ecs_mapper import ECSFieldMapper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleEngine:
    """Execute ESQL rules and generate alerts"""
    
    def __init__(self, es_client=None, alert_manager=None, enable_ecs_mapping=True):
        """Initialize rule engine"""
        self.es_client = es_client or ElasticsearchClient()
        self.alert_manager = alert_manager or AlertManager()
        self.enable_ecs_mapping = enable_ecs_mapping
        
    def execute_rule(self, rule):
        """
        Execute a single rule
        
        Args:
            rule: Rule object to execute
            
        Returns:
            Number of alerts generated
        """
        if not rule.get('enabled', False):
            logger.debug(f"Skipping disabled rule: {rule['name']}")
            return 0
        
        query = rule.get('query', '').strip()
        if not query:
            logger.warning(f"Rule {rule['name']} has no query")
            return 0
        
        try:
            logger.info(f"Executing rule: {rule['name']}")
            
            # Transform ECS field names to actual Elasticsearch field names
            if self.enable_ecs_mapping:
                original_query = query
                query = ECSFieldMapper.transform_query(query)
                if query != original_query:
                    logger.debug(f"Transformed query with ECS mapping")
            
            # Execute the ES|QL query
            result = self.es_client.execute_esql(query)
            
            if result is None:
                logger.error(f"Query execution failed for rule: {rule['name']}")
                return 0
            
            # Parse results
            alerts_generated = self._process_query_results(rule, result)
            
            return alerts_generated
            
        except Exception as e:
            logger.error(f"Error executing rule {rule['name']}: {e}")
            return 0
    
    def _process_query_results(self, rule, result):
        """
        Process ES|QL query results and create alerts
        
        Args:
            rule: Rule that was executed
            result: Query result from Elasticsearch
            
        Returns:
            Number of alerts created
        """
        try:
            # ES|QL results structure: {columns: [...], values: [[...]]}
            if not result or 'values' not in result:
                logger.debug(f"No results for rule: {rule['name']}")
                return 0
            
            values = result.get('values', [])
            columns = result.get('columns', [])
            
            if not values:
                logger.debug(f"No matching data for rule: {rule['name']}")
                return 0
            
            # Convert results to dictionaries
            matched_logs = []
            for row in values:
                log_entry = {}
                for i, col in enumerate(columns):
                    col_name = col.get('name', f'col_{i}')
                    if i < len(row):
                        log_entry[col_name] = row[i]
                matched_logs.append(log_entry)
            
            # Create alert with matched logs
            if matched_logs:
                self.alert_manager.add_alert(rule, matched_logs)
                logger.info(f"Generated alert for rule '{rule['name']}' with {len(matched_logs)} matched logs")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Error processing results for rule {rule['name']}: {e}")
            return 0
    
    def execute_all_rules(self, rules):
        """
        Execute multiple rules
        
        Args:
            rules: List of rule objects
            
        Returns:
            dict with execution summary
        """
        total_rules = len(rules)
        executed = 0
        failed = 0
        alerts_generated = 0
        
        logger.info(f"Starting execution of {total_rules} rules")
        
        for rule in rules:
            try:
                result = self.execute_rule(rule)
                if result >= 0:
                    executed += 1
                    alerts_generated += result
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to execute rule {rule.get('name', 'unknown')}: {e}")
                failed += 1
        
        summary = {
            'total_rules': total_rules,
            'executed': executed,
            'failed': failed,
            'alerts_generated': alerts_generated
        }
        
        logger.info(f"Execution complete: {summary}")
        return summary
    
    def execute_enabled_rules(self, rules):
        """Execute only enabled rules"""
        enabled_rules = [r for r in rules if r.get('enabled', False)]
        logger.info(f"Found {len(enabled_rules)} enabled rules out of {len(rules)} total")
        return self.execute_all_rules(enabled_rules)
