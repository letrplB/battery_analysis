#!/usr/bin/env python3
"""
Test script for test plan parsing functionality.
"""

from battery_cycle_analyzer.src.gui import parse_test_plan

def test_testplan_parsing():
    """Test the test plan parsing with the provided file."""
    
    # Read the test plan file
    with open('import_data/KMO 10x3cyc RC 1000 cycles stability 4h pause.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📋 Testing test plan parsing...")
    print(f"File content length: {len(content)} characters")
    print()
    
    # Parse the test plan
    try:
        configs = parse_test_plan(content)
        
        print(f"✅ Successfully parsed {len(configs)} C-rate periods:")
        print()
        
        for i, config in enumerate(configs):
            print(f"Period {i+1}:")
            print(f"  Cycles: {config['start_cycle']} - {config['end_cycle']}")
            print(f"  Charge C-rate: {config['charge_crate']}")
            print(f"  Discharge C-rate: {config['discharge_crate']}")
            print()
        
        # Calculate total cycles
        total_cycles = sum(config['end_cycle'] - config['start_cycle'] + 1 for config in configs)
        print(f"📊 Total cycles covered: {total_cycles}")
        
        # Show some sample lines from the file for debugging
        print("\n📄 Sample lines from test plan:")
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):
            if line.strip():
                print(f"{i+1:2d}: {line}")
        
    except Exception as e:
        print(f"❌ Error parsing test plan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_testplan_parsing() 