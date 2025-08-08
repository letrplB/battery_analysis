"""
Core modules for Battery Cycle Analyzer

This package contains the core data processing pipeline:

- data_models: Data structures and models
- encoding_detector: File encoding detection
- metadata_parser: Metadata extraction from headers
- raw_data_parser: Raw data parsing and validation
- data_loader: Orchestrates file loading
- preprocessor: Data preprocessing and cycle detection
- test_plan_parser: Test plan parsing for C-rate extraction
"""

from .data_models import (
    FileMetadata,
    RawBatteryData,
    ProcessingParameters,
    PreprocessedData,
    AnalysisConfig,
    AnalysisResults
)
from .data_loader import DataLoader
from .preprocessor import DataPreprocessor
from .test_plan_parser import TestPlanParser, TestPlanConfig, CRatePeriod
from .encoding_detector import EncodingDetector
from .metadata_parser import MetadataParser
from .raw_data_parser import RawDataParser

__all__ = [
    'FileMetadata',
    'RawBatteryData',
    'ProcessingParameters',
    'PreprocessedData',
    'AnalysisConfig',
    'AnalysisResults',
    'DataLoader',
    'DataPreprocessor',
    'TestPlanParser',
    'TestPlanConfig',
    'CRatePeriod',
    'EncodingDetector',
    'MetadataParser',
    'RawDataParser'
]