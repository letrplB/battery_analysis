import pandas as pd
from typing import Dict, Tuple
import chardet
from pathlib import Path

from core.data_models import FileMetadata, RawBatteryData


class DataLoader:
    """Handles loading and initial validation of battery test data files"""
    
    REQUIRED_COLUMNS = ['Time[h]', 'Command', 'U[V]', 'I[A]']
    OPTIONAL_COLUMNS = ['State', 'Cyc', 'Ah[Ah]', 'Ah-Cyc-Charge', 'Ah-Cyc-Discharge']
    
    @staticmethod
    def load_file(file_path: str) -> RawBatteryData:
        """Load battery test file and extract metadata"""
        file_path = Path(file_path)
        
        # Get file size
        file_size_kb = file_path.stat().st_size / 1024
        
        # Detect encoding
        encoding = DataLoader._detect_encoding(file_path)
        
        # Parse header and get metadata
        metadata, header_lines = DataLoader._parse_header(file_path, encoding)
        metadata.file_name = file_path.name
        metadata.file_size_kb = file_size_kb
        
        # Load data
        data = DataLoader._load_data_section(file_path, encoding, header_lines)
        
        # Count total lines
        with open(file_path, 'r', encoding=encoding) as f:
            total_lines = sum(1 for _ in f)
        metadata.total_lines = total_lines
        
        # Validate columns and create mapping
        column_mapping = DataLoader._validate_columns(data)
        
        # Check for optional columns
        has_state = 'State' in data.columns
        has_cycle = 'Cyc' in data.columns or 'Cycle' in data.columns
        
        return RawBatteryData(
            data=data,
            metadata=metadata,
            column_mapping=column_mapping,
            has_state_column=has_state,
            has_cycle_column=has_cycle
        )
    
    @staticmethod
    def _detect_encoding(file_path: Path) -> str:
        """Detect file encoding"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    
    @staticmethod
    def _parse_header(file_path: Path, encoding: str) -> Tuple[FileMetadata, int]:
        """Parse metadata from file header"""
        metadata = FileMetadata(
            file_name="",
            file_size_kb=0,
            total_lines=0,
            additional_metadata={}
        )
        
        header_lines = 0
        
        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
            for line in file:
                if not line.startswith('~'):
                    break
                    
                header_lines += 1
                line = line.strip('~').strip()
                
                if not line:
                    continue
                
                # Parse known metadata fields
                if 'Date and Time of Data Converting:' in line:
                    metadata.date_converting = line.split(':', 1)[1].strip()
                elif 'Name of Test:' in line:
                    metadata.test_name = line.split(':', 1)[1].strip()
                elif 'Battery:' in line:
                    metadata.battery_name = line.split(':', 1)[1].strip()
                elif 'Start of Test:' in line:
                    metadata.test_start = line.split(':', 1)[1].strip()
                elif 'End of Test:' in line:
                    metadata.test_end = line.split(':', 1)[1].strip()
                elif 'Testchannel:' in line:
                    metadata.test_channel = line.split(':', 1)[1].strip()
                elif 'Operator (Test):' in line:
                    metadata.operator_test = line.split(':', 1)[1].strip()
                elif 'Operator (Data converting):' in line:
                    metadata.operator_converting = line.split(':', 1)[1].strip()
                elif 'Testplan:' in line:
                    metadata.test_plan = line.split(':', 1)[1].strip()
                elif ':' in line:
                    # Store other metadata
                    key, value = line.split(':', 1)
                    metadata.additional_metadata[key.strip()] = value.strip()
        
        return metadata, header_lines
    
    @staticmethod
    def _load_data_section(file_path: Path, encoding: str, skip_rows: int) -> pd.DataFrame:
        """Load the data section of the file"""
        # Try different delimiters
        for delimiter in ['\t', ' ', ',', ';']:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=delimiter,
                    skiprows=skip_rows,
                    encoding=encoding,
                    on_bad_lines='skip',
                    engine='python'
                )
                
                # Check if we got reasonable data
                if len(df.columns) > 5 and len(df) > 0:
                    # Clean column names
                    df.columns = [col.strip() for col in df.columns]
                    return df
                    
            except Exception:
                continue
        
        raise ValueError(f"Could not parse data from {file_path.name}")
    
    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> Dict[str, str]:
        """Validate required columns exist and create mapping"""
        column_mapping = {}
        
        for req_col in DataLoader.REQUIRED_COLUMNS:
            if req_col not in df.columns:
                # Try to find alternative names
                alternatives = {
                    'Time[h]': ['Time', 't[h]', 'Time_h'],
                    'Command': ['Cmd', 'Mode'],
                    'U[V]': ['V[V]', 'Voltage[V]', 'U'],
                    'I[A]': ['Current[A]', 'I']
                }
                
                found = False
                for alt in alternatives.get(req_col, []):
                    if alt in df.columns:
                        column_mapping[req_col] = alt
                        found = True
                        break
                
                if not found:
                    raise ValueError(f"Required column '{req_col}' not found in data")
            else:
                column_mapping[req_col] = req_col
        
        return column_mapping