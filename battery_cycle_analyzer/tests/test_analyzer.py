#!/usr/bin/env python3
"""
Test script for the battery cycle analyzer.
This script tests the core functionality with the provided data file.
"""

import sys
import os
from battery_cycle_analyzer.src.analyzer import parse_header, load_data_from_file, analyze_cycles

def test_analyzer():
    """Test the analyzer with the sample data file."""
    
    # Path to the test data file
    data_file = "import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt"
    
    if not os.path.exists(data_file):
        print(f"❌ Test data file not found: {data_file}")
        return False
    
    print("🔋 Testing Battery Cycle Analyzer")
    print("=" * 40)
    
    try:
        # Read file content with encoding handling
        print("📁 Reading data file...")
        
        # Try different encodings for header parsing
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        file_content = None
        
        for encoding in encodings:
            try:
                with open(data_file, 'r', encoding=encoding) as f:
                    file_content = f.read()
                print(f"✅ File loaded with {encoding} encoding: {len(file_content)} characters")
                break
            except UnicodeDecodeError:
                continue
        
        if file_content is None:
            print(f"❌ Could not decode file with any encoding")
            return False
        
        # Parse header
        print("📋 Parsing metadata...")
        metadata = parse_header(file_content)
        print(f"✅ Found {len(metadata)} metadata entries")
        
        for key, value in list(metadata.items())[:5]:  # Show first 5 entries
            print(f"   {key}: {value}")
        if len(metadata) > 5:
            print(f"   ... and {len(metadata) - 5} more entries")
        
        # Load data using the new function
        print("📊 Loading data...")
        df = load_data_from_file(data_file)
        print(f"✅ Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"   Columns: {list(df.columns)}")
        
        # Check for required columns
        required_cols = ['Time[h]', 'Command', 'U[V]', 'I[A]', 'State']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Missing columns: {missing_cols}")
        else:
            print("✅ All required columns present")
        
        # Check for discharge data
        if 'Command' in df.columns:
            discharge_count = len(df[df['Command'].str.lower() == 'discharge'])
            print(f"📈 Found {discharge_count} discharge data points")
        
        # Test analysis with small weight for testing
        print("🔍 Running cycle analysis...")
        active_material_weight = 0.05  # 50 mg as mentioned in test name
        theoretical_capacity = 0.050  # 50 mAh theoretical capacity
        
        results_df, summary = analyze_cycles(df, active_material_weight, theoretical_capacity, "State-based")
        
        if results_df.empty:
            print("❌ No cycles found in analysis")
            return False
        
        print(f"✅ Analysis completed successfully!")
        print(f"   Total half-cycles found: {len(results_df)}")
        print(f"   Charge cycles: {summary.get('Total_Charge_Cycles', 0)}")
        print(f"   Discharge cycles: {summary.get('Total_Discharge_Cycles', 0)}")
        print(f"   C-rate groups: {summary.get('C_Rate_Groups', 0)}")
        if summary.get('Total_Discharge_Cycles', 0) > 0:
            print(f"   Initial discharge capacity: {summary['Initial_Discharge_Capacity_Ah']:.6f} Ah")
            print(f"   Final discharge capacity: {summary['Final_Discharge_Capacity_Ah']:.6f} Ah")
            print(f"   Discharge capacity retention: {summary['Discharge_Capacity_Retention_%']:.1f}%")
        print(f"   Test duration: {summary['Total_Test_Duration_h']:.1f} hours")
        
        # Show first few cycles
        print("\n📋 First 5 cycles:")
        print(results_df.head().to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_analyzer()
    sys.exit(0 if success else 1) 