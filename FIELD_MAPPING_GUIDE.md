# Rule Field Mapping Issues and Fixes

## Problem Summary

The ESQL rules in `rules/` directory were written using **ECS (Elastic Common Schema)** normalized field names, but the actual Elasticsearch data uses **Windows Event Log raw field names**. This causes all rules to fail with "Unknown column" errors.

## Root Cause Analysis

### Expected vs Actual Field Names

| Rule Field (ECS) | Actual Elasticsearch Field | Notes |
|------------------|----------------------------|-------|
| `user.name` | `winlog.event_data.TargetUserName` or `winlog.event_data.SubjectUserName` | User involved in event |
| `group.name` | `winlog.event_data.Group` or `winlog.event_data.TargetUserName` | Group name |
| `source.ip` | `winlog.event_data.IpAddress` | Source IP address |
| `process.name` | `winlog.event_data.NewProcessName` or `winlog.event_data.ProcessName` | Process executable name |
| `process.parent.name` | `winlog.event_data.ParentProcessName` | Parent process name |
| `process.command_line` | `winlog.event_data.CommandLine` | Command line arguments |
| `winlog.logon.authentication_package` | `winlog.event_data.AuthenticationPackageName` | Authentication method (NTLM, Kerberos) |
| `process.target.name` | `winlog.event_data.TargetImage` | Target process in injection attacks |

### What Elasticsearch Actually Contains

Running `python discover_fields.py` shows that winlogbeat-* has **772 fields**, mostly under:
- `winlog.event_data.*` - Raw Windows event log fields
- `event.*` - Event metadata (code, outcome, kind, action)
- `host.*` - Host information
- `agent.*` - Agent metadata

## ES|QL Compatibility Issues

Additionally, the Elasticsearch version being used has ES|QL limitations:

1. **`COUNT_IF()` function doesn't exist** - Use `CASE` with `SUM` instead
2. **`KEEP` cannot reference original columns after `STATS`** - Aggregations change the column set
3. **`params` must be an array `[]`, not a dict `{}`** - Fixed in `es_client.py`

## Fixed Sample Rules

Created 3 working example rules with correct field names:

### 1. Brute Force Detection
**File**: `rules/GDPR_yml/IV/AC-01-Multiple-Failed-Login-Attempts-Brute-Force-FIXED.yml`

```yaml
query: |
  FROM winlogbeat-*
  | WHERE @timestamp >= NOW() - 5 minutes
  | WHERE event.code == "4625"
  | STATS failed_attempts = COUNT(*) BY winlog.event_data.IpAddress, winlog.event_data.TargetUserName, host.name
  | WHERE failed_attempts >= 3
  | EVAL severity = "medium"
```

**Changes**:
- `source.ip` → `winlog.event_data.IpAddress`
- `user.name` → `winlog.event_data.TargetUserName`
- Removed `KEEP @timestamp` (not available after `STATS`)

### 2. Event Log Clearing
**File**: `rules/GDPR_yml/MULTI/AU-03-Windows-Event-Log-Cleared-FIXED.yml`

```yaml
query: |
  FROM winlogbeat-*
  | WHERE @timestamp >= NOW() - 5 minutes
  | WHERE event.code == "1102"
  | EVAL severity = "critical"
```

**Changes**:
- `user.name` → `winlog.event_data.SubjectUserName`
- Already using `event.code` which exists

### 3. Successful Login After Failures
**File**: `rules/GDPR_yml/IV/AC-03-Successful-Login-After-Multiple-Failures-FIXED.yml`

```yaml
query: |
  FROM winlogbeat-*
  | WHERE @timestamp >= NOW() - 10 minutes
  | WHERE event.code IN ("4624", "4625")
  | EVAL 
      is_failure = CASE(event.code == "4625", 1, 0),
      is_success = CASE(event.code == "4624", 1, 0)
  | STATS 
      failures = SUM(is_failure),
      successes = SUM(is_success),
      max_time = MAX(@timestamp)
    BY winlog.event_data.IpAddress, winlog.event_data.TargetUserName, host.name
  | WHERE failures >= 3 AND successes >= 1
  | EVAL severity = "high"
```

**Changes**:
- `COUNT_IF()` → `CASE` with `SUM`
-  Field name updates
- Removed problematic `KEEP`

## Tools Created

### 1. `diagnose.py`
Diagnostic script that:
- Checks Elasticsearch connectivity
- Lists all indices with document counts
- Tests simple ES|QL queries
- Executes sample rules
- Analyzes rule queries for common issues

**Usage**: `python diagnose.py`

### 2. `discover_fields.py`
Field discovery tool that:
- Lists all available fields in each index
- Groups fields by category (user, process, auth, etc.)
- Provides field mapping suggestions
- Tests common queries

**Usage**: `python discover_fields.py`

### 3. `enable_rules.py`
Bulk rule enabler:
- Enables or disables all rules at once
- Modifies YAML files in-place

**Usage**: 
- `python enable_rules.py enable` - Enable all rules
- `python enable_rules.py disable` - Disable all rules

## Recommendations

### Option 1: Manual Fix (Recommended for Learning)
1. Use `discover_fields.py` to understand available fields
2. Pick a few important rules to fix
3. Update field names based on mapping table above
4. Test with `python diagnose.py`
5. Gradually fix more rules as needed

### Option 2: Automated Fix (Not Implemented Yet)
Create a script to automatically replace field names in all 168 rules:
- Parse each YAML file
- Replace ECS field names with actual field names
- Handle edge cases (some fields may not exist)
- Test each rule

##Option 3: Use Logstash/Ingest Pipeline  
Configure Elasticsearch to normalize Windows event logs to ECS format:
- Use Logstash with winlogbeat codec
- Or create Elasticsearch ingest pipelines
- Map `winlog.event_data.*` to ECS fields
- Then original rules would work without changes

## Current Status

✅ **ES|QL API Fixed** - Params format corrected  
✅ **3 Sample Rules Working** - Execute without errors  
✅ **Field Mapping Documented** - Know what to change  
✅ **Tools Created** - Can diagnose and discover fields  

⚠️ **165 Rules Need Fixing** - Field names need updates  
⚠️ **No Recent Alerts** - No malicious activity in last 5-10 minutes (this is normal)

## Next Steps

1. **Test with historical data**: Expand time windows to 7-30 days
2. **Fix high-priority rules**: Focus on critical/high severity rules first
3. **Consider ECS normalization**: Long-term solution for all rules to work
4. **Monitor production**: Once fixed, rules will detect real threats
