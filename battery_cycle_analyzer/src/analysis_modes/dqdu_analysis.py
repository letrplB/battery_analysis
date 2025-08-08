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


def extract_cycle_data(df: pd.DataFrame, cycle_number: int, half_cycle_type: str, 
                      cycle_boundaries: List[Tuple[int, int]]) -> pd.DataFrame:
    """
    Extract specific half-cycle data for dQ/dU analysis using preprocessed boundaries.
    
    Args:
        df: Main dataframe with battery data
        cycle_number: Cycle number to extract (1-indexed)
        half_cycle_type: 'charge' or 'discharge'
        cycle_boundaries: Pre-computed cycle boundaries from preprocessing
        
    Returns:
        DataFrame with the extracted cycle data
        
    Raises:
        ValueError: If cycle number is invalid or no data found for the specified phase
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate cycle number
    if not (0 < cycle_number <= len(cycle_boundaries)):
        raise ValueError(f"Invalid cycle number {cycle_number}. Available: 1-{len(cycle_boundaries)}")
    
    # Get cycle boundaries
    start_idx, end_idx = cycle_boundaries[cycle_number - 1]  # Convert to 0-indexed
    cycle_data = df.iloc[start_idx:end_idx + 1].copy()
    
    # Check for adjacent pause/rest periods to capture full voltage range
    if start_idx > 0 and df.iloc[start_idx - 1]['Command'].lower() in ['pause', 'rest']:
        pause_start = start_idx - 1
        while pause_start > 0 and df.iloc[pause_start - 1]['Command'].lower() in ['pause', 'rest']:
            pause_start -= 1
        start_idx = pause_start
        cycle_data = df.iloc[start_idx:end_idx + 1].copy()
    
    if end_idx < len(df) - 1 and df.iloc[end_idx + 1]['Command'].lower() in ['pause', 'rest']:
        pause_end = end_idx + 1
        while pause_end < len(df) - 1 and df.iloc[pause_end + 1]['Command'].lower() in ['pause', 'rest']:
            pause_end += 1
        end_idx = pause_end
        cycle_data = df.iloc[start_idx:end_idx + 1].copy()
    
    # Filter to the specific half-cycle type
    filtered_data = cycle_data[cycle_data['Command'].str.lower() == half_cycle_type.lower()].copy()
    
    if filtered_data.empty:
        raise ValueError(f"No {half_cycle_type} data found in cycle {cycle_number}")
    
    logger.info(f"Cycle {cycle_number} ({half_cycle_type}): {len(filtered_data)} points from index {start_idx} to {end_idx}")
    
    return filtered_data


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
                    smoothing: Optional[Dict] = None, 
                    phase_type: str = 'discharge') -> np.ndarray:
    """
    Calculate differential capacity dQ/dU.
    
    Args:
        voltage: Voltage data (should be uniformly spaced)
        capacity: Capacity data (in Ah)
        smoothing: Optional smoothing parameters
        phase_type: 'charge' or 'discharge' for sign convention
        
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
    
    # Apply sign convention: discharge should be negative
    # This is the standard convention in battery analysis
    if phase_type.lower() == 'discharge':
        dq_du = -np.abs(dq_du)  # Ensure discharge is negative
    else:
        dq_du = np.abs(dq_du)  # Ensure charge is positive
    
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
                         params: Dict[str, Any], 
                         cycle_boundaries: List[Tuple[int, int]]) -> Dict:
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
            - use_common_voltage_range: Use common voltage range for all cycles (better for comparison)
        cycle_boundaries: Pre-computed cycle boundaries from preprocessing
    
    Returns:
        Dictionary with dQ/dU results for each selected cycle
    """
    results = {}
    
    # First pass: collect voltage ranges if we need a common range
    voltage_ranges = []
    if params.get('use_common_voltage_range', True):  # Default to True for better comparison
        for cycle_num, half_cycle_type in cycle_selections:
            try:
                cycle_data = extract_cycle_data(df, cycle_num, half_cycle_type, cycle_boundaries)
                voltage = cycle_data['U[V]'].values
                voltage_ranges.append((voltage.min(), voltage.max()))
            except Exception:
                pass
        
        if voltage_ranges:
            # Find the common voltage range (intersection of all ranges)
            common_v_min = max(v_min for v_min, _ in voltage_ranges)
            common_v_max = min(v_max for _, v_max in voltage_ranges)
            logging.info(f"Using common voltage range: {common_v_min:.3f} to {common_v_max:.3f} V")
            # Override the voltage_range parameter
            params = params.copy()
            params['voltage_range'] = (common_v_min, common_v_max)
    
    for cycle_num, half_cycle_type in cycle_selections:
        try:
            # Extract cycle data
            cycle_data = extract_cycle_data(df, cycle_num, half_cycle_type, cycle_boundaries)
            
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
                        # Calculate relative capacity from start of cycle
                        capacity = np.abs(raw_capacity - raw_capacity[0])
                        logging.info(f"Using absolute capacity column {col}, range: {raw_capacity[0]:.6f} to {raw_capacity[-1]:.6f}")
                        logging.info(f"Capacity range for {half_cycle_type}: {capacity.min():.6f} to {capacity.max():.6f} Ah")
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
                dq_du = calculate_dq_du(v_interp, q_interp, smoothing, phase_type=half_cycle_type)
            else:
                dq_du = calculate_dq_du(v_interp, q_interp, None, phase_type=half_cycle_type)
            
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

