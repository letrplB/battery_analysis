"""
Data Cleaner Module

Handles device-specific data cleaning and normalization.
Converts various battery tester formats to a standardized format.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Supported battery tester devices"""
    BASYTEC = "basytec"
    ARBIN = "arbin"
    BIOLOGIC = "biologic"
    NEWARE = "neware"
    MACCOR = "maccor"
    GENERIC = "generic"


class DecimalSeparator(Enum):
    """Decimal separator formats"""
    DOT = "."
    COMMA = ","
    AUTO = "auto"  # Auto-detect


@dataclass
class DeviceProfile:
    """Profile for a specific device type"""
    name: str
    device_type: DeviceType
    decimal_separator: DecimalSeparator = DecimalSeparator.DOT
    delimiter: str = "\t"
    encoding: str = "utf-8"
    header_prefix: str = "~"
    datetime_format: Optional[str] = "%d.%m.%Y %H:%M:%S"
    
    # Column name mappings from device-specific to standard
    column_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Special handling flags
    has_datetime_with_space: bool = True
    has_metadata_header: bool = True
    skip_empty_lines: bool = True
    
    # Data cleaning rules
    remove_columns: List[str] = field(default_factory=list)
    required_columns: List[str] = field(default_factory=list)


class DataCleaner:
    """Cleans and normalizes battery test data from various devices"""
    
    # Standard column names used throughout the application
    STANDARD_COLUMNS = {
        'time': 'Time[h]',
        'voltage': 'U[V]',
        'current': 'I[A]',
        'capacity': 'Ah[Ah]',
        'command': 'Command',
        'state': 'State',
        'cycle': 'Cyc',
        'temperature1': 'T1[°C]',
        'temperature2': 'T2[°C]',
        'datetime': 'DateTime',
        'dataset': 'DataSet'
    }
    
    # Device profiles
    DEVICE_PROFILES = {
        DeviceType.BASYTEC: DeviceProfile(
            name="Basytec Battery Test System",
            device_type=DeviceType.BASYTEC,
            decimal_separator=DecimalSeparator.COMMA,  # European format
            delimiter="\t",
            encoding="utf-8",
            header_prefix="~",
            datetime_format="%d.%m.%Y %H:%M:%S",
            column_mappings={
                'Time[h]': 'Time[h]',
                'U[V]': 'U[V]',
                'I[A]': 'I[A]',
                'Ah[Ah]': 'Ah[Ah]',
                'Command': 'Command',
                'State': 'State',
                'Cyc': 'Cyc',
                'T1[°C]': 'T1[°C]',
                'T2[°C]': 'T2[°C]',
                'DateTime': 'DateTime',
                'DataSet': 'DataSet',
                'Ah-Cyc-Charge-0': 'Ah-Cyc-Charge',
                'Ah-Cyc-Discharge-0': 'Ah-Cyc-Discharge'
            },
            required_columns=['Time[h]', 'U[V]', 'I[A]', 'Command']
        ),
        
        DeviceType.ARBIN: DeviceProfile(
            name="Arbin Battery Tester",
            device_type=DeviceType.ARBIN,
            decimal_separator=DecimalSeparator.DOT,
            delimiter=",",
            encoding="utf-8",
            header_prefix="",
            column_mappings={
                'Test_Time(s)': 'Time[h]',  # Need to convert from seconds
                'Voltage(V)': 'U[V]',
                'Current(A)': 'I[A]',
                'Charge_Capacity(Ah)': 'Ah[Ah]',
                'Cycle_Index': 'Cyc',
                'Step_Index': 'State'
            },
            required_columns=['Test_Time(s)', 'Voltage(V)', 'Current(A)']
        ),
        
        DeviceType.NEWARE: DeviceProfile(
            name="Neware Battery Testing System",
            device_type=DeviceType.NEWARE,
            decimal_separator=DecimalSeparator.DOT,
            delimiter=",",
            encoding="utf-8",
            header_prefix="",
            column_mappings={
                'Time': 'Time[h]',  # May need conversion
                'Voltage': 'U[V]',
                'Current': 'I[A]',
                'Capacity': 'Ah[Ah]',
                'Cycle': 'Cyc',
                'Step': 'State'
            },
            required_columns=['Time', 'Voltage', 'Current']
        ),

        DeviceType.BIOLOGIC: DeviceProfile(
            name="BioLogic BT-Lab",
            device_type=DeviceType.BIOLOGIC,
            decimal_separator=DecimalSeparator.COMMA,  # European format
            delimiter="\t",
            encoding="utf-8",
            header_prefix="",  # BT-Lab uses different header format (not ~)
            datetime_format="%m/%d/%Y %H:%M:%S",
            column_mappings={
                # BT-Lab processed export column names
                'cycle number': 'Cyc',
                'Ecell/V': 'U[V]',
                '<I>/mA': 'I[A]',  # Need mA -> A conversion
                'Capacity/mA.h': 'Ah[Ah]',  # Need mAh -> Ah conversion
                'ox/red': 'ox_red',  # Intermediate, mapped to Command later
                'Q discharge/mA.h': 'Ah-Cyc-Discharge',
                'Q charge/mA.h': 'Ah-Cyc-Charge',
                'Efficiency/%': 'Efficiency',
                'counter inc.': 'counter_inc',
                'control changes': 'control_changes',
                # Alternative column names from different BT-Lab exports (raw data)
                'time/s': 'Time[h]',  # Need s -> h conversion
                'Ewe/V': 'U[V]',
                'I/mA': 'I[A]',
                '(Q-Qo)/mA.h': 'Ah[Ah]',
            },
            has_datetime_with_space=False,
            has_metadata_header=True,
            required_columns=['U[V]', 'I[A]']  # After mapping
        )
    }
    
    def __init__(self, device_type: DeviceType = DeviceType.BASYTEC):
        """
        Initialize data cleaner with device profile
        
        Args:
            device_type: Type of battery tester device
        """
        self.device_type = device_type
        self.profile = self.DEVICE_PROFILES.get(
            device_type,
            self._create_generic_profile()
        )
        logger.info(f"Initialized DataCleaner for {self.profile.name}")
    
    def clean_data(
        self,
        df: pd.DataFrame,
        decimal_separator: Optional[DecimalSeparator] = None
    ) -> pd.DataFrame:
        """
        Clean and normalize data based on device profile
        
        Args:
            df: Raw dataframe to clean
            decimal_separator: Override decimal separator detection
            
        Returns:
            Cleaned and normalized dataframe
        """
        logger.info(f"Cleaning data with {len(df)} rows")
        
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Step 1: Standardize column names
        # (Decimal separators are already handled in raw_data_parser)
        df_clean = self._standardize_columns(df_clean)
        
        # Step 2: Convert data types
        df_clean = self._convert_data_types(df_clean)
        
        # Step 3: Device-specific cleaning
        df_clean = self._apply_device_specific_cleaning(df_clean)
        
        # Step 4: Validate required columns
        self._validate_required_columns(df_clean)
        
        # Step 5: Remove invalid rows
        df_clean = self._remove_invalid_rows(df_clean)
        
        logger.info(f"Cleaned data has {len(df_clean)} valid rows")
        
        return df_clean
    
    def clean_raw_text(
        self,
        text: str,
        decimal_separator: Optional[DecimalSeparator] = None
    ) -> str:
        """
        Clean raw text data before parsing

        Args:
            text: Raw text content
            decimal_separator: Decimal separator to use

        Returns:
            Cleaned text ready for parsing
        """
        # For Basytec, we know it uses comma decimals and tab delimiters
        if self.device_type == DeviceType.BASYTEC:
            lines = text.split('\n')
            cleaned_lines = []

            for line in lines:
                if line.startswith('~'):
                    # Don't modify header/metadata lines
                    cleaned_lines.append(line)
                else:
                    # For data lines: replace comma decimals with dots
                    # Basytec uses tabs as delimiters, so commas are ONLY decimals
                    cleaned_line = line.replace(',', '.')
                    cleaned_lines.append(cleaned_line)

            text = '\n'.join(cleaned_lines)

        # For BioLogic BT-Lab, also uses comma decimals with tab delimiters
        elif self.device_type == DeviceType.BIOLOGIC:
            lines = text.split('\n')
            cleaned_lines = []

            # Find where data starts (after "Nb header lines : XX")
            header_lines = self._get_biologic_header_lines(text)

            for i, line in enumerate(lines):
                if i < header_lines:
                    # Keep header lines as-is
                    cleaned_lines.append(line)
                else:
                    # For data lines: replace comma decimals with dots
                    # BT-Lab uses tabs as delimiters, so commas are ONLY decimals
                    cleaned_line = line.replace(',', '.')
                    cleaned_lines.append(cleaned_line)

            text = '\n'.join(cleaned_lines)

        # Fix encoding issues (temperature symbols, etc.)
        text = self._fix_encoding_issues(text)

        return text

    def _get_biologic_header_lines(self, text: str) -> int:
        """
        Get the number of header lines from BioLogic BT-Lab file

        BT-Lab files have 'Nb header lines : XX' on line 2

        Args:
            text: Raw file text

        Returns:
            Number of header lines (default 0 if not found)
        """
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if 'Nb header lines' in line:
                try:
                    # Extract number after colon
                    parts = line.split(':')
                    if len(parts) >= 2:
                        return int(parts[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0
    
    def _fix_decimal_separators(
        self,
        df: pd.DataFrame,
        separator: DecimalSeparator
    ) -> pd.DataFrame:
        """Fix decimal separators in numeric columns"""
        
        if separator == DecimalSeparator.AUTO:
            separator = self._detect_decimal_separator_df(df)
        
        if separator == DecimalSeparator.COMMA:
            # Convert comma decimals to dots
            for col in df.columns:
                if df[col].dtype == object:
                    # Try to convert string columns with comma decimals
                    try:
                        df[col] = df[col].str.replace(',', '.').astype(float)
                    except (ValueError, AttributeError):
                        pass  # Not a numeric column
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names based on device profile"""
        
        # Apply column mappings
        rename_dict = {}
        for old_name, new_name in self.profile.column_mappings.items():
            if old_name in df.columns:
                rename_dict[old_name] = new_name
        
        if rename_dict:
            df = df.rename(columns=rename_dict)
            logger.debug(f"Renamed columns: {rename_dict}")
        
        # Remove unwanted columns
        if self.profile.remove_columns:
            cols_to_remove = [col for col in self.profile.remove_columns if col in df.columns]
            if cols_to_remove:
                df = df.drop(columns=cols_to_remove)
                logger.debug(f"Removed columns: {cols_to_remove}")
        
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types"""
        
        # Numeric columns - most should already be numeric from parser
        numeric_cols = ['Time[h]', 'U[V]', 'I[A]', 'Ah[Ah]', 
                       'T1[°C]', 'T2[°C]', 'State', 'Cyc', 'DataSet']
        
        for col in numeric_cols:
            if col in df.columns and df[col].dtype == object:
                # Only convert if still string type
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Special handling for time conversion (e.g., seconds to hours)
        if self.device_type == DeviceType.ARBIN and 'Time[h]' in df.columns:
            # Arbin uses seconds, convert to hours
            df['Time[h]'] = df['Time[h]'] / 3600
        
        return df
    
    def _apply_device_specific_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply device-specific cleaning rules"""

        if self.device_type == DeviceType.BASYTEC:
            # Fix temperature column headers
            df = self._fix_temperature_columns(df)

            # Ensure Command column is string and lowercase for consistency
            if 'Command' in df.columns:
                # Convert to string first (in case it's object or mixed type)
                df['Command'] = df['Command'].astype(str)
                # Then convert to lowercase
                df['Command'] = df['Command'].str.lower()

        elif self.device_type == DeviceType.ARBIN:
            # Create Command column from step types if needed
            if 'Command' not in df.columns and 'Step_Type' in df.columns:
                df['Command'] = df['Step_Type'].map({
                    'CC_Chg': 'Charge',
                    'CC_DChg': 'Discharge',
                    'Rest': 'Pause'
                }).fillna('Unknown')

        elif self.device_type == DeviceType.BIOLOGIC:
            df = self._apply_biologic_cleaning(df)

        return df

    def _apply_biologic_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply BioLogic BT-Lab specific cleaning and unit conversions"""

        # First, ensure numeric columns are actually numeric
        # (they may still be strings after initial parsing)
        numeric_cols_biologic = ['I[A]', 'U[V]', 'Ah[Ah]', 'Ah-Cyc-Discharge',
                                  'Ah-Cyc-Charge', 'Cyc', 'ox_red', 'Efficiency']
        for col in numeric_cols_biologic:
            if col in df.columns and df[col].dtype == object:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Unit conversion: mA -> A for current
        if 'I[A]' in df.columns:
            df['I[A]'] = df['I[A]'] / 1000.0
            logger.debug("Converted current from mA to A")

        # Unit conversion: mAh -> Ah for capacity columns
        capacity_cols = ['Ah[Ah]', 'Ah-Cyc-Discharge', 'Ah-Cyc-Charge']
        for col in capacity_cols:
            if col in df.columns:
                df[col] = df[col] / 1000.0
                logger.debug(f"Converted {col} from mAh to Ah")

        # Map ox/red to Command column based on current sign
        # ox/red: 1 = oxidation (charge), 0 = reduction (discharge) or rest
        if 'ox_red' in df.columns:
            # Determine command based on ox/red flag and current
            def map_command(row):
                ox_red = row.get('ox_red', 0)
                current = row.get('I[A]', 0)

                if ox_red == 1:
                    return 'charge'
                elif current < -1e-9:  # Small threshold for numerical noise
                    return 'discharge'
                elif abs(current) < 1e-9:
                    return 'pause'
                else:
                    return 'charge'  # Positive current with ox_red=0

            df['Command'] = df.apply(map_command, axis=1)
            logger.debug("Created Command column from ox/red indicator")

        # Generate synthetic time if not present (for processed exports)
        # This uses row index as proxy - data points are typically at regular intervals
        if 'Time[h]' not in df.columns:
            # Check metadata for sampling interval, default to ~20s based on typical BT-Lab settings
            # For processed exports, we use row index as a monotonic "time" proxy
            df['Time[h]'] = df.index * (20.0 / 3600.0)  # 20 seconds per point -> hours
            logger.warning("No time column found in BioLogic data. Generated synthetic time "
                          "from row index (assuming ~20s intervals). This is approximate.")

        # Convert time from seconds to hours if we have time/s column
        # (This would be from raw BT-Lab exports)
        if 'time/s' in df.columns and 'Time[h]' not in df.columns:
            df['Time[h]'] = df['time/s'] / 3600.0
            logger.debug("Converted time from seconds to hours")

        # Ensure Cyc column is integer (it comes as scientific notation float)
        if 'Cyc' in df.columns:
            df['Cyc'] = df['Cyc'].round().astype(int)
            logger.debug("Converted Cyc to integer")

        return df
    
    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns are present"""
        
        missing = []
        for col in self.profile.required_columns:
            if col not in df.columns:
                missing.append(col)
        
        if missing:
            raise ValueError(f"Required columns missing after cleaning: {missing}")
    
    def _remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows with invalid data"""
        
        # Remove rows where all numeric columns are NaN
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df = df.dropna(subset=numeric_cols, how='all')
        
        # Remove rows with negative time
        if 'Time[h]' in df.columns:
            df = df[df['Time[h]'] >= 0]
        
        return df
    
    def _clean_line_decimals(self, line: str) -> str:
        """Clean decimal separators in a single line"""
        
        # Split by tabs or spaces
        parts = line.split('\t') if '\t' in line else line.split()
        
        cleaned_parts = []
        for part in parts:
            # Check if this looks like a number with comma decimal
            if re.match(r'^-?\d+,\d+$', part):
                # Replace comma with dot
                cleaned_parts.append(part.replace(',', '.'))
            else:
                cleaned_parts.append(part)
        
        # Rejoin with original delimiter
        delimiter = '\t' if '\t' in line else ' '
        return delimiter.join(cleaned_parts)
    
    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding issues"""
        
        # Fix temperature symbols
        text = text.replace('[�C]', '[°C]')
        text = text.replace('[ºC]', '[°C]')
        
        return text
    
    def _fix_temperature_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix temperature column names with special characters"""
        
        rename_dict = {}
        for col in df.columns:
            if 'T1[' in col and 'C]' in col:
                rename_dict[col] = 'T1[°C]'
            elif 'T2[' in col and 'C]' in col:
                rename_dict[col] = 'T2[°C]'
        
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        return df
    
    def _detect_decimal_separator(self, text: str) -> DecimalSeparator:
        """Auto-detect decimal separator from text"""
        
        # Count occurrences of patterns
        comma_decimal_count = len(re.findall(r'\d+,\d+', text))
        dot_decimal_count = len(re.findall(r'\d+\.\d+', text))
        
        if comma_decimal_count > dot_decimal_count:
            return DecimalSeparator.COMMA
        else:
            return DecimalSeparator.DOT
    
    def _detect_decimal_separator_df(self, df: pd.DataFrame) -> DecimalSeparator:
        """Auto-detect decimal separator from dataframe"""
        
        # Check first few string columns for patterns
        for col in df.columns:
            if df[col].dtype == object:
                sample = df[col].head(100).astype(str).str.cat()
                separator = self._detect_decimal_separator(sample)
                if separator != DecimalSeparator.DOT:
                    return separator
        
        return DecimalSeparator.DOT
    
    def _create_generic_profile(self) -> DeviceProfile:
        """Create a generic device profile for unknown devices"""
        
        return DeviceProfile(
            name="Generic Battery Tester",
            device_type=DeviceType.GENERIC,
            decimal_separator=DecimalSeparator.AUTO,
            delimiter="\t",
            encoding="utf-8",
            header_prefix="",
            column_mappings={},
            required_columns=['Time[h]', 'U[V]', 'I[A]']
        )