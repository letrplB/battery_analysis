"""
Raw Data Parser Module

Handles parsing of battery test data files with various formats and encodings.
Specializes in handling Basytec format with special considerations for DateTime fields.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
from io import StringIO

from .data_cleaner import DataCleaner, DeviceType, DecimalSeparator

logger = logging.getLogger(__name__)


class RawDataParser:
    """Parses raw battery test data from various formats"""
    
    # Expected columns in battery test data
    REQUIRED_COLUMNS = ['Time[h]', 'Command', 'U[V]', 'I[A]']
    OPTIONAL_COLUMNS = ['State', 'Cyc', 'Ah[Ah]', 'DateTime', 'DataSet',
                       'Ah-Cyc-Charge', 'Ah-Cyc-Discharge', 'Ah-Step', 
                       'Wh[Wh]', 'T1[°C]', 'T2[°C]']
    
    # Numeric columns that need conversion
    NUMERIC_COLUMNS = ['Time[h]', 'I[A]', 'U[V]', 'Ah[Ah]', 
                       'Ah-Cyc-Charge', 'Ah-Cyc-Discharge', 
                       'Ah-Step', 'Wh[Wh]', 'T1[°C]', 'T2[°C]',
                       'State', 'Cyc', 'DataSet']
    
    def __init__(self, device_type: DeviceType = DeviceType.BASYTEC):
        """Initialize parser with device type"""
        self.device_type = device_type
        self.data_cleaner = DataCleaner(device_type)
    
    def parse_data_from_content(
        self,
        content: str,
        skip_rows: int,
        column_header: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse data from cleaned content
        
        Args:
            content: Cleaned file content
            skip_rows: Number of header rows to skip
            column_header: Optional pre-parsed column header line
            
        Returns:
            DataFrame with parsed data
        """
        lines = content.split('\n')
        
        # Find or use the header line
        header_line = self._find_header_line(lines, skip_rows, column_header)
        
        if header_line:
            # Use custom parser for complex formats
            df = self._parse_with_header(lines, header_line, skip_rows)
        else:
            # Fallback to pandas parsing from string
            # Skip header lines and create StringIO for pandas
            data_lines = '\n'.join(lines[skip_rows:])
            df = pd.read_csv(StringIO(data_lines), sep='\t', engine='python')
        
        # Note: Decimal separators already fixed in clean_raw_text
        # Just need to convert data types
        df = self._convert_numeric_columns_simple(df)
        
        return df
    
    def parse_data_section(
        self,
        file_path: Path, 
        encoding: str, 
        skip_rows: int,
        column_header: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse the data section of a battery test file
        
        Args:
            file_path: Path to the data file
            encoding: File encoding to use
            skip_rows: Number of header rows to skip
            column_header: Optional pre-parsed column header line
            
        Returns:
            DataFrame with parsed data
        """
        # Read file content
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            lines = f.readlines()
        
        # Find or use the header line
        header_line = self._find_header_line(lines, skip_rows, column_header)
        
        if header_line:
            # Use custom parser for complex formats
            df = self._parse_with_header(lines, header_line, skip_rows)
        else:
            # Fallback to standard pandas parsing
            df = self._parse_with_pandas(file_path, encoding, skip_rows)
        
        # Apply data cleaning
        df = self.data_cleaner.clean_data(df)
        
        return df
    
    @staticmethod
    def _find_header_line(
        lines: List[str],
        skip_rows: int,
        provided_header: Optional[str] = None
    ) -> Optional[str]:
        """
        Find the column header line in the file

        Args:
            lines: All lines from the file
            skip_rows: Number of header rows
            provided_header: Optional pre-parsed header

        Returns:
            Header line string or None
        """
        if provided_header:
            return provided_header

        # Check for BioLogic format (column header at skip_rows - 1, no ~ prefix)
        if skip_rows > 0 and skip_rows <= len(lines):
            potential_header = lines[skip_rows - 1].strip()
            if 'Ecell/V' in potential_header or 'cycle number' in potential_header:
                return potential_header

        # Look for Basytec header line (usually the last line with ~)
        for i in range(min(skip_rows, len(lines)) - 1, -1, -1):
            if i < len(lines) and lines[i].startswith('~'):
                if 'Time[h]' in lines[i] or 'DataSet' in lines[i]:
                    return lines[i].strip('~').strip()

        return None
    
    @staticmethod
    def _parse_with_header(
        lines: List[str], 
        header_line: str, 
        skip_rows: int
    ) -> pd.DataFrame:
        """
        Parse data using a known header line
        
        Args:
            lines: All lines from the file
            header_line: The header line with column names
            skip_rows: Number of rows to skip
            
        Returns:
            DataFrame with parsed data
        """
        # Parse header to get column names
        columns = RawDataParser._parse_header_columns(header_line)
        
        if not columns:
            raise ValueError("Could not parse column names from header")
        
        # Find where data starts
        data_start_idx = RawDataParser._find_data_start(lines, skip_rows)
        
        # Parse data rows
        data_rows = RawDataParser._parse_data_rows(
            lines[data_start_idx:], 
            columns
        )
        
        if not data_rows:
            raise ValueError("No valid data rows found in file")
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=columns)
        
        # Convert numeric columns
        df = RawDataParser._convert_numeric_columns(df)
        
        # Validate required columns
        RawDataParser._validate_columns(df)
        
        return df
    
    @staticmethod
    def _parse_header_columns(header_line: str) -> List[str]:
        """
        Parse column names from header line
        
        Args:
            header_line: Header line string
            
        Returns:
            List of column names
        """
        # Try tab-separated first (most common for Basytec)
        columns = header_line.split('\t')
        
        if len(columns) <= 1:
            # Try space-separated
            columns = header_line.split()
        
        # Clean column names and fix encoding issues
        cleaned_columns = []
        for col in columns:
            col = col.strip()
            if col:
                # Fix temperature column with special character
                if 'T1[' in col and 'C]' in col:
                    col = 'T1[°C]'
                elif 'T2[' in col and 'C]' in col:
                    col = 'T2[°C]'
                cleaned_columns.append(col)
        
        logger.debug(f"Parsed {len(cleaned_columns)} columns from header")
        return cleaned_columns
    
    @staticmethod
    def _find_data_start(lines: List[str], skip_rows: int) -> int:
        """
        Find where actual data starts in the file
        
        Args:
            lines: All lines from file
            skip_rows: Expected number of header rows
            
        Returns:
            Index where data starts
        """
        # Data starts after header rows
        for i in range(skip_rows, len(lines)):
            if lines[i].strip() and not lines[i].startswith('~'):
                return i
        
        return skip_rows
    
    @staticmethod
    def _parse_data_rows(
        lines: List[str], 
        columns: List[str]
    ) -> List[List]:
        """
        Parse individual data rows handling special cases
        
        Args:
            lines: Data lines to parse
            columns: Column names
            
        Returns:
            List of parsed data rows
        """
        data_rows = []
        datetime_idx = None
        
        # Find DateTime column index if present
        if 'DateTime' in columns:
            datetime_idx = columns.index('DateTime')
        
        for line_num, line in enumerate(lines):
            if not line.strip() or line.startswith('~'):
                continue
            
            # Try tab-separated first
            parts = line.strip().split('\t')
            
            if len(parts) != len(columns):
                # Try space-separated with DateTime handling
                parts = line.strip().split()
                
                # Handle DateTime field that contains space
                if datetime_idx is not None and len(parts) > len(columns):
                    parts = RawDataParser._combine_datetime_parts(
                        parts, datetime_idx, len(columns)
                    )
            
            # Only add row if it has the right number of columns
            if len(parts) == len(columns):
                data_rows.append(parts)
            elif line_num < 10:  # Only log first few mismatches
                logger.debug(f"Row {line_num}: Column count mismatch - "
                           f"expected {len(columns)}, got {len(parts)}")
        
        logger.info(f"Parsed {len(data_rows)} valid data rows")
        return data_rows
    
    @staticmethod
    def _combine_datetime_parts(
        parts: List[str], 
        datetime_idx: int, 
        expected_cols: int
    ) -> List[str]:
        """
        Combine date and time parts that were split by space
        
        Args:
            parts: Split parts of the line
            datetime_idx: Index of DateTime column
            expected_cols: Expected number of columns
            
        Returns:
            Parts with combined DateTime
        """
        # Calculate how many extra parts we have
        extra_parts = len(parts) - expected_cols
        
        if extra_parts > 0 and datetime_idx < len(parts) - 1:
            # Combine the DateTime parts (usually date and time)
            # Assume DateTime is split into 2 parts
            combined_datetime = f"{parts[datetime_idx]} {parts[datetime_idx + 1]}"
            
            # Reconstruct parts list
            new_parts = (
                parts[:datetime_idx] + 
                [combined_datetime] + 
                parts[datetime_idx + 2:]
            )
            
            return new_parts
        
        return parts
    
    @staticmethod
    def _parse_with_pandas(
        file_path: Path, 
        encoding: str, 
        skip_rows: int
    ) -> pd.DataFrame:
        """
        Fallback parser using pandas read_csv
        
        Args:
            file_path: Path to file
            encoding: File encoding
            skip_rows: Rows to skip
            
        Returns:
            DataFrame with parsed data
        """
        # Try different delimiters
        for delimiter in ['\t', ' ', ';']:
            try:
                # For European format with comma decimals
                decimal = ',' if delimiter != ',' else '.'
                
                df = pd.read_csv(
                    file_path,
                    sep=delimiter,
                    skiprows=skip_rows,
                    encoding=encoding,
                    decimal=decimal,  # Handle comma as decimal separator
                    on_bad_lines='skip',
                    engine='python'
                )
                
                # Check if we got reasonable data
                if len(df.columns) > 5 and len(df) > 0:
                    # Clean column names
                    df.columns = [col.strip() for col in df.columns]
                    
                    # Convert numeric columns
                    df = RawDataParser._convert_numeric_columns(df)
                    
                    # Validate
                    RawDataParser._validate_columns(df)
                    
                    return df
                    
            except Exception as e:
                logger.debug(f"Failed with delimiter '{delimiter}': {e}")
                continue
        
        raise ValueError("Could not parse data with any delimiter")
    
    def _convert_numeric_columns_simple(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert string columns to numeric (decimals already fixed in cleaning)
        
        Args:
            df: DataFrame to convert
            
        Returns:
            DataFrame with numeric columns converted
        """
        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    @staticmethod
    def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert string columns to numeric where appropriate
        
        Args:
            df: DataFrame to convert
            
        Returns:
            DataFrame with numeric columns converted
        """
        for col in RawDataParser.NUMERIC_COLUMNS:
            if col in df.columns:
                # First replace comma decimal separators with dots (European format)
                # This is critical for Basytec data!
                if df[col].dtype == object:  # Only for string columns
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        """
        Validate that required columns are present

        Args:
            df: DataFrame to validate

        Raises:
            ValueError: If required columns are missing
        """
        # Define column alternatives for different device formats
        # At least one from each group must be present
        required_column_groups = {
            'voltage': ['U[V]', 'Ecell/V', 'Ewe/V', 'Voltage', 'Voltage(V)'],
            'current': ['I[A]', '<I>/mA', 'I/mA', 'Current', 'Current(A)'],
        }

        missing_groups = []
        for group_name, alternatives in required_column_groups.items():
            if not any(alt in df.columns for alt in alternatives):
                missing_groups.append(f"{group_name} (expected one of: {alternatives})")

        if missing_groups:
            raise ValueError(f"Required columns missing: {missing_groups}. "
                           f"Available columns: {list(df.columns)}")