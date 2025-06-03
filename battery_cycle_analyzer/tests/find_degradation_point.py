#!/usr/bin/env python3
"""
Find where capacity degradation starts
"""

import pandas as pd
from battery_cycle_analyzer.src.analyzer import load_data_from_file, analyze_cycles

def find_degradation_point():
    print("🔍 Finding capacity degradation point...")
    
    # Load the raw data
    file_path = "import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt"
    df = load_data_from_file(file_path)
    
    # Test analysis with simple parameters
    active_material_weight = 0.002  # grams
    theoretical_capacity = 0.05    # Ah
    
    crate_configs = [
        {'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}
    ]
    
    # Run analysis but suppress most warnings
    import sys
    from io import StringIO
    
    # Redirect stdout to suppress warnings
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        results_df, summary = analyze_cycles(
            df, 
            active_material_weight, 
            theoretical_capacity, 
            method="State-based",
            crate_configs=crate_configs
        )
    finally:
        sys.stdout = old_stdout
    
    # Analyze discharge cycles
    discharge_cycles = results_df[results_df['Half_Cycle_Type'] == 'Discharge'].copy()
    discharge_cycles['Full_Cycle'] = discharge_cycles['Cycle_Number'] // 2
    
    print(f"✅ Analysis complete. Found {len(discharge_cycles)} discharge cycles")
    
    # Find degradation transitions
    print(f"\n📉 Capacity degradation analysis:")
    
    # Show cycles 1-50
    print(f"\nCycles 1-50:")
    early_cycles = discharge_cycles[discharge_cycles['Full_Cycle'] <= 50]
    for i in range(0, min(50, len(early_cycles)), 5):
        cycle = early_cycles.iloc[i]
        print(f"  Cycle {cycle['Full_Cycle']:3d}: {cycle['Capacity_Ah']:.6f} Ah")
    
    # Find where capacity drops below thresholds
    significant_capacity = discharge_cycles[discharge_cycles['Capacity_Ah'] >= 0.00005]  # 0.05 mAh
    small_capacity = discharge_cycles[(discharge_cycles['Capacity_Ah'] >= 0.000001) & (discharge_cycles['Capacity_Ah'] < 0.00005)]
    zero_capacity = discharge_cycles[discharge_cycles['Capacity_Ah'] < 0.000001]
    
    print(f"\n📊 Capacity distribution:")
    print(f"  Significant capacity (≥0.05 mAh): {len(significant_capacity)} cycles")
    print(f"  Small capacity (0.001-0.05 mAh): {len(small_capacity)} cycles") 
    print(f"  Near-zero capacity (<0.001 mAh): {len(zero_capacity)} cycles")
    
    # Find transition points
    if len(significant_capacity) > 0:
        last_good_cycle = significant_capacity['Full_Cycle'].max()
        print(f"  Last cycle with significant capacity: {last_good_cycle}")
    
    if len(zero_capacity) > 0:
        first_dead_cycle = zero_capacity['Full_Cycle'].min()
        print(f"  First cycle with near-zero capacity: {first_dead_cycle}")
    
    # Show transition region
    if len(significant_capacity) > 0 and len(zero_capacity) > 0:
        transition_start = max(1, last_good_cycle - 10)
        transition_end = min(len(discharge_cycles), first_dead_cycle + 10)
        
        print(f"\n🔄 Transition region (cycles {transition_start}-{transition_end}):")
        transition_cycles = discharge_cycles[
            (discharge_cycles['Full_Cycle'] >= transition_start) & 
            (discharge_cycles['Full_Cycle'] <= transition_end)
        ]
        
        for _, cycle in transition_cycles.iterrows():
            capacity_mah = cycle['Capacity_Ah'] * 1000
            print(f"  Cycle {cycle['Full_Cycle']:3d}: {capacity_mah:6.3f} mAh ({cycle['Capacity_Ah']:.6f} Ah)")

if __name__ == "__main__":
    find_degradation_point() 