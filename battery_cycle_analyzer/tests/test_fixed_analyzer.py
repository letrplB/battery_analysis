#!/usr/bin/env python3
"""
Test script to verify the fixed analyzer works correctly.
"""

from battery_cycle_analyzer.src.analyzer import load_data, analyze_cycles, parse_header

def test_fixed_analyzer():
    """Test the fixed analyzer with correct command names and column names."""
    
    print("🧪 Testing fixed analyzer...")
    
    # Load the data file
    with open('import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt', 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Parse metadata
    metadata = parse_header(content)
    print(f"✅ Metadata parsed: {len(metadata)} items")
    
    # Load and parse data
    df = load_data(content)
    print(f"✅ Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Test parameters
    active_material_weight = 1.0  # grams
    theoretical_capacity = 0.050  # Ah
    crate_configs = [
        {'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}
    ]
    
    # Run analysis
    print(f"\n🔄 Running cycle analysis...")
    results_df, summary = analyze_cycles(
        df, 
        active_material_weight, 
        theoretical_capacity, 
        "State-based", 
        crate_configs, 
        baseline_cycle=0  # Auto-select
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"   Results shape: {results_df.shape}")
    print(f"   Columns: {list(results_df.columns)}")
    
    if not results_df.empty:
        print(f"\n📋 First 10 cycles:")
        print(results_df.head(10)[['Cycle_Number', 'Half_Cycle_Type', 'Capacity_Ah', 'Duration_h', 'Is_Realistic']])
        
        # Check for cycle 31
        cycle_31 = results_df[results_df['Cycle_Number'] == 31]
        if not cycle_31.empty:
            print(f"\n🎯 Found Cycle 31:")
            for idx, row in cycle_31.iterrows():
                print(f"   {row['Half_Cycle_Type']}: {row['Capacity_Ah']:.6f} Ah, {row['Duration_h']:.3f}h, Realistic: {row['Is_Realistic']}")
        else:
            print(f"\n❌ Cycle 31 not found")
        
        # Summary statistics
        print(f"\n📈 Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    else:
        print(f"❌ No results found!")

if __name__ == "__main__":
    test_fixed_analyzer() 