"""
Rule loader for loading and parsing ESQL rules from YAML files
"""
import os
import yaml
import hashlib
from pathlib import Path
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleLoader:
    """Load and parse ESQL rules from YAML files"""
    
    def __init__(self, rules_dir=None):
        """Initialize rule loader"""
        self.rules_dir = rules_dir or Config.RULES_DIRECTORY
        self.rules = []
        
    def _generate_rule_id(self, file_path, rule_data):
        """Generate a unique ID for a rule"""
        # Use file path and rule name to generate consistent ID
        unique_string = f"{file_path}:{rule_data.get('name', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def _parse_rule_file(self, file_path):
        """Parse a single YAML rule file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_data = yaml.safe_load(f)
            
            if not rule_data:
                logger.warning(f"Empty rule file: {file_path}")
                return None
            
            # Generate rule ID
            rule_id = self._generate_rule_id(file_path, rule_data)
            
            # Extract category from path
            path_parts = Path(file_path).parts
            category = 'unknown'
            if 'GDPR_yml' in path_parts:
                category = 'GDPR'
            elif 'NIST_rule_base' in path_parts:
                category = 'NIST'
            elif 'PCI-DSS_yml' in path_parts:
                category = 'PCI-DSS'
            
            # Build rule object
            rule = {
                'id': rule_id,
                'name': rule_data.get('name', 'Unnamed Rule'),
                'description': rule_data.get('description', ''),
                'type': rule_data.get('type', 'esql'),
                'query': rule_data.get('query', ''),
                'query_language': rule_data.get('query_language', 'esql'),
                'index': rule_data.get('index', []),
                'enabled': rule_data.get('enabled', False),
                'severity': rule_data.get('severity', 'medium'),
                'risk_score': rule_data.get('risk_score', 50),
                'tags': rule_data.get('tags', []),
                'schedule_interval': rule_data.get('schedule_interval', '5m'),
                'category': category,
                'file_path': str(file_path),
                'mitre_attack': rule_data.get('mitre_attack', {}),
                'nist': rule_data.get('nist', []),
                'gdpr': rule_data.get('gdpr', []),
                'pci_dss': rule_data.get('pci-dss', []),
                'hipaa': rule_data.get('hipaa', [])
            }
            
            return rule
            
        except Exception as e:
            logger.error(f"Error parsing rule file {file_path}: {e}")
            return None
    
    def load_all_rules(self):
        """Load all rules from the rules directory"""
        self.rules = []
        rules_path = Path(self.rules_dir)
        
        if not rules_path.exists():
            logger.error(f"Rules directory not found: {self.rules_dir}")
            return self.rules
        
        # Find all YAML files recursively
        yaml_files = list(rules_path.rglob('*.yml')) + list(rules_path.rglob('*.yaml'))
        
        logger.info(f"Found {len(yaml_files)} rule files")
        
        for yaml_file in yaml_files:
            rule = self._parse_rule_file(yaml_file)
            if rule:
                self.rules.append(rule)
        
        logger.info(f"Successfully loaded {len(self.rules)} rules")
        return self.rules
    
    def get_rule_by_id(self, rule_id):
        """Get a specific rule by ID"""
        for rule in self.rules:
            if rule['id'] == rule_id:
                return rule
        return None
    
    def get_rules_by_category(self, category):
        """Get all rules in a specific category"""
        return [r for r in self.rules if r['category'] == category]
    
    def get_enabled_rules(self):
        """Get all enabled rules"""
        return [r for r in self.rules if r['enabled']]
    
    def get_rules_by_severity(self, severity):
        """Get all rules with a specific severity"""
        return [r for r in self.rules if r['severity'] == severity]
    
    def get_statistics(self):
        """Get statistics about loaded rules"""
        total = len(self.rules)
        enabled = len(self.get_enabled_rules())
        
        by_category = {}
        by_severity = {}
        
        for rule in self.rules:
            cat = rule['category']
            sev = rule['severity']
            
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            'total': total,
            'enabled': enabled,
            'disabled': total - enabled,
            'by_category': by_category,
            'by_severity': by_severity
        }
