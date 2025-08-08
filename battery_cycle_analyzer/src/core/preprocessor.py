import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from scipy import integrate
import logging

from .data_models import (
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
            parameters.boundary_method
        )
        
        if not cycle_boundaries:
            validation_warnings.append("No cycles detected in data")
        
        # Calculate basic cycle metadata
        cycle_metadata = self._calculate_cycle_metadata(
            raw_data.data,
            cycle_boundaries,
            parameters
        )
        
        # Validate data quality
        warnings = self._validate_data_quality(raw_data.data, cycle_metadata)
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
        method: str
    ) -> List[Tuple[int, int]]:
        """Detect cycle boundaries in the data"""
        
        if method == "State-based" and has_state:
            return self._detect_boundaries_by_state(df)
        else:
            return self._detect_boundaries_by_current(df)
    
    def _detect_boundaries_by_state(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        """Detect cycle boundaries using State column"""
        boundaries = []
        
        # Find state transitions
        state_changes = df['State'].diff() != 0
        change_indices = df.index[state_changes].tolist()
        
        if not change_indices:
            return boundaries
        
        # Add start if not present
        if change_indices[0] != 0:
            change_indices.insert(0, 0)
        
        # Add end if not present
        if change_indices[-1] != len(df) - 1:
            change_indices.append(len(df) - 1)
        
        # Group into cycles (assuming state cycles through values)
        current_cycle_start = None
        for i in range(len(change_indices) - 1):
            start_idx = change_indices[i]
            end_idx = change_indices[i + 1]
            
            # Check if this segment contains discharge
            segment = df.iloc[start_idx:end_idx]
            if 'Discharge' in segment['Command'].values:
                if current_cycle_start is None:
                    current_cycle_start = start_idx
                
                # Check if next segment is charge (end of cycle)
                if i < len(change_indices) - 2:
                    next_segment = df.iloc[change_indices[i+1]:change_indices[i+2]]
                    if 'Charge' in next_segment['Command'].values:
                        boundaries.append((current_cycle_start, change_indices[i+2]))
                        current_cycle_start = None
        
        return boundaries
    
    def _detect_boundaries_by_current(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        """Detect cycle boundaries using current zero-crossings"""
        boundaries = []
        
        # Identify discharge and charge segments
        current = df['I[A]'].values
        
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
        parameters: ProcessingParameters
    ) -> pd.DataFrame:
        """Calculate basic metadata for each cycle"""
        
        if not boundaries:
            return pd.DataFrame()
        
        cycle_data = []
        
        for cycle_num, (start_idx, end_idx) in enumerate(boundaries, 1):
            cycle_df = df.iloc[start_idx:end_idx]
            
            # Get charge and discharge segments
            discharge_mask = cycle_df['I[A]'] < 0
            charge_mask = cycle_df['I[A]'] > 0
            
            discharge_df = cycle_df[discharge_mask]
            charge_df = cycle_df[charge_mask]
            
            # Calculate capacities
            discharge_capacity = 0
            charge_capacity = 0
            
            if len(discharge_df) > 1:
                time_h = discharge_df['Time[h]'].values
                current_a = np.abs(discharge_df['I[A]'].values)
                discharge_capacity = integrate.trapz(current_a, time_h)
            
            if len(charge_df) > 1:
                time_h = charge_df['Time[h]'].values
                current_a = charge_df['I[A]'].values
                charge_capacity = integrate.trapz(current_a, time_h)
            
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
                'Voltage_Min': cycle_df['U[V]'].min() if len(cycle_df) > 0 else 0,
                'Voltage_Max': cycle_df['U[V]'].max() if len(cycle_df) > 0 else 0,
                'Duration_h': cycle_df['Time[h]'].max() - cycle_df['Time[h]'].min() if len(cycle_df) > 0 else 0
            })
        
        return pd.DataFrame(cycle_data)
    
    def _validate_data_quality(
        self,
        df: pd.DataFrame,
        cycle_metadata: pd.DataFrame
    ) -> List[str]:
        """Validate data quality and return warnings"""
        warnings = []
        
        # Check for missing values
        missing_counts = df[['Time[h]', 'U[V]', 'I[A]']].isnull().sum()
        if missing_counts.any():
            warnings.append(f"Missing values detected: {missing_counts.to_dict()}")
        
        # Check for unrealistic values
        if (df['U[V]'] < 0).any():
            warnings.append("Negative voltage values detected")
        
        if (df['U[V]'] > 10).any():
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