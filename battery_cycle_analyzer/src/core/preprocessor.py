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

        # Check for pre-defined cycle numbers (e.g., from BioLogic)
        # If we have a Cyc column with actual cycle numbers, use that directly
        if 'Cyc' in df.columns and df['Cyc'].nunique() > 1:
            # Check if this looks like BioLogic data with pre-calculated capacities
            has_precalc = 'Ah-Cyc-Discharge' in df.columns and 'Ah-Cyc-Charge' in df.columns
            if has_precalc:
                self.logger.info("Using cycle numbers from Cyc column (BioLogic data)")
                return self._detect_boundaries_by_cycle_column(df)

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

    def _detect_boundaries_by_cycle_column(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        """Detect cycle boundaries using the Cyc column directly

        Used for data sources like BioLogic that have pre-defined cycle numbers.
        """
        boundaries = []

        # Get unique cycle numbers (excluding 0 which is often initialization)
        cycle_numbers = sorted(df['Cyc'].unique())
        cycle_numbers = [c for c in cycle_numbers if c > 0]

        for cycle_num in cycle_numbers:
            cycle_mask = df['Cyc'] == cycle_num
            cycle_indices = df.index[cycle_mask]

            if len(cycle_indices) > 0:
                start_idx = cycle_indices[0]
                end_idx = cycle_indices[-1]
                boundaries.append((start_idx, end_idx))

        self.logger.info(f"Detected {len(boundaries)} cycles from Cyc column")
        return boundaries
    
    def _detect_boundaries_by_state(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        """Detect cycle boundaries using command transitions
        
        A cycle can be either:
        - Discharge followed by Charge (standard)
        - Charge followed by Discharge (formation cycles)
        
        Each cycle boundary includes both phases
        """
        boundaries = []
        
        # Ensure we have Command column
        if 'Command' not in df.columns:
            self.logger.error("Command column not found for cycle detection")
            return boundaries
        
        # Get command sequence
        commands = df['Command'].str.lower().values
        indices = df.index.values
        
        if len(commands) == 0:
            return boundaries
        
        # Determine cycle pattern from first commands
        first_cmd = commands[0]
        
        # Track command changes
        i = 0
        while i < len(commands):
            current_cmd = commands[i]
            
            # Start of a potential cycle
            if current_cmd in ['discharge', 'charge']:
                cycle_start = indices[i]
                first_phase = current_cmd
                
                # Find where first phase ends
                while i < len(commands) and commands[i] == first_phase:
                    i += 1
                
                # Check if followed by opposite phase
                if i < len(commands):
                    second_phase = commands[i]
                    expected_second = 'charge' if first_phase == 'discharge' else 'discharge'
                    
                    if second_phase == expected_second:
                        # Find where second phase ends
                        while i < len(commands) and commands[i] == second_phase:
                            i += 1
                        
                        # Complete cycle found
                        cycle_end = indices[i - 1] if i > 0 else indices[-1]
                        boundaries.append((cycle_start, cycle_end))
                    # else: same phase repeated or pause, not a complete cycle
            else:
                i += 1
        
        self.logger.info(f"Detected {len(boundaries)} complete cycles")
        
        # Debug: Log first and last few cycles
        if boundaries:
            self.logger.debug(f"First cycle indices: {boundaries[0]}")
            self.logger.debug(f"Last cycle indices: {boundaries[-1]}")
            if len(boundaries) > 1:
                self.logger.debug(f"Second cycle indices: {boundaries[1]}")
        
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

        # Check for pre-calculated capacity columns (e.g., from BioLogic processed exports)
        has_precalc_capacity = (
            'Ah-Cyc-Discharge' in df.columns and
            'Ah-Cyc-Charge' in df.columns
        )

        if has_precalc_capacity:
            self.logger.info("Using pre-calculated capacity columns (Ah-Cyc-Discharge, Ah-Cyc-Charge)")

        cycle_data = []

        for cycle_num, (start_idx, end_idx) in enumerate(boundaries, 1):
            cycle_df = df.iloc[start_idx:end_idx]

            # Calculate capacities - use pre-calculated if available, otherwise integrate
            if has_precalc_capacity:
                # Use max value of pre-calculated capacity columns within this cycle
                discharge_capacity = cycle_df['Ah-Cyc-Discharge'].max()
                charge_capacity = cycle_df['Ah-Cyc-Charge'].max()

                # Handle NaN values
                if pd.isna(discharge_capacity):
                    discharge_capacity = 0
                if pd.isna(charge_capacity):
                    charge_capacity = 0
            else:
                # Integrate current over time (original method)
                discharge_mask = cycle_df[current_col] < 0
                charge_mask = cycle_df[current_col] > 0

                discharge_df = cycle_df[discharge_mask]
                charge_df = cycle_df[charge_mask]

                discharge_capacity = 0
                charge_capacity = 0

                if len(discharge_df) > 1:
                    time_h = discharge_df[time_col].values
                    current_a = np.abs(discharge_df[current_col].values)
                    discharge_capacity = np.trapezoid(current_a, time_h)

                if len(charge_df) > 1:
                    time_h = charge_df[time_col].values
                    current_a = np.abs(charge_df[current_col].values)
                    charge_capacity = np.trapezoid(current_a, time_h)

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