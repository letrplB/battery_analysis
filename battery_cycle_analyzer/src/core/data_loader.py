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

logger = logging.getLogger(__name__)


class DataLoader:
    """Orchestrates loading and validation of battery test data files"""
    
    def __init__(self):
        """Initialize data loader with parser instances"""
        self.encoding_detector = EncodingDetector()
        self.metadata_parser = MetadataParser()
        self.raw_data_parser = RawDataParser()
    
    def load_file(self, file_path: str) -> RawBatteryData:
        """
        Load battery test file and extract all components
        
        Args:
            file_path: Path to the battery test file
            
        Returns:
            RawBatteryData object with loaded data and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Loading file: {file_path.name}")
        
        # Step 1: Detect encoding
        encoding = self.encoding_detector.detect_encoding(file_path)
        
        # Step 2: Parse metadata and find header info
        metadata, header_lines, column_header = self.metadata_parser.parse_header(
            file_path, encoding
        )
        
        # Step 3: Parse raw data
        data = self.raw_data_parser.parse_data_section(
            file_path, encoding, header_lines, column_header
        )
        
        # Step 4: Create column mapping
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