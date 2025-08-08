import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from scipy import integrate
import logging

from core.data_models import (
    RawBatteryData, 
    ProcessingParameters, 
    PreprocessedData
)


class DataPreprocessor:
    """Handles data preprocessing and cycle detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def preprocess(
        self,
        raw_data: RawBatteryData,
        parameters: ProcessingParameters
    ) -> PreprocessedData:
        """Preprocess raw data for analysis"""
        
        validation_warnings = []
        
        # Detect cycle boundaries
        cycle_boundaries = self._detect_cycle_boundaries(
            raw_data.data,
            raw_data.has_state_column,
            parameters.boundary_method,
            raw_data.column_mapping
        )
        
        if not cycle_boundaries:
            validation_warnings.append("No cycles detected in data")
        
        # Calculate basic cycle metadata
        cycle_metadata = self._calculate_cycle_metadata(
            raw_data.data,
            cycle_boundaries,
            parameters,
            raw_data.column_mapping
        )
        
        # Validate data quality
        warnings = self._validate_data_quality(raw_data.data, cycle_metadata, raw_data.column_mapping)
        validation_warnings.extend(warnings)
        
        return PreprocessedData(
            raw_data=raw_data,
            parameters=parameters,
            cycle_boundaries=cycle_boundaries,
            cycle_metadata=cycle_metadata,
            validation_warnings=validation_warnings
        )
    
    def _detect_cycle_boundaries(
        self,
        df: pd.DataFrame,
        has_state: bool,
        method: str,
        column_mapping: Dict[str, str] = None
    ) -> List[Tuple[int, int]]:
        """Detect cycle boundaries in the data"""
        
        # Get actual column names from mapping
        if column_mapping is None:
            column_mapping = {}
        
        command_col = column_mapping.get('Command', 'Command')
        
        # Filter to only charge and discharge commands (remove pause, etc.)
        if command_col in df.columns:
            # Debug: Check what values are in the Command column
            unique_commands = df[command_col].unique()
            self.logger.info(f"Unique commands in data: {unique_commands[:10]}")
            
            df_filtered = df[df[command_col].str.lower().isin(['charge', 'discharge'])].copy()
            if len(df_filtered) == 0:
                self.logger.warning(f"No charge/discharge data found after filtering. Command column '{command_col}' has values: {unique_commands[:10]}")
                return []
        else:
            self.logger.warning(f"Command column '{command_col}' not found in data columns: {df.columns.tolist()}")
            df_filtered = df
        
        if method == "State-based" and has_state:
            return self._detect_boundaries_by_state(df_filtered)
        else:
            return self._detect_boundaries_by_current(df_filtered, column_mapping)
    
    def _detect_boundaries_by_state(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        """Detect cycle boundaries using State column"""
        boundaries = []
        
        # The legacy code approach: detect charge/discharge transitions
        # regardless of State, which is used differently
        
        # Ensure we have Command column
        if 'Command' not in df.columns:
            self.logger.error("Command column not found for cycle detection")
            return boundaries
        
        # Get indices
        indices = df.index.tolist()
        
        # Track current cycle
        cycle_start = None
        in_discharge = False
        in_charge = False
        
        for i, idx in enumerate(indices):
            command = df.loc[idx, 'Command'].lower()
            
            if command == 'discharge':
                if not in_discharge:
                    # Start of discharge
                    if cycle_start is None:
                        cycle_start = idx
                    in_discharge = True
                    in_charge = False
            
            elif command == 'charge':
                if not in_charge:
                    # Start of charge
                    if cycle_start is None:
                        cycle_start = idx
                    in_charge = True
                    in_discharge = False
            
            # Check for cycle completion (next discharge after charge)
            if i < len(indices) - 1:
                next_command = df.loc[indices[i + 1], 'Command'].lower()
                if command == 'charge' and next_command == 'discharge':
                    # End of cycle
                    if cycle_start is not None:
                        boundaries.append((cycle_start, idx))
                        cycle_start = indices[i + 1]  # Start next cycle
        
        # Add last cycle if exists
        if cycle_start is not None and cycle_start < indices[-1]:
            boundaries.append((cycle_start, indices[-1]))
        
        return boundaries
    
    def _detect_boundaries_by_current(self, df: pd.DataFrame, column_mapping: Dict[str, str] = None) -> List[Tuple[int, int]]:
        """Detect cycle boundaries using current zero-crossings"""
        boundaries = []
        
        # Get actual column name for current
        if column_mapping is None:
            column_mapping = {}
        current_col = column_mapping.get('I[A]', 'I[A]')
        
        if current_col not in df.columns:
            self.logger.error(f"Current column '{current_col}' not found in data")
            return boundaries
        
        # Identify discharge and charge segments
        current = df[current_col].values
        
        # Find zero crossings
        sign_changes = np.diff(np.sign(current[current != 0]))
        change_indices = np.where(sign_changes != 0)[0]
        
        if len(change_indices) < 2:
            return boundaries
        
        # Group into cycles
        for i in range(0, len(change_indices) - 1, 2):
            if i + 1 < len(change_indices):
                start = change_indices[i]
                end = change_indices[i + 1]
                
                # Validate this is a discharge-charge cycle
                if np.mean(current[start:end]) < 0:  # Discharge first
                    boundaries.append((start, end))
        
        return boundaries
    
    def _calculate_cycle_metadata(
        self,
        df: pd.DataFrame,
        boundaries: List[Tuple[int, int]],
        parameters: ProcessingParameters,
        column_mapping: Dict[str, str] = None
    ) -> pd.DataFrame:
        """Calculate basic metadata for each cycle"""
        
        if not boundaries:
            return pd.DataFrame()
        
        # Get actual column names from mapping
        if column_mapping is None:
            column_mapping = {}
        
        current_col = column_mapping.get('I[A]', 'I[A]')
        time_col = column_mapping.get('Time[h]', 'Time[h]')
        voltage_col = column_mapping.get('U[V]', 'U[V]')
        
        # Check if required columns exist
        if current_col not in df.columns:
            self.logger.error(f"Current column '{current_col}' not found in data columns: {df.columns.tolist()}")
            return pd.DataFrame()
        if time_col not in df.columns:
            self.logger.error(f"Time column '{time_col}' not found in data columns: {df.columns.tolist()}")
            return pd.DataFrame()
        if voltage_col not in df.columns:
            self.logger.error(f"Voltage column '{voltage_col}' not found in data columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        cycle_data = []
        
        for cycle_num, (start_idx, end_idx) in enumerate(boundaries, 1):
            cycle_df = df.iloc[start_idx:end_idx]
            
            # Get charge and discharge segments
            discharge_mask = cycle_df[current_col] < 0
            charge_mask = cycle_df[current_col] > 0
            
            discharge_df = cycle_df[discharge_mask]
            charge_df = cycle_df[charge_mask]
            
            # Calculate capacities
            discharge_capacity = 0
            charge_capacity = 0
            
            if len(discharge_df) > 1:
                time_h = discharge_df[time_col].values
                current_a = np.abs(discharge_df[current_col].values)
                discharge_capacity = np.trapz(current_a, time_h)
            
            if len(charge_df) > 1:
                time_h = charge_df[time_col].values
                current_a = np.abs(charge_df[current_col].values)  # Use absolute value for charge too
                charge_capacity = np.trapz(current_a, time_h)
            
            # Calculate specific capacity
            specific_discharge = (discharge_capacity * 1000) / parameters.active_material_weight
            specific_charge = (charge_capacity * 1000) / parameters.active_material_weight
            
            # Get C-rates for this cycle
            c_rate_charge = 0.333  # Default
            c_rate_discharge = 0.333  # Default
            
            for start_c, end_c, charge_rate, discharge_rate in parameters.c_rates:
                if start_c <= cycle_num <= end_c:
                    c_rate_charge = charge_rate
                    c_rate_discharge = discharge_rate
                    break
            
            cycle_data.append({
                'Cycle': cycle_num,
                'Start_Index': start_idx,
                'End_Index': end_idx,
                'Discharge_Capacity_Ah': discharge_capacity,
                'Charge_Capacity_Ah': charge_capacity,
                'Specific_Discharge_mAhg': specific_discharge,
                'Specific_Charge_mAhg': specific_charge,
                'Efficiency_%': (discharge_capacity / charge_capacity * 100) if charge_capacity > 0 else 0,
                'C_Rate_Charge': c_rate_charge,
                'C_Rate_Discharge': c_rate_discharge,
                'Voltage_Min': cycle_df[voltage_col].min() if len(cycle_df) > 0 else 0,
                'Voltage_Max': cycle_df[voltage_col].max() if len(cycle_df) > 0 else 0,
                'Duration_h': cycle_df[time_col].max() - cycle_df[time_col].min() if len(cycle_df) > 0 else 0
            })
        
        return pd.DataFrame(cycle_data)
    
    def _validate_data_quality(
        self,
        df: pd.DataFrame,
        cycle_metadata: pd.DataFrame,
        column_mapping: Dict[str, str] = None
    ) -> List[str]:
        """Validate data quality and return warnings"""
        warnings = []
        
        # Get actual column names from mapping
        if column_mapping is None:
            column_mapping = {}
        
        time_col = column_mapping.get('Time[h]', 'Time[h]')
        voltage_col = column_mapping.get('U[V]', 'U[V]')
        current_col = column_mapping.get('I[A]', 'I[A]')
        
        # Check for missing values
        check_cols = []
        for col in [time_col, voltage_col, current_col]:
            if col in df.columns:
                check_cols.append(col)
        
        if check_cols:
            missing_counts = df[check_cols].isnull().sum()
            if missing_counts.any():
                warnings.append(f"Missing values detected: {missing_counts.to_dict()}")
        
        # Check for unrealistic values
        if voltage_col in df.columns:
            if (df[voltage_col] < 0).any():
                warnings.append("Negative voltage values detected")
            
            if (df[voltage_col] > 10).any():
                warnings.append("Voltage values above 10V detected")
        
        # Check cycle consistency
        if len(cycle_metadata) > 0:
            # Check for very low capacities
            low_capacity_cycles = cycle_metadata[
                cycle_metadata['Specific_Discharge_mAhg'] < 10
            ]['Cycle'].tolist()
            
            if low_capacity_cycles:
                warnings.append(f"Very low capacity in cycles: {low_capacity_cycles[:5]}")
            
            # Check for very high capacities
            high_capacity_cycles = cycle_metadata[
                cycle_metadata['Specific_Discharge_mAhg'] > 1000
            ]['Cycle'].tolist()
            
            if high_capacity_cycles:
                warnings.append(f"Unusually high capacity in cycles: {high_capacity_cycles[:5]}")
        
        return warnings