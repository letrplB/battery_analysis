"""
Metadata Parser Module

Extracts metadata from battery test file headers.
Handles various metadata formats and encoding issues.
"""

from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
import os

from .data_models import FileMetadata

logger = logging.getLogger(__name__)


class MetadataParser:
    """Parses metadata from battery test file headers"""

    # Known metadata field mappings for Basytec
    METADATA_MAPPINGS = {
        'Date and Time of Data Converting': 'date_converting',
        'Name of Test': 'test_name',
        'Battery': 'battery_name',
        'Start of Test': 'test_start',
        'End of Test': 'test_end',
        'Testchannel': 'test_channel',
        'Operator (Test)': 'operator_test',
        'Operator (Data converting)': 'operator_converting',
        'Testplan': 'test_plan'
    }

    # BioLogic BT-Lab metadata field mappings
    BIOLOGIC_METADATA_MAPPINGS = {
        'Electrode material': 'test_name',
        'Acquisition started on': 'test_start',
        'Run on channel': 'test_channel',
        'User': 'operator_test',
        'Device': 'additional_metadata',
        'Mass of active material': 'additional_metadata',
        'Characteristic mass': 'additional_metadata',
        'Battery capacity': 'additional_metadata',
    }
    
    @staticmethod
    def parse_header_from_content(
        content: str,
        file_name: str = "unknown.txt",
        file_size_kb: float = 0
    ) -> Tuple[FileMetadata, int, Optional[str]]:
        """
        Parse metadata from cleaned file content

        Args:
            content: Cleaned file content
            file_name: Original file name
            file_size_kb: File size in KB

        Returns:
            Tuple of (metadata, header_lines_count, column_header_line)
        """
        lines = content.split('\n')

        metadata = FileMetadata(
            file_name=file_name,
            file_size_kb=file_size_kb,
            total_lines=len(lines)
        )

        # Detect file type and parse accordingly
        if MetadataParser._is_biologic_file(content):
            return MetadataParser._parse_biologic_header(lines, metadata)
        else:
            return MetadataParser._parse_basytec_header(lines, metadata)

    @staticmethod
    def _is_biologic_file(content: str) -> bool:
        """Check if content is from a BioLogic BT-Lab file"""
        first_lines = content[:500]
        return 'BT-Lab ASCII FILE' in first_lines or 'Nb header lines' in first_lines

    @staticmethod
    def _parse_basytec_header(
        lines: List[str],
        metadata: FileMetadata
    ) -> Tuple[FileMetadata, int, Optional[str]]:
        """Parse Basytec format header (lines starting with ~)"""
        header_lines = 0
        column_header = None

        # Parse header lines (lines starting with ~)
        for i, line in enumerate(lines):
            if not line.startswith('~'):
                break

            header_lines += 1

            # Skip empty metadata lines
            if line.strip() == '~':
                continue

            # Check for column header
            if 'Time[h]' in line or 'DataSet' in line:
                column_header = line.strip('~').strip()
                continue

            # Parse metadata key-value pairs
            if ':' in line:
                key_value = line[1:].strip()  # Remove ~ prefix
                if ':' in key_value:
                    key, value = key_value.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    # Map to metadata fields
                    if key in MetadataParser.METADATA_MAPPINGS:
                        field = MetadataParser.METADATA_MAPPINGS[key]
                        setattr(metadata, field, value)

        logger.info(f"Parsed {header_lines} Basytec header lines")
        return metadata, header_lines, column_header

    @staticmethod
    def _parse_biologic_header(
        lines: List[str],
        metadata: FileMetadata
    ) -> Tuple[FileMetadata, int, Optional[str]]:
        """Parse BioLogic BT-Lab format header"""
        header_lines = 0
        column_header = None

        # Find number of header lines from "Nb header lines : XX"
        for line in lines[:10]:
            if 'Nb header lines' in line:
                try:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        header_lines = int(parts[1].strip())
                        break
                except (ValueError, IndexError):
                    pass

        if header_lines == 0:
            # Fallback: scan for column header
            for i, line in enumerate(lines):
                if 'Ecell/V' in line or 'cycle number' in line:
                    header_lines = i + 1
                    break

        # Get column header (last line of header section)
        if header_lines > 0 and header_lines <= len(lines):
            column_header = lines[header_lines - 1].strip()

        # Parse metadata from header lines
        for i in range(min(header_lines, len(lines))):
            line = lines[i].strip()

            if ':' in line and not line.startswith('\t'):
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()

                # Map BioLogic metadata fields
                if key in MetadataParser.BIOLOGIC_METADATA_MAPPINGS:
                    field = MetadataParser.BIOLOGIC_METADATA_MAPPINGS[key]
                    if field == 'additional_metadata':
                        if metadata.additional_metadata is None:
                            metadata.additional_metadata = {}
                        metadata.additional_metadata[key] = value
                    else:
                        setattr(metadata, field, value)

        logger.info(f"Parsed {header_lines} BioLogic header lines")
        return metadata, header_lines, column_header
    
    @staticmethod
    def parse_header(
        file_path: Path, 
        encoding: str
    ) -> Tuple[FileMetadata, int, Optional[str]]:
        """
        Parse metadata from file header
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            Tuple of (metadata, header_lines_count, column_header_line)
        """
        metadata = FileMetadata(
            file_name=file_path.name,
            file_size_kb=file_path.stat().st_size / 1024,
            total_lines=0,
            additional_metadata={}
        )
        
        header_lines = 0
        column_header_line = None
        
        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
            for line in file:
                # Stop at first non-header line
                if not line.startswith('~'):
                    break
                
                header_lines += 1
                
                # Check if this is the column header line
                if MetadataParser._is_column_header(line):
                    column_header_line = line.strip('~').strip()
                    logger.debug(f"Found column header at line {header_lines}")
                    continue
                
                # Parse metadata from this line
                MetadataParser._parse_metadata_line(line, metadata)
        
        # Count total lines in file
        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
            metadata.total_lines = sum(1 for _ in file)
        
        logger.info(f"Parsed metadata: {header_lines} header lines, "
                   f"{metadata.total_lines} total lines")
        
        return metadata, header_lines, column_header_line
    
    @staticmethod
    def _is_column_header(line: str) -> bool:
        """
        Check if a line is the column header line
        
        Args:
            line: Line to check
            
        Returns:
            True if this is the column header
        """
        # Column headers typically contain these keywords
        column_indicators = ['Time[h]', 'DataSet', 'DateTime', 'Command', 'U[V]', 'I[A]']
        
        # Check if multiple indicators are present
        matches = sum(1 for indicator in column_indicators if indicator in line)
        
        return matches >= 3  # Need at least 3 column names to be confident
    
    @staticmethod
    def _parse_metadata_line(line: str, metadata: FileMetadata) -> None:
        """
        Parse a single metadata line and update metadata object
        
        Args:
            line: Line to parse (starting with ~)
            metadata: Metadata object to update
        """
        # Remove ~ prefix and clean
        line = line.strip('~').strip()
        
        if not line or ':' not in line:
            return
        
        # Split on first colon
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        
        # Check if this is a known metadata field
        for known_key, attr_name in MetadataParser.METADATA_MAPPINGS.items():
            if known_key in key:
                setattr(metadata, attr_name, value)
                logger.debug(f"Set metadata.{attr_name} = {value}")
                return
        
        # Store unknown fields in additional_metadata
        metadata.additional_metadata[key] = value
    
    @staticmethod
    def extract_test_info(metadata: FileMetadata) -> Dict[str, str]:
        """
        Extract key test information from metadata
        
        Args:
            metadata: Metadata object
            
        Returns:
            Dictionary of key test information
        """
        info = {}
        
        if metadata.test_name:
            info['Test Name'] = metadata.test_name
        
        if metadata.battery_name:
            info['Battery'] = metadata.battery_name
        
        if metadata.test_start and metadata.test_end:
            info['Duration'] = f"{metadata.test_start} to {metadata.test_end}"
        
        if metadata.test_channel:
            info['Channel'] = metadata.test_channel
        
        if metadata.operator_test:
            info['Operator'] = metadata.operator_test
        
        return info