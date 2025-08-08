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
    import logging
    logger = logging.getLogger(__name__)
    
    # Log available columns for debugging
    logger.info(f"Available columns in dataframe: {df.columns.tolist()}")
    
    # Filter to charge/discharge commands only
    df_filtered = df[df['Command'].str.lower().isin(['charge', 'discharge'])].copy()
    
    # Detect cycles - use proper pairing of charge/discharge
    command = df_filtered['Command'].str.lower()
    
    # Track command changes
    command_changes = command != command.shift(1)
    
    # Initialize cycle counter
    cycle_num = 0
    cycle_numbers = []
    current_phase = None
    
    for i, (cmd, change) in enumerate(zip(command, command_changes)):
        if change:  # Command changed
            if current_phase == 'discharge' and cmd == 'charge':
                # Discharge -> Charge: same cycle
                pass
            elif current_phase == 'charge' and cmd == 'discharge':
                # Charge -> Discharge: new cycle
                cycle_num += 1
            elif current_phase is None:
                # First command
                cycle_num = 1
            else:
                # Other transitions
                cycle_num += 1
            current_phase = cmd
        cycle_numbers.append(cycle_num)
    
    df_filtered['CycleNumber'] = cycle_numbers
    
    # Log what we found
    logger.info(f"Total cycles found: {df_filtered['CycleNumber'].max()}")
    
    # Filter to the specific cycle and type
    cycle_data = df_filtered[
        (df_filtered['CycleNumber'] == cycle_number) & 
        (df_filtered['Command'].str.lower() == half_cycle_type.lower())
    ].copy()
    
    if cycle_data.empty:
        logger.warning(f"No data found for cycle {cycle_number} ({half_cycle_type})")
        logger.warning(f"Available cycle numbers: {sorted(df_filtered['CycleNumber'].unique())[:20]}")
        logger.warning(f"Commands in filtered data: {df_filtered['Command'].unique()}")
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Ensure arrays are numeric (convert from object dtype if needed)
    try:
        voltage = np.asarray(voltage, dtype=np.float64)
        capacity = np.asarray(capacity, dtype=np.float64)
    except (ValueError, TypeError) as e:
        logger.error(f"Could not convert to numeric - V dtype: {voltage.dtype}, C dtype: {capacity.dtype}")
        logger.error(f"Sample voltage values: {voltage[:5] if len(voltage) > 0 else 'empty'}")
        logger.error(f"Sample capacity values: {capacity[:5] if len(capacity) > 0 else 'empty'}")
        raise ValueError(f"Could not convert data to numeric: {e}")
    
    # Remove any NaN values
    mask = ~(np.isnan(voltage) | np.isnan(capacity))
    voltage = voltage[mask]
    capacity = capacity[mask]
    
    if len(voltage) < 2:
        logger.error(f"Insufficient data points for interpolation: {len(voltage)}")
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
        logger.error(f"Insufficient unique voltage points: {len(voltage_unique)}")
        raise ValueError("Insufficient unique voltage points for interpolation")
    
    # Create uniform voltage grid
    v_min, v_max = voltage_unique.min(), voltage_unique.max()
    v_interp = np.linspace(v_min, v_max, n_points)
    
    logger.info(f"Interpolating: {len(voltage_unique)} unique points to {n_points} points")
    logger.info(f"Voltage range: {v_min:.3f} to {v_max:.3f} V")
    logger.info(f"Capacity range: {capacity_unique.min():.6f} to {capacity_unique.max():.6f} Ah")
    
    # Interpolate capacity - use linear for stability
    interp_func = interpolate.interp1d(voltage_unique, capacity_unique, 
                                       kind='linear', bounds_error=False, 
                                       fill_value='extrapolate')
    q_interp = interp_func(v_interp)
    
    return v_interp, q_interp


def calculate_dq_du(voltage: np.ndarray, capacity: np.ndarray, 
                    smoothing: Optional[Dict] = None) -> np.ndarray:
    """
    Calculate differential capacity dQ/dU.
    
    Args:
        voltage: Voltage data (should be uniformly spaced)
        capacity: Capacity data (in Ah)
        smoothing: Optional smoothing parameters
        
    Returns:
        dQ/dU values array (in mAh/V)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Convert capacity to mAh first for better numerical stability with small batteries
    capacity_mah = capacity * 1000  # Convert Ah to mAh
    
    logger.info(f"Capacity range for dQ/dU: {capacity_mah.min():.3f} to {capacity_mah.max():.3f} mAh")
    
    # Apply smoothing to capacity before differentiation if requested
    if smoothing:
        capacity_mah = apply_smoothing(capacity_mah, smoothing)
    
    # Calculate numerical derivative dQ/dV
    dv = np.gradient(voltage)
    dq = np.gradient(capacity_mah)  # Already in mAh
    
    # Avoid division by zero - use a larger threshold for voltage differences
    dv[np.abs(dv) < 1e-6] = 1e-6
    
    # Calculate dQ/dU (differential capacity) - already in mAh/V
    dq_du = dq / dv
    
    # Check for reasonable values
    if np.all(np.abs(dq_du) < 1e-6):
        logger.warning("All dQ/dU values are near zero - check capacity data")
    
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
    if not params or params.get('method') == 'none':
        return data
        
    method = params.get('method', 'savgol')
    
    if method == 'savgol' or method == 'savitzky_golay':
        window = params.get('window_size', params.get('window', 11))
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
            
            # Try different capacity column names - prioritize absolute capacity
            capacity_cols = {
                'discharge': ['Ah[Ah]', 'Ah-Cyc-Discharge-0', 'Ah-Cyc-Discharge'],
                'charge': ['Ah[Ah]', 'Ah-Cyc-Charge-0', 'Ah-Cyc-Charge']
            }
            
            capacity = None
            for col in capacity_cols[half_cycle_type.lower()]:
                if col in cycle_data.columns:
                    raw_capacity = cycle_data[col].values
                    
                    # For absolute capacity column, calculate relative capacity within cycle
                    if col == 'Ah[Ah]':
                        # Use absolute values and reset to start from 0
                        capacity = np.abs(raw_capacity - raw_capacity[0])
                        logging.info(f"Using absolute capacity column {col}, range: {raw_capacity[0]:.6f} to {raw_capacity[-1]:.6f}")
                    else:
                        # Cycle-specific columns should already be relative
                        capacity = np.abs(raw_capacity)
                        logging.info(f"Using cycle capacity column {col}, max: {capacity.max():.6f}")
                    
                    # Check if we have reasonable capacity values (for small batteries)
                    # For 50 mAh/g with 0.035g = 1.75 mAh = 0.00175 Ah theoretical
                    if capacity.max() < 1e-7:  # Less than 0.0001 mAh - truly too small
                        logging.warning(f"Very small capacity values in {col}: max={capacity.max():.9f} Ah")
                        continue  # Try next column
                    
                    logging.info(f"Selected capacity column: {col}")
                    break
            
            if capacity is None:
                # Fallback: integrate current over time
                logging.info("No capacity column found, integrating current over time")
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
            
            # Log data ranges for debugging
            try:
                v_min = float(voltage.min())
                v_max = float(voltage.max())
                c_min = float(capacity.min())
                c_max = float(capacity.max())
                logging.info(f"Cycle {cycle_num} ({half_cycle_type}): "
                            f"V range: {v_min:.2f}-{v_max:.2f} V, "
                            f"Q range: {c_min:.6f}-{c_max:.6f} Ah, "
                            f"Points: {len(voltage)}")
            except (ValueError, TypeError) as e:
                logging.error(f"Data type issue - V dtype: {voltage.dtype}, C dtype: {capacity.dtype}")
                logging.error(f"Sample values - V: {voltage[:3]}, C: {capacity[:3]}")
            
            # Calculate dQ/dU
            smoothing = params.get('smoothing')
            # Only pass smoothing if it's not None/none
            if smoothing and smoothing.get('method', 'none').lower() != 'none':
                dq_du = calculate_dq_du(v_interp, q_interp, smoothing)
            else:
                dq_du = calculate_dq_du(v_interp, q_interp, None)
            
            # Check if dQ/dU has valid values
            if np.all(np.isnan(dq_du)) or len(dq_du) == 0:
                logging.warning(f"All dQ/dU values are NaN for cycle {cycle_num}")
            else:
                logging.info(f"dQ/dU range: {np.nanmin(dq_du):.4f} to {np.nanmax(dq_du):.4f}")
            
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