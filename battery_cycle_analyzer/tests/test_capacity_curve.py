#!/usr/bin/env python3
"""
Test script to analyze capacity degradation curve
"""

import pandas as pd
import matplotlib.pyplot as plt
from battery_cycle_analyzer.src.analyzer import load_data_from_file, analyze_cycles

def plot_capacity_curve():
    print("📈 Analyzing capacity degradation curve...")
    
    # Load the raw data
    file_path = "import_data/KM-KMFO-721-F1E5(16) 50mAh 2xF.txt"
    print(f"📂 Loading data from: {file_path}")
    
    try:
        df = load_data_from_file(file_path)
        print(f"✅ Data loaded: {df.shape[0]} rows")
        
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
            print(f"\n📊 Analyzing capacity trends...")
            
            # Separate charge and discharge cycles
            charge_cycles = results_df[results_df['Half_Cycle_Type'] == 'Charge'].copy()
            discharge_cycles = results_df[results_df['Half_Cycle_Type'] == 'Discharge'].copy()
            
            # Convert cycle numbers to full cycle numbers (divide by 2)
            charge_cycles['Full_Cycle'] = (charge_cycles['Cycle_Number'] + 1) // 2
            discharge_cycles['Full_Cycle'] = discharge_cycles['Cycle_Number'] // 2
            
            print(f"   Charge cycles: {len(charge_cycles)}")
            print(f"   Discharge cycles: {len(discharge_cycles)}")
            
            # Show capacity statistics at different points
            print(f"\n📈 Capacity evolution:")
            
            # First 10 cycles
            print(f"   First 10 discharge cycles:")
            first_10 = discharge_cycles.head(10)
            for _, cycle in first_10.iterrows():
                print(f"     Cycle {cycle['Full_Cycle']}: {cycle['Capacity_Ah']:.6f} Ah")
            
            # Middle cycles (around cycle 500)
            print(f"\n   Middle cycles (around 500):")
            middle = discharge_cycles[(discharge_cycles['Full_Cycle'] >= 495) & (discharge_cycles['Full_Cycle'] <= 505)]
            for _, cycle in middle.iterrows():
                print(f"     Cycle {cycle['Full_Cycle']}: {cycle['Capacity_Ah']:.6f} Ah")
            
            # Last 10 cycles
            print(f"\n   Last 10 discharge cycles:")
            last_10 = discharge_cycles.tail(10)
            for _, cycle in last_10.iterrows():
                print(f"     Cycle {cycle['Full_Cycle']}: {cycle['Capacity_Ah']:.6f} Ah")
            
            # Calculate retention
            if len(discharge_cycles) > 0:
                initial_capacity = discharge_cycles['Capacity_Ah'].iloc[0]
                final_capacity = discharge_cycles['Capacity_Ah'].iloc[-1]
                retention = (final_capacity / initial_capacity * 100) if initial_capacity > 0 else 0
                
                print(f"\n📉 Discharge capacity retention:")
                print(f"   Initial: {initial_capacity:.6f} Ah")
                print(f"   Final: {final_capacity:.6f} Ah")
                print(f"   Retention: {retention:.1f}%")
            
            # Create a simple capacity vs cycle plot
            try:
                plt.figure(figsize=(12, 6))
                
                plt.subplot(1, 2, 1)
                plt.plot(discharge_cycles['Full_Cycle'], discharge_cycles['Capacity_Ah'] * 1000, 'b.-', alpha=0.7, label='Discharge')
                plt.plot(charge_cycles['Full_Cycle'], charge_cycles['Capacity_Ah'] * 1000, 'r.-', alpha=0.7, label='Charge')
                plt.xlabel('Full Cycle Number')
                plt.ylabel('Capacity (mAh)')
                plt.title('Battery Capacity vs Cycle Number')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                plt.subplot(1, 2, 2)
                # Only plot realistic cycles for cleaner view
                realistic_discharge = discharge_cycles[discharge_cycles['Capacity_Ah'] > 0.00001]
                if len(realistic_discharge) > 0:
                    plt.plot(realistic_discharge['Full_Cycle'], realistic_discharge['Capacity_Ah'] * 1000, 'b.-', alpha=0.7)
                    plt.xlabel('Full Cycle Number')
                    plt.ylabel('Capacity (mAh)')
                    plt.title('Discharge Capacity (Realistic Cycles Only)')
                    plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig('capacity_degradation.png', dpi=150, bbox_inches='tight')
                print(f"\n📊 Plot saved as 'capacity_degradation.png'")
                
            except Exception as e:
                print(f"⚠️  Could not create plot: {e}")
            
        else:
            print("❌ No results generated!")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    plot_capacity_curve() 