"""
Core modules for Battery Cycle Analyzer

This package contains the core data processing pipeline:

- data_models: Data structures and models
- data_loader: File loading and parsing
- preprocessor: Data preprocessing and cycle detection
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

__all__ = [
    'FileMetadata',
    'RawBatteryData',
    'ProcessingParameters',
    'PreprocessedData',
    'AnalysisConfig',
    'AnalysisResults',
    'DataLoader',
    'DataPreprocessor'
]