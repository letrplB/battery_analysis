#!/usr/bin/env python3
"""
Debug script to check what command values are actually in the data.
"""

from battery_cycle_analyzer.src.analyzer import load_data
import pandas as pd

def debug_commands():
    """Check what command values are in the data."""
    
    print("🔍 Debugging command values in the data...")
    
    # Load the data file
    with open('import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt', 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Parse data
    df = load_data(content)
    print(f"✅ Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Check unique command values
    print(f"\n📊 Unique Command values:")
    command_counts = df['Command'].value_counts()
    for cmd, count in command_counts.items():
        print(f"   '{cmd}': {count} rows")
    
    # Check State values
    print(f"\n📊 Unique State values:")
    state_counts = df['State'].value_counts()
    for state, count in state_counts.items():
        print(f"   {state}: {count} rows")
    
    # Look at first few rows with different commands
    print(f"\n📋 Sample data for each command:")
    for cmd in command_counts.index[:5]:  # Show first 5 command types
        sample = df[df['Command'] == cmd].head(3)
        print(f"\n   Command '{cmd}':")
        for idx, row in sample.iterrows():
            print(f"     Time: {row['Time[h]']:.6f}h, State: {row['State']}, Current: {row['I[A]']:.6f}A")

if __name__ == "__main__":
    debug_commands() 