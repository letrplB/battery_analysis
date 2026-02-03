"""
Data Loader Module

Orchestrates the loading of battery test data files by coordinating
specialized parsers for encoding, metadata, and raw data.
"""

import pandas as pd
from typing import Dict
from pathlib import Path
import logging

from .data_models import FileMetadata, RawBatteryData
from .encoding_detector import EncodingDetector
from .metadata_parser import MetadataParser
from .raw_data_parser import RawDataParser
from .data_cleaner import DeviceType, DataCleaner

logger = logging.getLogger(__name__)


class DataLoader:
    """Orchestrates loading and validation of battery test data files"""
    
    def __init__(self, device_type: DeviceType = DeviceType.BASYTEC):
        """Initialize data loader with parser instances
        
        Args:
            device_type: Type of battery tester device (default: BASYTEC)
        """
        self.device_type = device_type
        self.encoding_detector = EncodingDetector()
        self.metadata_parser = MetadataParser()
        self.raw_data_parser = RawDataParser(device_type)
        self.data_cleaner = DataCleaner(device_type)
    
    def load_file(self, file_path: str, device_type: DeviceType = None) -> RawBatteryData:
        """
        Load battery test file and extract all components
        
        Args:
            file_path: Path to the battery test file
            device_type: Override device type for this specific file
            
        Returns:
            RawBatteryData object with loaded data and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Loading file: {file_path.name}")
        
        # Update device type if provided
        if device_type and device_type != self.device_type:
            self.device_type = device_type
            self.raw_data_parser = RawDataParser(device_type)
            self.data_cleaner = DataCleaner(device_type)
        
        # Step 1: Detect encoding
        encoding = self.encoding_detector.detect_encoding(file_path)
        
        # Step 2: Read and clean raw file content FIRST
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            raw_content = f.read()
        
        # Get file info for metadata
        file_size_kb = file_path.stat().st_size / 1024
        
        # Clean the raw text based on device type (decimal separators, special chars, etc.)
        cleaned_content = self.data_cleaner.clean_raw_text(raw_content)
        
        # Step 3: Parse metadata from cleaned content
        metadata, header_lines, column_header = self.metadata_parser.parse_header_from_content(
            cleaned_content,
            file_name=file_path.name,
            file_size_kb=file_size_kb
        )
        
        # Step 4: Parse data from cleaned content
        data = self.raw_data_parser.parse_data_from_content(
            cleaned_content, header_lines, column_header
        )

        # Step 5: Apply device-specific cleaning (column mapping, unit conversions, etc.)
        data = self.data_cleaner.clean_data(data)

        # Step 6: Create column mapping
        column_mapping = self._create_column_mapping(data)
        
        # Step 5: Detect available features
        has_state = 'State' in data.columns
        has_cycle = 'Cyc' in data.columns or 'Cycle' in data.columns
        
        logger.info(f"Loaded {len(data)} data rows with {len(data.columns)} columns")
        logger.info(f"Features: State={'Yes' if has_state else 'No'}, "
                   f"Cycle={'Yes' if has_cycle else 'No'}")
        
        return RawBatteryData(
            data=data,
            metadata=metadata,
            column_mapping=column_mapping,
            has_state_column=has_state,
            has_cycle_column=has_cycle
        )
    
    def _create_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Create mapping for column name variations
        
        Args:
            df: DataFrame with columns
            
        Returns:
            Dictionary mapping standard names to actual column names
        """
        mapping = {}
        
        # Define alternative names for standard columns
        alternatives = {
            'Time[h]': ['Time', 't[h]', 'Time_h', 'Time(h)'],
            'Command': ['Cmd', 'Mode', 'Step'],
            'U[V]': ['V[V]', 'Voltage[V]', 'U', 'Voltage'],
            'I[A]': ['Current[A]', 'I', 'Current'],
            'State': ['Status', 'Cycle_State'],
            'Cyc': ['Cycle', 'Cycle_Number', 'Cyc_Nb']
        }
        
        for standard_name, alt_names in alternatives.items():
            # First check if standard name exists
            if standard_name in df.columns:
                mapping[standard_name] = standard_name
            else:
                # Look for alternatives
                for alt in alt_names:
                    if alt in df.columns:
                        mapping[standard_name] = alt
                        logger.debug(f"Mapped {standard_name} -> {alt}")
                        break
        
        return mapping