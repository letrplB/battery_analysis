#!/usr/bin/env python3
"""
Debug script to check cycle detection.
"""

from battery_cycle_analyzer.src.analyzer import load_data
import pandas as pd

def debug_cycle_detection():
    """Debug cycle detection logic."""
    
    print("🔍 Debugging cycle detection...")
    
    # Load the data file
    with open('import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt', 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Parse data
    df = load_data(content)
    print(f"✅ Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Filter to only charge and discharge commands
    df_filtered = df[df['Command'].isin(['Charge', 'Discharge'])].copy()
    print(f"📊 After command filtering: {df_filtered.shape[0]} rows")
    
    # Check State values in filtered data
    print(f"\n📊 State values in filtered data:")
    state_counts = df_filtered['State'].value_counts()
    for state, count in state_counts.items():
        print(f"   State {state}: {count} rows")
    
    # Detect cycle starts (when State equals 2)
    state_is_2 = df_filtered['State'] == 2
    charge_starts = state_is_2 & (df_filtered['Command'] == 'Charge')
    discharge_starts = state_is_2 & (df_filtered['Command'] == 'Discharge')
    cycle_starts = charge_starts | discharge_starts
    
    print(f"\n🔄 Cycle detection:")
    print(f"   State equals 2: {state_is_2.sum()}")
    print(f"   Charge starts: {charge_starts.sum()}")
    print(f"   Discharge starts: {discharge_starts.sum()}")
    print(f"   Total cycle starts: {cycle_starts.sum()}")
    
    # Assign cycle numbers
    df_filtered['CycleNumber'] = cycle_starts.cumsum()
    
    print(f"   Max cycle number: {df_filtered['CycleNumber'].max()}")
    print(f"   Unique cycle numbers: {df_filtered['CycleNumber'].nunique()}")
    
    # Check first few cycles
    print(f"\n📋 First few cycles:")
    for cycle_num in range(1, min(6, df_filtered['CycleNumber'].max() + 1)):
        cycle_data = df_filtered[df_filtered['CycleNumber'] == cycle_num]
        if len(cycle_data) > 0:
            command = cycle_data['Command'].iloc[0]
            start_time = cycle_data['Time[h]'].min()
            end_time = cycle_data['Time[h]'].max()
            duration = end_time - start_time
            print(f"   Cycle {cycle_num}: {command}, {len(cycle_data)} points, {duration:.4f}h duration")

if __name__ == "__main__":
    debug_cycle_detection() 