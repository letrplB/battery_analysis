from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd


@dataclass
class FileMetadata:
    """Metadata extracted from battery test file headers"""
    file_name: str
    file_size_kb: float
    total_lines: int
    date_converting: Optional[str] = None
    test_name: Optional[str] = None
    battery_name: Optional[str] = None
    test_start: Optional[str] = None
    test_end: Optional[str] = None
    test_channel: Optional[str] = None
    operator_test: Optional[str] = None
    operator_converting: Optional[str] = None
    test_plan: Optional[str] = None
    additional_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class RawBatteryData:
    """Raw data loaded from battery test file"""
    data: pd.DataFrame
    metadata: FileMetadata
    column_mapping: Dict[str, str]
    has_state_column: bool = False
    has_cycle_column: bool = False


@dataclass
class ProcessingParameters:
    """Parameters for data preprocessing"""
    active_material_weight: float  # in grams
    theoretical_capacity: float  # in Ah
    c_rates: List[Tuple[int, int, float, float]]  # (start_cycle, end_cycle, charge_rate, discharge_rate)
    boundary_method: str = "State-based"
    baseline_cycle: int = 30  # for retention calculation


@dataclass
class PreprocessedData:
    """Data after preprocessing, ready for analysis"""
    raw_data: RawBatteryData
    parameters: ProcessingParameters
    cycle_boundaries: List[Tuple[int, int]]  # List of (start_idx, end_idx) for each cycle
    cycle_metadata: pd.DataFrame  # Basic info about each cycle
    validation_warnings: List[str]
    

@dataclass
class AnalysisConfig:
    """Configuration for specific analysis modes"""
    mode: str  # "standard", "dqdu", "combined"
    
    # Standard cycle analysis config
    plot_types: List[str] = field(default_factory=list)
    
    # dQ/dU analysis config
    selected_cycles: List[int] = field(default_factory=list)
    voltage_filter_enabled: bool = False
    voltage_range: Tuple[float, float] = None
    smoothing_method: str = "None"
    smoothing_window: int = 5
    peak_detection_enabled: bool = False
    peak_prominence: float = 0.1
    interpolation_points: int = 333


@dataclass
class AnalysisResults:
    """Unified results container for all analysis types"""
    mode: str
    cycle_data: Optional[pd.DataFrame] = None
    summary_stats: Optional[Dict[str, Any]] = None
    plots: Optional[Dict[str, Any]] = None  # Plotly figures
    dqdu_data: Optional[pd.DataFrame] = None
    peak_data: Optional[pd.DataFrame] = None
    warnings: List[str] = field(default_factory=list)
    export_data: Optional[pd.DataFrame] = None