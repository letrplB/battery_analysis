"""
Encoding Detector Module

Detects file encoding for proper text parsing.
Handles various encodings commonly used in battery test files.
"""

import chardet
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EncodingDetector:
    """Detects and validates file encodings"""
    
    # Common encodings for battery test files
    COMMON_ENCODINGS = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    # Sample size for detection (in bytes)
    SAMPLE_SIZE = 10000
    
    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """
        Detect file encoding using chardet library
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding string
        """
        try:
            with open(file_path, 'rb') as f:
                # Read sample for detection
                raw_data = f.read(EncodingDetector.SAMPLE_SIZE)
                
                # Use chardet to detect encoding
                result = chardet.detect(raw_data)
                
                if result and result['encoding']:
                    encoding = result['encoding']
                    confidence = result.get('confidence', 0)
                    
                    logger.info(f"Detected encoding: {encoding} "
                              f"(confidence: {confidence:.2%})")
                    
                    # Validate encoding
                    if EncodingDetector._validate_encoding(file_path, encoding):
                        return encoding
                    else:
                        logger.warning(f"Detected encoding {encoding} failed validation")
                
        except Exception as e:
            logger.warning(f"Error detecting encoding: {e}")
        
        # Fallback to trying common encodings
        return EncodingDetector._try_common_encodings(file_path)
    
    @staticmethod
    def _validate_encoding(file_path: Path, encoding: str) -> bool:
        """
        Validate that the detected encoding can read the file
        
        Args:
            file_path: Path to file
            encoding: Encoding to validate
            
        Returns:
            True if encoding is valid
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Try to read first 100 lines
                for i, line in enumerate(f):
                    if i >= 100:
                        break
                    # Check for common patterns
                    if '~' in line or 'Time[h]' in line:
                        return True
                
                return True  # If no errors, encoding is valid
                
        except (UnicodeDecodeError, UnicodeError):
            return False
    
    @staticmethod
    def _try_common_encodings(file_path: Path) -> str:
        """
        Try common encodings when detection fails
        
        Args:
            file_path: Path to file
            
        Returns:
            First working encoding or 'utf-8' as default
        """
        for encoding in EncodingDetector.COMMON_ENCODINGS:
            if EncodingDetector._validate_encoding(file_path, encoding):
                logger.info(f"Using fallback encoding: {encoding}")
                return encoding
        
        # Default to utf-8 with error handling
        logger.warning("No valid encoding found, defaulting to utf-8")
        return 'utf-8'
    
    @staticmethod
    def read_with_encoding(
        file_path: Path, 
        encoding: Optional[str] = None
    ) -> str:
        """
        Read file content with proper encoding
        
        Args:
            file_path: Path to file
            encoding: Optional encoding to use
            
        Returns:
            File content as string
        """
        if not encoding:
            encoding = EncodingDetector.detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise