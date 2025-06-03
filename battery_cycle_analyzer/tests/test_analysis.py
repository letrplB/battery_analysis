#!/usr/bin/env python3
"""
Test script to verify the fixed battery cycle analysis
"""

import pandas as pd
from battery_cycle_analyzer.src.analyzer import load_data_from_file, analyze_cycles

def main():
    print("🔬 Testing fixed battery cycle analysis...")
    
    # Load the raw data
    file_path = "import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt"
    print(f"📂 Loading data from: {file_path}")
    
    try:
        df = load_data_from_file(file_path)
        print(f"✅ Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Show first few rows to verify parsing
        print("\n🔍 First 5 rows of parsed data:")
        print(df.head())
        
        print(f"\n📊 Command distribution:")
        print(df['Command'].value_counts())
        
        print(f"\n📊 State distribution:")
        print(df['State'].value_counts())
        
        # Test analysis with simple parameters
        active_material_weight = 0.002  # grams
        theoretical_capacity = 0.05    # Ah
        
        # Simple C-rate configuration for testing
        crate_configs = [
            {'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}
        ]
        
        print(f"\n🧮 Running cycle analysis...")
        results_df, summary = analyze_cycles(
            df, 
            active_material_weight, 
            theoretical_capacity, 
            method="State-based",
            crate_configs=crate_configs
        )
        
        if not results_df.empty:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📈 Results summary:")
            print(f"   Total half-cycles: {len(results_df)}")
            print(f"   First 10 cycles:")
            print(results_df[['Cycle_Number', 'Half_Cycle_Type', 'Capacity_Ah', 'Duration_h']].head(10))
            
            # Check capacity values
            print(f"\n📊 Capacity statistics:")
            print(f"   Mean capacity: {results_df['Capacity_Ah'].mean():.6f} Ah")
            print(f"   Min capacity: {results_df['Capacity_Ah'].min():.6f} Ah")
            print(f"   Max capacity: {results_df['Capacity_Ah'].max():.6f} Ah")
            
        else:
            print("❌ No results generated!")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 