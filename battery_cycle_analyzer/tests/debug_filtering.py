#!/usr/bin/env python3
"""
Debug script to investigate filtering effects on capacity values.
"""

from battery_cycle_analyzer.src.analyzer import load_data, parse_header
import pandas as pd
import numpy as np

def debug_filtering_effects():
    """Debug what the filtering is doing to capacity values."""
    
    print("🔍 Debugging filtering effects on capacity values...")
    
    # Load the data file
    with open('import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt', 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Parse data
    df = load_data(content)
    print(f"✅ Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Filter to only charge and discharge commands
    df_filtered = df[df['Command'].isin(['charge', 'discharge'])].copy()
    print(f"📊 After command filtering: {df_filtered.shape[0]} rows")
    
    # Detect cycle starts (when State changes to 2)
    state_changes = df_filtered['State'].diff() == 2
    charge_starts = state_changes & (df_filtered['Command'] == 'charge')
    discharge_starts = state_changes & (df_filtered['Command'] == 'discharge')
    cycle_starts = charge_starts | discharge_starts
    
    # Assign cycle numbers
    df_filtered['CycleNumber'] = cycle_starts.cumsum()
    
    print(f"🔄 Total cycles detected: {df_filtered['CycleNumber'].max()}")
    
    # Analyze first 50 cycles in detail
    print(f"\n📋 Analyzing first 50 cycles in detail:")
    print(f"{'Cycle':<8} {'Type':<10} {'Duration_h':<12} {'Capacity_Ah':<15} {'Status':<20}")
    print("-" * 70)
    
    realistic_count = 0
    filtered_count = 0
    
    for cycle_num in range(1, min(51, df_filtered['CycleNumber'].max() + 1)):
        cycle_data = df_filtered[df_filtered['CycleNumber'] == cycle_num]
        
        if len(cycle_data) == 0:
            continue
            
        # Get cycle info
        cycle_type = cycle_data['Command'].iloc[0].title()
        time_h = cycle_data['Time[h]'].values
        current_a = cycle_data['I[A]'].values
        
        # Calculate duration and capacity
        duration_h = time_h[-1] - time_h[0] if len(time_h) > 1 else 0
        capacity_ah = np.trapezoid(np.abs(current_a), time_h)
        
        # Check filtering criteria
        duration_ok = duration_h >= 0.1
        capacity_ok = capacity_ah >= 0.001
        is_realistic = duration_ok and capacity_ok
        
        if is_realistic:
            realistic_count += 1
            status = "✅ Realistic"
        else:
            filtered_count += 1
            if not duration_ok:
                status = f"❌ Too short ({duration_h:.3f}h)"
            else:
                status = f"❌ Too small ({capacity_ah:.6f}Ah)"
        
        print(f"{cycle_num:<8} {cycle_type:<10} {duration_h:<12.3f} {capacity_ah:<15.6f} {status}")
    
    print(f"\n📊 Summary of first 50 cycles:")
    print(f"   Realistic cycles: {realistic_count}")
    print(f"   Filtered out: {filtered_count}")
    
    # Look at the original capacity values without filtering
    print(f"\n🔍 Original capacity analysis (no filtering):")
    
    # Find cycles with reasonable capacity (> 0.01 Ah)
    good_cycles = []
    for cycle_num in range(1, min(101, df_filtered['CycleNumber'].max() + 1)):
        cycle_data = df_filtered[df_filtered['CycleNumber'] == cycle_num]
        
        if len(cycle_data) == 0:
            continue
            
        time_h = cycle_data['Time[h]'].values
        current_a = cycle_data['I[A]'].values
        capacity_ah = np.trapezoid(np.abs(current_a), time_h)
        
        if capacity_ah > 0.01:  # Look for cycles with > 0.01 Ah
            good_cycles.append({
                'cycle': cycle_num,
                'type': cycle_data['Command'].iloc[0],
                'capacity': capacity_ah,
                'duration': time_h[-1] - time_h[0] if len(time_h) > 1 else 0
            })
    
    print(f"   Found {len(good_cycles)} cycles with capacity > 0.01 Ah:")
    for cycle in good_cycles[:10]:  # Show first 10
        print(f"   Cycle {cycle['cycle']} ({cycle['type']}): {cycle['capacity']:.4f} Ah, {cycle['duration']:.2f}h")
    
    # Check what the theoretical capacity should be
    print(f"\n🔋 Theoretical capacity analysis:")
    print(f"   Input theoretical capacity: 0.050 Ah")
    print(f"   Expected realistic range: 0.040-0.060 Ah (80-120% of theoretical)")
    
    # Look for cycles in the expected range
    expected_cycles = [c for c in good_cycles if 0.040 <= c['capacity'] <= 0.060]
    print(f"   Cycles in expected range: {len(expected_cycles)}")
    
    if expected_cycles:
        print(f"   First few expected cycles:")
        for cycle in expected_cycles[:5]:
            print(f"   Cycle {cycle['cycle']} ({cycle['type']}): {cycle['capacity']:.4f} Ah")

if __name__ == "__main__":
    debug_filtering_effects() 