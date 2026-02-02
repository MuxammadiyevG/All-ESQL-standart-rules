#!/usr/bin/env python3
"""
Diagnostic script to check Elasticsearch indices and test rule execution
"""
from es_client import ElasticsearchClient
from rule_loader import RuleLoader
from rule_engine import RuleEngine
from alert_manager import AlertManager
import json

def check_elasticsearch_indices():
    """Check what indices exist in Elasticsearch"""
    print("=" * 60)
    print("CHECKING ELASTICSEARCH INDICES")
    print("=" * 60)
    
    client = ElasticsearchClient()
    
    # Test connection
    if not client.ping():
        print("❌ Cannot connect to Elasticsearch!")
        return
    
    print("✓ Connected to Elasticsearch\n")
    
    # Get all indices
    try:
        response = client.client.cat.indices(format='json')
        
        if not response:
            print("⚠️  No indices found!")
            return
        
        print(f"Found {len(response)} indices:\n")
        
        # Filter for common log indices
        log_patterns = ['winlogbeat', 'filebeat', 'logstash', 'logs', 'beats']
        
        relevant_indices = []
        for idx in response:
            index_name = idx.get('index', '')
            docs_count = idx.get('docs.count', '0')
            store_size = idx.get('store.size', '0')
            
            is_relevant = any(pattern in index_name.lower() for pattern in log_patterns)
            
            if is_relevant or not index_name.startswith('.'):
                relevant_indices.append(idx)
                marker = "📊" if is_relevant else "  "
                print(f"{marker} {index_name:40s} | {docs_count:>10s} docs | {store_size}")
        
        if not relevant_indices:
            print("\n⚠️  No relevant log indices found!")
            print("   Rules expect indices like: winlogbeat-*, filebeat-*, etc.")
        
    except Exception as e:
        print(f"❌ Error getting indices: {e}")

def test_simple_query():
    """Test a simple ES|QL query"""
    print("\n" + "=" * 60)
    print("TESTING SIMPLE ES|QL QUERY")
    print("=" * 60)
    
    client = ElasticsearchClient()
    
    # Try a very simple query on all indices
    test_queries = [
        "FROM * | LIMIT 5",
        "FROM winlogbeat-* | LIMIT 5",
        "FROM filebeat-* | LIMIT 5",
        "FROM logs-* | LIMIT 5"
    ]
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        try:
            result = client.execute_esql(query)
            if result and 'values' in result:
                count = len(result.get('values', []))
                print(f"  ✓ Success: {count} rows returned")
                if count > 0:
                    print(f"  Sample data: {result['values'][0][:3] if result['values'][0] else 'empty'}")
            else:
                print(f"  ⚠️  No data returned")
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")

def test_rule_execution():
    """Test executing a few simple rules"""
    print("\n" + "=" * 60)
    print("TESTING RULE EXECUTION")
    print("=" * 60)
    
    # Load rules
    loader = RuleLoader()
    rules = loader.load_all_rules()
    enabled_rules = [r for r in rules if r['enabled']]
    
    print(f"\n✓ Loaded {len(enabled_rules)} enabled rules")
    
    # Create engine
    es_client = ElasticsearchClient()
    alert_manager = AlertManager()
    engine = RuleEngine(es_client, alert_manager)
    
    # Test first 3 rules
    test_count = min(3, len(enabled_rules))
    print(f"\nTesting first {test_count} rules:\n")
    
    for i, rule in enumerate(enabled_rules[:test_count]):
        print(f"{i+1}. {rule['name']} ({rule['category']})")
        print(f"   Query preview: {rule['query'][:80]}...")
        
        try:
            result = engine.execute_rule(rule)
            if result > 0:
                print(f"   ✅ Generated {result} alert(s)!")
            else:
                print(f"   ℹ️  No matches found")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
        print()

def analyze_rule_queries():
    """Analyze rule queries for common issues"""
    print("\n" + "=" * 60)
    print("ANALYZING RULE QUERIES")
    print("=" * 60)
    
    loader = RuleLoader()
    rules = loader.load_all_rules()
    enabled_rules = [r for r in rules if r['enabled']]
    
    issues = {
        'missing_time_filter': [],
        'invalid_index': [],
        'empty_query': [],
        'syntax_issues': []
    }
    
    for rule in enabled_rules:
        query = rule.get('query', '').strip()
        indices = rule.get('index', [])
        
        # Check for empty query
        if not query:
            issues['empty_query'].append(rule['name'])
            continue
        
        # Check for time filter (important for performance)
        if 'NOW()' not in query and '@timestamp' in query:
            issues['missing_time_filter'].append(rule['name'])
        
        # Check if indices are specified
        if not indices:
            issues['invalid_index'].append(rule['name'])
    
    print(f"\nAnalysis Results:")
    print(f"  Total enabled rules: {len(enabled_rules)}")
    print(f"  Empty queries: {len(issues['empty_query'])}")
    print(f"  Missing time filters: {len(issues['missing_time_filter'])}")
    print(f"  No indices specified: {len(issues['invalid_index'])}")
    
    if issues['empty_query']:
        print(f"\n⚠️  Rules with empty queries:")
        for name in issues['empty_query'][:5]:
            print(f"     - {name}")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ELASTICSEARCH & RULE DIAGNOSTICS")
    print("=" * 60 + "\n")
    
    check_elasticsearch_indices()
    test_simple_query()
    test_rule_execution()
    analyze_rule_queries()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)
