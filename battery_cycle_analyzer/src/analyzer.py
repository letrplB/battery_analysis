"""
Battery Cycle Stability Data Analysis Core Module

This module provides core functions for analyzing battery cycle data from Basytec Battery Test System.
"""

import pandas as pd
import numpy as np
from scipy import integrate
import itertools
import re
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from io import StringIO


def parse_header(file_content: str) -> Dict[str, str]:
    """
    Parse metadata from the header lines (starting with ~) of the Basytec file.
    
    Args:
        file_content: Raw file content as string
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {}
    lines = file_content.split('\n')
    
    for line in lines:
        if not line.startswith('~'):
            break
            
        # Skip empty metadata lines and column header line
        if line.strip() == '~' or 'Time[h]' in line:
            continue
            
        # Extract key-value pairs from metadata lines
        if ':' in line:
            key_value = line[1:].strip()  # Remove ~ prefix
            if ':' in key_value:
                key, value = key_value.split(':', 1)
                metadata[key.strip()] = value.strip()
    
    return metadata


def load_data_from_file(file_path: str) -> pd.DataFrame:
    """
    Load data from Basytec file, handling different encodings and skipping metadata headers.
    
    Args:
        file_path: Path to the data file
        
    Returns:
        DataFrame with the battery test data
    """
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                file_content = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode file with any of the tried encodings: {encodings}")
    
    return load_data(file_content)


def load_data(file_content: str) -> pd.DataFrame:
    """
    Load data from Basytec file content, skipping metadata headers.
    Optimized for large files up to 300 MB.
    
    Args:
        file_content: Raw file content as string
        
    Returns:
        DataFrame with the battery test data
    """
    # Check file size and provide memory management for large files
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > 50:
        print(f"📊 Processing large file ({file_size_mb:.1f} MB)...")
    
    lines = file_content.split('\n')
    
    # Find the column header line and data lines
    header_line = None
    data_lines = []
    found_header = False
    
    for i, line in enumerate(lines):
        if line.startswith('~Time[h]'):
            # This is the column header line
            header_line = line[1:].strip()  # Remove ~ prefix
            found_header = True
        elif found_header and not line.startswith('~') and line.strip():
            # This is a data line
            data_lines.append(line.strip())
    
    if not header_line:
        raise ValueError("Could not find column header line starting with '~Time[h]'")
    
    if not data_lines:
        raise ValueError("No data lines found after header")
    
    # Debug: Check first few data lines to understand structure
    print(f"🔍 Header: {header_line}")
    print(f"🔍 First data line: {data_lines[0]}")
    
    # The issue is that DateTime field contains spaces (e.g., "05.05.2025 14:36:06")
    # We need to handle this properly by either:
    # 1. Combining the date and time parts, or
    # 2. Using a different parsing approach
    
    # Let's manually parse each line to handle the DateTime field correctly
    parsed_data = []
    header_parts = header_line.split()
    
    print(f"🔍 Expected columns: {len(header_parts)}")
    print(f"🔍 Header parts: {header_parts[:10]}...")  # Show first 10 columns
    
    for line in data_lines:
        parts = line.split()
        
        # The DateTime field is split into date and time parts
        # We need to combine them back
        if len(parts) >= 4:  # Ensure we have enough parts
            # Combine date and time parts (positions 2 and 3)
            datetime_combined = f"{parts[2]} {parts[3]}"
            # Reconstruct the line with combined datetime
            new_parts = parts[:2] + [datetime_combined] + parts[4:]
            parsed_data.append(new_parts)
        else:
            print(f"⚠️  Skipping malformed line: {line}")
    
    if not parsed_data:
        raise ValueError("No valid data lines could be parsed")
    
    print(f"🔍 First parsed line: {parsed_data[0][:10]}...")  # Show first 10 fields
    print(f"🔍 Parsed line length: {len(parsed_data[0])}")
    
    # Create DataFrame manually with optimized memory usage for large files
    if file_size_mb > 100:
        print(f"💾 Creating DataFrame from {len(parsed_data):,} data rows...")
    
    df = pd.DataFrame(parsed_data, columns=header_parts)
    
    # Convert numeric columns with proper decimal handling
    numeric_cols = ['Time[h]', 't-Step[h]', 't-Set[h]', 't-Cyc[h]', 'U[V]', 'I[A]', 'Ah[Ah]', 
                   'Ah-Cyc-Charge-0', 'Ah-Cyc-Discharge-0', 'Ah-Step', 'Ah-Set', 'Ah-Ch-Set', 
                   'Ah-Dis-Set', 'Wh[Wh/kg]', 'T1[°C]', 'R-DC']
    
    for col in numeric_cols:
        if col in df.columns:
            try:
                # Replace comma with dot for decimal conversion
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
            except Exception as e:
                print(f"⚠️  Warning: Could not convert {col} to numeric: {e}")
    
    # Convert integer columns
    int_cols = ['DataSet', 'Line', 'Cyc-Count', 'Count', 'State']
    for col in int_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            except Exception as e:
                print(f"⚠️  Warning: Could not convert {col} to integer: {e}")
    
    print("✅ Data loaded and parsed successfully")
    print(f"🔍 Final Time[h] first 5 values: {df['Time[h]'].head(5).tolist()}")
    print(f"🔍 Final DataSet first 5 values: {df['DataSet'].head(5).tolist()}")
    
    return df


def detect_boundaries(df: pd.DataFrame, method: str = "State-based") -> List[int]:
    """
    Detect cycle boundaries in the data.
    
    Args:
        df: DataFrame with battery test data
        method: Method for boundary detection ("State-based" or "Zero-crossing")
        
    Returns:
        List of indices where cycle boundaries occur
    """
    if method == "State-based":
        # Find rows where State == 2 (end of cycle)
        if 'State' in df.columns:
            bounds = df.index[df['State'] == 2].tolist()
        else:
            raise ValueError("State column not found in data. Cannot use State-based boundary detection.")
    
    elif method == "Zero-crossing":
        # Find zero-crossings of current sign
        if 'I[A]' in df.columns:
            current = df['I[A]'].values
            # Find sign changes
            sign_changes = np.where(np.diff(np.sign(current)))[0]
            bounds = sign_changes.tolist()
        else:
            raise ValueError("Current column 'I[A]' not found in data. Cannot use Zero-crossing boundary detection.")
    
    else:
        raise ValueError(f"Unknown boundary detection method: {method}")
    
    return bounds


def compute_capacity(df: pd.DataFrame, active_material_weight: float, theoretical_capacity: float, method: str = "State-based", crate_configs: List[Dict] = None, logger: logging.Logger = None) -> pd.DataFrame:
    """
    Compute capacity for each charge/discharge cycle with improved filtering.
    
    Args:
        df: DataFrame with battery test data
        active_material_weight: Weight of active material in grams
        theoretical_capacity: Theoretical/nominal capacity in Ah
        method: Method for boundary detection
        crate_configs: List of C-rate configuration dictionaries
        logger: Logger instance for warnings (optional)
        
    Returns:
        DataFrame with cycle analysis results
    """
    print("🔄 Filtering data...")
    # Filter to only charge and discharge commands (remove pause, etc.)
    df_filtered = df[df['Command'].str.lower().isin(['charge', 'discharge'])].copy()
    print(f"📊 Processing {len(df_filtered):,} active data points (filtered from {len(df):,})...")
    
    if len(df_filtered) == 0:
        print("❌ No charge/discharge data found!")
        return pd.DataFrame()
    
    print("🔢 Assigning cycle numbers...")
    # Detect charge and discharge segments
    is_charge = df_filtered['Command'].str.lower() == 'charge'
    is_discharge = df_filtered['Command'].str.lower() == 'discharge'
    
    # Find starts of charge cycles (charge after non-charge)
    charge_prev = is_charge.shift(1, fill_value=False)
    charge_starts = is_charge & (~charge_prev)
    
    # Find starts of discharge cycles (discharge after non-discharge)  
    discharge_prev = is_discharge.shift(1, fill_value=False)
    discharge_starts = is_discharge & (~discharge_prev)
    
    # Assign cycle numbers using vectorized operations
    # Each charge or discharge start gets a new cycle number
    cycle_starts = charge_starts | discharge_starts
    df_filtered['CycleNumber'] = cycle_starts.cumsum()
    
    # Remove cycles with no data (cycle number 0)
    df_filtered = df_filtered[df_filtered['CycleNumber'] > 0]
    
    print("🧮 Computing capacities...")
    
    # Track warnings statistics
    warning_counts = {'too_short': 0, 'too_small': 0, 'too_large': 0}
    
    def get_crate_for_cycle(cycle_num: int, half_cycle_type: str) -> Tuple[float, float, int]:
        """Get C-rate configuration for a given cycle number and type."""
        if not crate_configs:
            return 1.0, 1.0, 1  # Default values
        
        for i, config in enumerate(crate_configs):
            start_cycle = config.get('start_cycle', 1)
            end_cycle = config.get('end_cycle', float('inf'))
            
            if start_cycle <= cycle_num <= end_cycle:
                charge_crate = config.get('charge_crate', 1.0)
                discharge_crate = config.get('discharge_crate', 1.0)
                return charge_crate, discharge_crate, i + 1
        
        # If no config found, use the last one
        if crate_configs:
            last_config = crate_configs[-1]
            return last_config.get('charge_crate', 1.0), last_config.get('discharge_crate', 1.0), len(crate_configs)
        
        return 1.0, 1.0, 1
    
    # Group by cycle number and compute capacity for each
    results = []
    total_cycles = df_filtered['CycleNumber'].max()
    
    for cycle_num, cycle_data in df_filtered.groupby('CycleNumber'):
        # Progress indicator
        if cycle_num % 100 == 1:
            print(f"   Processing group {cycle_num}/{total_cycles}...")
        
        # Determine cycle type
        command = cycle_data['Command'].iloc[0].lower()
        half_cycle_type = 'charge' if command == 'charge' else 'discharge'
        
        # Calculate time duration
        time_h = cycle_data['Time[h]'].values
        time_duration = time_h.max() - time_h.min()
        
        # Calculate capacity using trapezoidal integration
        current_a = cycle_data['I[A]'].values
        
        # Always use absolute current for capacity calculation
        capacity_ah = np.trapezoid(np.abs(current_a), time_h)
        
        # Quality checks for realistic cycles
        is_realistic = True
        warnings = []
        
        # Check 1: Minimum duration (should be at least 1 minute = 0.0167 hours)
        if time_duration < 0.01:  # Less than 0.6 minutes
            is_realistic = False
            warnings.append(f"too short ({time_duration:.4f}h)")
            warning_counts['too_short'] += 1
        
        # Check 2: Minimum capacity (should be at least 0.001 mAh = 0.000001 Ah)
        if capacity_ah < 0.000010:  # Less than 0.01 mAh
            is_realistic = False
            warnings.append(f"too small ({capacity_ah:.6f}Ah)")
            warning_counts['too_small'] += 1
        
        # Check 3: Maximum reasonable capacity (should be less than 10 Ah for typical batteries)
        if capacity_ah > 10.0:
            is_realistic = False
            warnings.append(f"too large ({capacity_ah:.6f}Ah)")
            warning_counts['too_large'] += 1
        
        # Log warnings instead of printing them
        if not is_realistic:
            warning_msg = f"Cycle {cycle_num} ({half_cycle_type}) unrealistic: {', '.join(warnings)}"
            if logger:
                logger.warning(warning_msg)
            # Only print a summary to console occasionally
            elif cycle_num % 500 == 1:
                print(f"⚠️  Warning: {warning_msg} (and more warnings - check log file)")
        
        # Calculate specific capacity
        specific_capacity_mah_per_g = (capacity_ah * 1000) / active_material_weight
        
        # Get C-rate for this cycle
        charge_crate, discharge_crate, crate_period = get_crate_for_cycle(cycle_num, half_cycle_type)
        current_crate = charge_crate if half_cycle_type == 'charge' else discharge_crate
        
        # Calculate voltage statistics
        voltage_min = cycle_data['U[V]'].min()
        voltage_max = cycle_data['U[V]'].max()
        voltage_avg = cycle_data['U[V]'].mean()
        
        # Store results
        results.append({
            'Cycle': cycle_num,
            'HalfCycleType': half_cycle_type,
            'Capacity_Ah': capacity_ah,
            'Specific_mAh_per_g': specific_capacity_mah_per_g,
            'C_Rate': current_crate,
            'C_Rate_Period': crate_period,
            'Duration_h': time_duration,
            'Voltage_Min_V': voltage_min,
            'Voltage_Max_V': voltage_max,
            'Voltage_Avg_V': voltage_avg,
            'Start_Time_h': time_h.min(),
            'End_Time_h': time_h.max(),
            'Data_Points': len(cycle_data),
            'Is_Realistic': is_realistic
        })
    
    results_df = pd.DataFrame(results)
    
    # Filter to only realistic cycles for further analysis
    realistic_cycles = results_df[results_df['Is_Realistic']].copy()
    
    print(f"✅ Analysis complete:")
    print(f"   Total half-cycles: {len(results_df)}")
    print(f"   Realistic cycles: {len(realistic_cycles)}")
    print(f"   Unrealistic cycles: {len(results_df) - len(realistic_cycles)}")
    
    # Log warning summary
    if logger:
        logger.warning("-" * 50)
        logger.warning("WARNING SUMMARY:")
        logger.warning(f"Total unrealistic cycles: {len(results_df) - len(realistic_cycles)}")
        logger.warning(f"  - Too short: {warning_counts['too_short']}")
        logger.warning(f"  - Too small capacity: {warning_counts['too_small']}")
        logger.warning(f"  - Too large capacity: {warning_counts['too_large']}")
        logger.warning("-" * 50)
    
    if len(realistic_cycles) > 0:
        charge_cycles = realistic_cycles[realistic_cycles['HalfCycleType'] == 'charge']
        discharge_cycles = realistic_cycles[realistic_cycles['HalfCycleType'] == 'discharge']
        print(f"   Realistic charge cycles: {len(charge_cycles)}")
        print(f"   Realistic discharge cycles: {len(discharge_cycles)}")
    
    return results_df


def analyze_cycles(df: pd.DataFrame, active_material_weight: float, theoretical_capacity: float, method: str = "State-based", crate_configs: List[Dict] = None, baseline_cycle: int = None, analysis_name: str = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Complete cycle analysis workflow with multiple C-rate configurations.
    
    Args:
        df: DataFrame with battery test data
        active_material_weight: Weight of active material in grams
        theoretical_capacity: Theoretical/nominal capacity in Ah (for reference)
        method: Method for boundary detection
        crate_configs: List of C-rate configuration dictionaries with cycle ranges
        baseline_cycle: Cycle number to use as baseline for retention calculation (None = use first cycle)
        analysis_name: Name for the analysis session (for logging)
        
    Returns:
        Tuple of (results DataFrame, summary statistics)
    """
    if crate_configs is None:
        crate_configs = [{'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}]
    
    # Set up logging for this analysis session
    logger = setup_analysis_logging(analysis_name)
    
    # Log analysis parameters
    logger.warning(f"Analysis parameters:")
    logger.warning(f"  Active material weight: {active_material_weight} g")
    logger.warning(f"  Theoretical capacity: {theoretical_capacity} Ah")
    logger.warning(f"  Boundary detection method: {method}")
    logger.warning(f"  C-rate configurations: {len(crate_configs)} periods")
    for i, config in enumerate(crate_configs):
        logger.warning(f"    Period {i+1}: Cycles {config['start_cycle']}-{config['end_cycle']}, Charge: {config['charge_crate']}, Discharge: {config['discharge_crate']}")
    logger.warning("-" * 50)
    
    # Compute capacity per half-cycle with logging
    results_df = compute_capacity(df, active_material_weight, theoretical_capacity, method, crate_configs, logger)
    
    if results_df.empty:
        return results_df, {}
    
    # Separate charge and discharge cycles for summary statistics
    charge_cycles = results_df[results_df['HalfCycleType'] == 'charge']
    discharge_cycles = results_df[results_df['HalfCycleType'] == 'discharge']
    
    # Compute summary statistics
    summary = {
        'Total_Half_Cycles': len(results_df),
        'Total_Charge_Cycles': len(charge_cycles),
        'Total_Discharge_Cycles': len(discharge_cycles),
        'C_Rate_Periods': len(crate_configs),
        'C_Rate_Groups': len(results_df['C_Rate_Period'].unique()),
        'Log_File': logger.handlers[0].baseFilename if logger.handlers else None,
    }
    
    # Add C-rate configuration summary
    for i, config in enumerate(crate_configs):
        summary[f'Period_{i+1}_Cycles'] = f"{config['start_cycle']}-{config['end_cycle']}"
        summary[f'Period_{i+1}_Charge_C_Rate'] = config['charge_crate']
        summary[f'Period_{i+1}_Discharge_C_Rate'] = config['discharge_crate']
    
    # Improved retention calculation using baseline cycle selection
    def calculate_retention_stats(cycles_df, cycle_type):
        """Calculate retention statistics for a specific cycle type."""
        if len(cycles_df) == 0:
            return {}
        
        # Determine baseline cycle
        if baseline_cycle is not None and baseline_cycle > 0:
            # Use specified baseline cycle - find the Nth cycle of this type
            if len(cycles_df) >= baseline_cycle:
                # Use the Nth cycle of this specific type (1-indexed)
                baseline_capacity = cycles_df.iloc[baseline_cycle - 1]['Capacity_Ah']
                logger.warning(f"Using {cycle_type} cycle #{baseline_cycle} (cycle number {cycles_df.iloc[baseline_cycle - 1]['Cycle']}) as baseline: {baseline_capacity:.6f} Ah")
            else:
                # Not enough cycles of this type, use first cycle
                baseline_capacity = cycles_df['Capacity_Ah'].iloc[0]
                logger.warning(f"Requested {cycle_type} cycle #{baseline_cycle} not available (only {len(cycles_df)} cycles), using first cycle: {baseline_capacity:.6f} Ah")
        else:
            # Use first cycle of the same C-rate as the last cycle
            last_crate = cycles_df['C_Rate'].iloc[-1]
            same_crate_cycles = cycles_df[cycles_df['C_Rate'] == last_crate]
            if len(same_crate_cycles) > 0:
                baseline_capacity = same_crate_cycles['Capacity_Ah'].iloc[0]
                logger.warning(f"Using first {cycle_type} cycle with same C-rate ({last_crate}) as baseline: {baseline_capacity:.6f} Ah")
            else:
                baseline_capacity = cycles_df['Capacity_Ah'].iloc[0]
                logger.warning(f"Using first {cycle_type} cycle as baseline: {baseline_capacity:.6f} Ah")
        
        final_capacity = cycles_df['Capacity_Ah'].iloc[-1]
        
        # Sanity check
        if not (0.001 <= baseline_capacity <= 10.0):
            logger.warning(f"{cycle_type} baseline capacity looks unrealistic: {baseline_capacity:.6f} Ah")
        if not (0.001 <= final_capacity <= 10.0):
            logger.warning(f"{cycle_type} final capacity looks unrealistic: {final_capacity:.6f} Ah")
        
        retention = (final_capacity / baseline_capacity * 100) if baseline_capacity > 0 else 0
        
        return {
            f'Initial_{cycle_type}_Capacity_Ah': baseline_capacity,
            f'Final_{cycle_type}_Capacity_Ah': final_capacity,
            f'{cycle_type}_Capacity_Retention_%': retention,
            f'Average_{cycle_type}_Capacity_Ah': cycles_df['Capacity_Ah'].mean(),
            f'{cycle_type}_Capacity_Std_Ah': cycles_df['Capacity_Ah'].std(),
        }
    
    # Add discharge-specific statistics
    if len(discharge_cycles) > 0:
        summary.update(calculate_retention_stats(discharge_cycles, 'Discharge'))
    
    # Add charge-specific statistics
    if len(charge_cycles) > 0:
        summary.update(calculate_retention_stats(charge_cycles, 'Charge'))
    
    # Overall test duration
    if len(results_df) > 0:
        summary['Total_Test_Duration_h'] = results_df['End_Time_h'].max() - results_df['Start_Time_h'].min()
    else:
        summary['Total_Test_Duration_h'] = 0
    
    return results_df, summary


def export_results(results_df: pd.DataFrame, metadata: Dict, summary: Dict, filename: str = "cycle_results.csv"):
    """
    Export results to CSV with metadata header.
    
    Args:
        results_df: DataFrame with cycle results
        metadata: Metadata dictionary from file header
        summary: Summary statistics dictionary
        filename: Output filename
    """
    with open(filename, 'w') as f:
        # Write metadata as comments
        f.write("# Battery Cycle Analysis Results\n")
        f.write("# Generated from Basytec Battery Test System data\n")
        f.write("#\n")
        
        for key, value in metadata.items():
            f.write(f"# {key}: {value}\n")
        
        f.write("#\n")
        f.write("# Summary Statistics:\n")
        for key, value in summary.items():
            f.write(f"# {key}: {value}\n")
        
        f.write("#\n")
        f.write("# Cycle Data:\n")
    
    # Append the DataFrame
    results_df.to_csv(filename, mode='a', index=False)


def setup_analysis_logging(analysis_name: str = None) -> logging.Logger:
    """
    Set up logging for a specific analysis session.
    
    Args:
        analysis_name: Name for the analysis (optional, will generate timestamp-based name if not provided)
        
    Returns:
        Logger instance for warnings
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log filename
    if analysis_name is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        analysis_name = f"analysis_{timestamp}"
    
    log_filename = os.path.join(logs_dir, f"{analysis_name}_warnings.log")
    
    # Create logger
    logger = logging.getLogger(f'cycle_warnings_{analysis_name}')
    logger.setLevel(logging.WARNING)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Log session start
    logger.warning(f"Analysis session started: {analysis_name}")
    logger.warning(f"Log file: {log_filename}")
    logger.warning("-" * 50)
    
    return logger 