"""
dQ/dU (Differential Capacity) Analysis Module

This module provides functions for analyzing battery differential capacity (dQ/dU),
which is useful for identifying phase transitions and degradation mechanisms.
"""

import numpy as np
import pandas as pd
from scipy import interpolate, signal
from typing import Dict, List, Tuple, Optional, Any
import logging


def extract_cycle_data(df: pd.DataFrame, cycle_number: int, half_cycle_type: str = 'discharge') -> pd.DataFrame:
    """
    Extract specific half-cycle data for dQ/dU analysis.
    
    Args:
        df: Main dataframe with battery data
        cycle_number: Cycle number to extract
        half_cycle_type: 'charge' or 'discharge'
        
    Returns:
        DataFrame with the extracted cycle data
    """
    # Filter to charge/discharge commands only
    df_filtered = df[df['Command'].str.lower().isin(['charge', 'discharge'])].copy()
    
    # Detect cycles
    is_charge = df_filtered['Command'].str.lower() == 'charge'
    is_discharge = df_filtered['Command'].str.lower() == 'discharge'
    
    # Find starts of cycles
    charge_prev = is_charge.shift(1, fill_value=False)
    charge_starts = is_charge & (~charge_prev)
    
    discharge_prev = is_discharge.shift(1, fill_value=False)
    discharge_starts = is_discharge & (~discharge_prev)
    
    # Assign cycle numbers
    cycle_starts = charge_starts | discharge_starts
    df_filtered['CycleNumber'] = cycle_starts.cumsum()
    
    # Filter to the specific cycle and type
    cycle_data = df_filtered[
        (df_filtered['CycleNumber'] == cycle_number) & 
        (df_filtered['Command'].str.lower() == half_cycle_type.lower())
    ].copy()
    
    if cycle_data.empty:
        raise ValueError(f"No data found for cycle {cycle_number} ({half_cycle_type})")
    
    return cycle_data


def interpolate_voltage_capacity(voltage: np.ndarray, capacity: np.ndarray, 
                                n_points: int = 333) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpolate V-Q data to uniform grid for consistent differentiation.
    
    Args:
        voltage: Voltage data array
        capacity: Capacity data array
        n_points: Number of interpolation points (default: 333)
        
    Returns:
        Tuple of (interpolated_voltage, interpolated_capacity)
    """
    # Remove any NaN values
    mask = ~(np.isnan(voltage) | np.isnan(capacity))
    voltage = voltage[mask]
    capacity = capacity[mask]
    
    if len(voltage) < 2:
        raise ValueError("Insufficient data points for interpolation")
    
    # Sort by voltage for interpolation
    sort_idx = np.argsort(voltage)
    voltage_sorted = voltage[sort_idx]
    capacity_sorted = capacity[sort_idx]
    
    # Remove duplicates
    unique_mask = np.diff(voltage_sorted, prepend=-np.inf) > 1e-10
    voltage_unique = voltage_sorted[unique_mask]
    capacity_unique = capacity_sorted[unique_mask]
    
    if len(voltage_unique) < 2:
        raise ValueError("Insufficient unique voltage points for interpolation")
    
    # Create uniform voltage grid
    v_min, v_max = voltage_unique.min(), voltage_unique.max()
    v_interp = np.linspace(v_min, v_max, n_points)
    
    # Interpolate capacity
    interp_func = interpolate.interp1d(voltage_unique, capacity_unique, 
                                       kind='cubic', bounds_error=False, 
                                       fill_value='extrapolate')
    q_interp = interp_func(v_interp)
    
    return v_interp, q_interp


def calculate_dq_du(voltage: np.ndarray, capacity: np.ndarray, 
                    smoothing: Optional[Dict] = None) -> np.ndarray:
    """
    Calculate differential capacity dQ/dU.
    
    Args:
        voltage: Voltage data (should be uniformly spaced)
        capacity: Capacity data
        smoothing: Optional smoothing parameters
        
    Returns:
        dQ/dU values array
    """
    # Apply smoothing to capacity before differentiation if requested
    if smoothing:
        capacity = apply_smoothing(capacity, smoothing)
    
    # Calculate numerical derivative dQ/dV
    dv = np.gradient(voltage)
    dq = np.gradient(capacity)
    
    # Avoid division by zero
    dv[np.abs(dv) < 1e-10] = 1e-10
    
    # Calculate dQ/dU (differential capacity)
    dq_du = dq / dv
    
    # Convert from Ah/V to mAh/V for better scaling
    dq_du = dq_du * 1000
    
    return dq_du


def apply_smoothing(data: np.ndarray, params: Dict) -> np.ndarray:
    """
    Apply smoothing to data based on specified method.
    
    Args:
        data: Input data array
        params: Smoothing parameters dictionary
            - method: 'savgol', 'moving_avg', or 'gaussian'
            - Additional method-specific parameters
            
    Returns:
        Smoothed data array
    """
    method = params.get('method', 'savgol')
    
    if method == 'savgol':
        window = params.get('window', 11)
        poly = params.get('poly', 3)
        # Ensure window is odd
        if window % 2 == 0:
            window += 1
        # Ensure we have enough points
        if len(data) <= window:
            return data
        return signal.savgol_filter(data, window, poly)
    
    elif method == 'moving_avg':
        window = params.get('window', 5)
        if len(data) <= window:
            return data
        kernel = np.ones(window) / window
        # Use mode='valid' and pad to maintain array size
        smoothed = np.convolve(data, kernel, mode='valid')
        # Pad the edges
        pad_width = (window - 1) // 2
        smoothed = np.pad(smoothed, (pad_width, window - 1 - pad_width), mode='edge')
        return smoothed
    
    elif method == 'gaussian':
        sigma = params.get('sigma', 1.0)
        return signal.gaussian_filter1d(data, sigma)
    
    else:
        return data


def detect_peaks(dq_du: np.ndarray, voltage: np.ndarray, 
                prominence: float = 0.1) -> Dict:
    """
    Identify peaks in dQ/dU curve (phase transitions).
    
    Args:
        dq_du: Differential capacity values
        voltage: Corresponding voltage values
        prominence: Minimum prominence for peak detection
        
    Returns:
        Dictionary with peak information
    """
    # Find peaks
    peaks, properties = signal.find_peaks(dq_du, prominence=prominence)
    
    if len(peaks) == 0:
        return {
            'peak_indices': [],
            'peak_voltages': [],
            'peak_intensities': [],
            'prominences': []
        }
    
    return {
        'peak_indices': peaks.tolist(),
        'peak_voltages': voltage[peaks].tolist(),
        'peak_intensities': dq_du[peaks].tolist(),
        'prominences': properties['prominences'].tolist()
    }


def compute_dqdu_analysis(df: pd.DataFrame, cycle_selections: List[Tuple[int, str]], 
                         params: Dict[str, Any]) -> Dict:
    """
    Main dQ/dU analysis pipeline.
    
    Args:
        df: Main dataframe with battery data
        cycle_selections: List of (cycle_num, half_cycle_type) tuples
        params: Dictionary with analysis parameters
            - n_points: Interpolation points (default: 333)
            - voltage_range: (min, max) tuple or None
            - smoothing: Smoothing method and parameters
            - peak_detection: Enable/disable peak finding
            - peak_prominence: Minimum prominence for peaks
    
    Returns:
        Dictionary with dQ/dU results for each selected cycle
    """
    results = {}
    
    for cycle_num, half_cycle_type in cycle_selections:
        try:
            # Extract cycle data
            cycle_data = extract_cycle_data(df, cycle_num, half_cycle_type)
            
            # Get voltage and capacity data
            voltage = cycle_data['U[V]'].values
            
            # Use appropriate capacity column based on cycle type
            if half_cycle_type.lower() == 'discharge':
                capacity_col = 'Ah-Cyc-Discharge-0'
            else:
                capacity_col = 'Ah-Cyc-Charge-0'
            
            if capacity_col in cycle_data.columns:
                capacity = cycle_data[capacity_col].values
            else:
                # Fallback: integrate current over time
                time_h = cycle_data['Time[h]'].values
                current = np.abs(cycle_data['I[A]'].values)
                capacity = np.cumsum(current * np.gradient(time_h))
            
            # Apply voltage filtering if specified
            if params.get('voltage_range'):
                v_min, v_max = params['voltage_range']
                mask = (voltage >= v_min) & (voltage <= v_max)
                voltage = voltage[mask]
                capacity = capacity[mask]
            
            # Interpolate to uniform grid
            v_interp, q_interp = interpolate_voltage_capacity(
                voltage, capacity, 
                n_points=params.get('n_points', 333)
            )
            
            # Calculate dQ/dU
            smoothing = params.get('smoothing')
            dq_du = calculate_dq_du(v_interp, q_interp, smoothing)
            
            # Detect peaks if enabled
            peaks = None
            if params.get('peak_detection', False):
                prominence = params.get('peak_prominence', 0.1)
                peaks = detect_peaks(dq_du, v_interp, prominence)
            
            results[f"cycle_{cycle_num}_{half_cycle_type}"] = {
                'voltage': v_interp.tolist(),
                'capacity': q_interp.tolist(),
                'dq_du': dq_du.tolist(),
                'peaks': peaks,
                'metadata': {
                    'cycle_number': cycle_num,
                    'half_cycle_type': half_cycle_type,
                    'n_points': len(v_interp),
                    'voltage_range': (v_interp.min(), v_interp.max()),
                    'capacity_range': (q_interp.min(), q_interp.max()),
                    'dq_du_range': (dq_du.min(), dq_du.max())
                }
            }
            
        except Exception as e:
            logging.warning(f"Failed to analyze cycle {cycle_num} ({half_cycle_type}): {str(e)}")
            results[f"cycle_{cycle_num}_{half_cycle_type}"] = {
                'error': str(e),
                'metadata': {
                    'cycle_number': cycle_num,
                    'half_cycle_type': half_cycle_type
                }
            }
    
    return results


def get_available_cycles_for_dqdu(results_df: pd.DataFrame) -> List[Tuple[int, str]]:
    """
    Get list of available cycles from standard analysis results.
    
    Args:
        results_df: DataFrame from standard cycle analysis
        
    Returns:
        List of (cycle_number, half_cycle_type) tuples
    """
    if results_df.empty:
        return []
    
    # Filter to realistic cycles only
    realistic_df = results_df[results_df.get('Is_Realistic', True)]
    
    cycles = []
    for _, row in realistic_df.iterrows():
        cycles.append((int(row['Cycle']), row['HalfCycleType']))
    
    return cycles