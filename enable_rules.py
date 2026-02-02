#!/usr/bin/env python3
"""
Script to enable/disable all ESQL rules
"""
import os
from pathlib import Path
import sys

def enable_all_rules(rules_dir='rules', enable=True):
    """
    Enable or disable all rules in the rules directory
    
    Args:
        rules_dir: Path to rules directory
        enable: True to enable, False to disable
    """
    rules_path = Path(rules_dir)
    
    if not rules_path.exists():
        print(f"❌ Rules directory not found: {rules_dir}")
        return
    
    # Find all YAML files
    yaml_files = list(rules_path.rglob('*.yml')) + list(rules_path.rglob('*.yaml'))
    
    print(f"Found {len(yaml_files)} rule files")
    
    modified_count = 0
    error_count = 0
    
    for yaml_file in yaml_files:
        try:
            # Read the file
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if modification is needed
            if enable:
                if 'enabled: false' in content:
                    # Replace enabled: false with enabled: true
                    new_content = content.replace('enabled: false', 'enabled: true')
                    
                    # Write back to file
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    modified_count += 1
                    print(f"✓ Enabled: {yaml_file.name}")
            else:
                if 'enabled: true' in content:
                    # Replace enabled: true with enabled: false
                    new_content = content.replace('enabled: true', 'enabled: false')
                    
                    # Write back to file
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    modified_count += 1
                    print(f"✓ Disabled: {yaml_file.name}")
                    
        except Exception as e:
            print(f"❌ Error processing {yaml_file}: {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total files: {len(yaml_files)}")
    print(f"  Modified: {modified_count}")
    print(f"  Errors: {error_count}")
    print(f"  Action: {'ENABLED' if enable else 'DISABLED'}")
    print(f"{'='*60}")
    
    if modified_count > 0:
        print("\n⚠️  Remember to restart the Flask application to reload the rules!")
        print("   Run: pkill -f 'python app.py' && source venv/bin/activate && python app.py &")

if __name__ == '__main__':
    # Parse command line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == 'disable':
            print("Disabling all rules...")
            enable_all_rules(enable=False)
        elif action == 'enable':
            print("Enabling all rules...")
            enable_all_rules(enable=True)
        else:
            print("Usage: python enable_rules.py [enable|disable]")
            print("  enable  - Enable all rules (default)")
            print("  disable - Disable all rules")
            sys.exit(1)
    else:
        # Default action: enable all rules
        print("Enabling all rules...")
        enable_all_rules(enable=True)
