#!/usr/bin/env python3
"""
Script to discover actual field names from Elasticsearch indices
and suggest fixes for rule queries
"""
from es_client import ElasticsearchClient
import json

def get_all_fields(index_pattern, limit=50):
    """Get all fields from an index"""
    client = ElasticsearchClient()
    
    try:
        # Get a sample document to see all fields
        result = client.execute_esql(f'FROM {index_pattern} | LIMIT 1')
        
        if not result or 'columns' not in result:
            print(f"❌ No data found in {index_pattern}")
            return []
        
        columns = result.get('columns', [])
        
        fields = [col.get('name') for col in columns]
        
        return fields
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def search_fields(fields, search_term):
    """Search for fields containing a search term"""
    return [f for f in fields if search_term.lower() in f.lower()]

def main():
    print("=" * 70)
    print("ELASTICSEARCH FIELD DISCOVERY TOOL")
    print("=" * 70)
    
    # Check different indices
    indices = ['winlogbeat-*', 'filebeat-*']
    
    all_fields = {}
    
    for index in indices:
        print(f"\n📊 Checking {index}...")
        fields = get_all_fields(index)
        if fields:
            all_fields[index] = fields
            print(f"   Found {len(fields)} fields")
    
    if not all_fields:
        print("\n❌ No fields found!")
        return
    
    # Common field mapping issues
    print("\n" + "=" * 70)
    print("COMMON FIELD NAME MAPPINGS")
    print("=" * 70)
    
    mappings = {
        'Account/User fields': ['user', 'account', 'subject'],
        'Group fields': ['group', 'member'],
        'Source IP fields': ['source', 'ipaddress', 'workstation'],
        'Process fields': ['process', 'image', 'commandline'],
        'Authentication fields': ['auth', 'logon', 'login'],
        'Event fields': ['event', 'eventid', 'code']
    }
    
    for index, fields in all_fields.items():
        print(f"\n🔍 {index}:")
        
        for category, keywords in mappings.items():
            print(f"\n  {category}:")
            matching = []
            for keyword in keywords:
                matches = search_fields(fields, keyword)
                matching.extend(matches)
            
            # Remove duplicates and limit
            matching = list(set(matching))[:15]
            
            if matching:
                for field in sorted(matching):
                    print(f"    - {field}")
            else:
                print(f"    (none found)")
    
    # Specific field suggestions
    print("\n" + "=" * 70)
    print("SUGGESTED FIELD REPLACEMENTS FOR RULES")
    print("=" * 70)
    
    suggestions = {
        'group.name': 'winlog.event_data.TargetUserName or winlog.event_data.MemberName',
        'user.name': 'winlog.event_data.TargetUserName or winlog.event_data.SubjectUserName',
        'source.ip': 'winlog.event_data.IpAddress or winlog.event_data.WorkstationName',
        'process.name': 'winlog.event_data.NewProcessName or winlog.event_data.ProcessName',
        'process.parent.name': 'winlog.event_data.ParentProcessName',
        'process.command_line': 'winlog.event_data.CommandLine',
        'winlog.logon.authentication_package': 'winlog.event_data.AuthenticationPackageName',
        'process.target.name': 'winlog.event_data.TargetImage'
    }
    
    print("\nRule field → Actual Elasticsearch field:")
    for rule_field, actual_field in suggestions.items():
        print(f"  {rule_field:40s} → {actual_field}")
    
    print("\n" + "=" * 70)
    print("TESTING SIMPLE QUERIES")
    print("=" * 70)
    
    # Test some simple queries
    client = ElasticsearchClient()
    
    test_queries = [
        ("Event Code 4624 (Logon)", 
         "FROM winlogbeat-* | WHERE event.code == \"4624\" | STATS count = COUNT(*) | LIMIT 1"),
        
        ("Event Code 4625 (Failed Logon)", 
         "FROM winlogbeat-* | WHERE event.code == \"4625\" | STATS count = COUNT(*) | LIMIT 1"),
        
        ("Event Code 1102 (Log Clear)", 
         "FROM winlogbeat-* | WHERE event.code == \"1102\" | STATS count = COUNT(*) | LIMIT 1"),
    ]
    
    for description, query in test_queries:
        print(f"\n{description}:")
        try:
            result = client.execute_esql(query)
            if result and 'values' in result and result['values']:
                count = result['values'][0][0] if result['values'][0] else 0
                print(f"  ✓ Found {count} events")
            else:
                print(f"  ℹ️  No events found")
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:80]}")

if __name__ == '__main__':
    main()
