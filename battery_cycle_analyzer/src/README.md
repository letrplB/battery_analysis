# Battery Cycle Analyzer - Source Code Documentation

## Directory Structure

```
src/
├── gui_modular.py           # Main application entry point
├── core/                    # Core data processing modules
│   ├── data_models.py       # Data structures and type definitions
│   ├── data_loader.py       # File loading orchestration
│   ├── data_cleaner.py      # Data cleaning and device profiles
│   ├── preprocessor.py      # Cycle detection and preprocessing
│   ├── encoding_detector.py # Character encoding detection
│   ├── metadata_parser.py   # Header metadata extraction
│   ├── raw_data_parser.py   # Raw data parsing and validation
│   └── test_plan_parser.py  # Test plan C-rate extraction
├── analysis_modes/          # Analysis implementations
│   ├── standard_cycle.py    # Standard capacity/efficiency analysis
│   └── dqdu_analysis.py     # Differential capacity (dQ/dU) analysis
└── gui_components/          # Modular UI components
    ├── data_input.py        # File upload and device selection
    ├── preprocessing.py     # Parameter configuration interface
    ├── analysis_selector.py # Analysis mode selection
    ├── results_viewer.py    # Results display and visualization
    └── export_manager.py    # Data export functionality
```

## Architecture Overview

### Data Processing Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Data Input  │────▶│ Preprocessing│────▶│   Analysis   │
│             │     │              │     │              │
│ • File      │     │ • Cleaning   │     │ • Standard   │
│ • Device    │     │ • Cycle      │     │ • dQ/dU      │
│ • Test Plan │     │   Detection  │     │ • Combined   │
└─────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                          ┌──────────────┐     ┌──────────────┐
                          │   Results    │────▶│    Export    │
                          │              │     │              │
                          │ • Plots      │     │ • CSV        │
                          │ • Tables     │     │ • Excel      │
                          │ • Metrics    │     │ • JSON       │
                          └──────────────┘     └──────────────┘
```

### Module Responsibilities

#### Core Modules (`core/`)

**data_models.py**
- Defines all data structures (RawBatteryData, PreprocessedData, AnalysisResults)
- Type hints and validation models
- Shared constants and enumerations

**data_loader.py**
- Orchestrates the file loading process
- Delegates to appropriate parsers based on device type
- Handles error recovery and validation

**data_cleaner.py**
- Device-specific data cleaning profiles
- Column mapping and standardization
- Unit conversions and formatting

**preprocessor.py**
- Cycle boundary detection (state-based and zero-crossing)
- Data validation and quality checks
- Capacity calculation and metadata extraction

#### Analysis Modes (`analysis_modes/`)

**standard_cycle.py**
- Capacity, retention, and efficiency calculations
- Trend analysis and statistics
- Visualization generation

**dqdu_analysis.py**
- Differential capacity computation
- Peak detection and analysis
- Phase transition identification

#### GUI Components (`gui_components/`)

**data_input.py**
- File upload interface
- Device type selection
- Test plan upload and parsing

**preprocessing.py**
- Parameter configuration (material weight, capacity)
- C-rate settings
- Boundary detection options

**analysis_selector.py**
- Analysis mode tabs (Standard, dQ/dU, Combined)
- Mode-specific settings
- Analysis execution

**results_viewer.py**
- Results visualization
- Interactive plots
- Data tables

**export_manager.py**
- Multiple export formats
- Report generation
- Advanced export options

## Key Design Patterns

### 1. Modular Architecture
Each component has a single responsibility and communicates through well-defined interfaces.

### 2. Data Pipeline
Data flows through discrete processing stages with validation at each step.

### 3. Device Abstraction
Device-specific logic is encapsulated in the DeviceType enum and associated cleaners.

### 4. Component Isolation
GUI components are independent and can be modified without affecting others.

## Adding New Features

### New Device Support
1. Add device to `DeviceType` enum in `data_cleaner.py`
2. Implement cleaning profile in `DataCleaner`
3. Add parser logic if needed

### New Analysis Mode
1. Create module in `analysis_modes/`
2. Implement analysis logic following existing patterns
3. Add UI component in `analysis_selector.py`

### New Export Format
1. Extend `export_manager.py`
2. Add format conversion method
3. Update UI options

## Development Guidelines

### Code Style
- Use type hints for all function parameters
- Follow PEP 8 naming conventions
- Add docstrings to all public functions
- Keep functions focused and under 50 lines

### Error Handling
- Use logging for debugging information
- Provide user-friendly error messages
- Validate data at module boundaries
- Handle edge cases gracefully

### Testing
Run individual modules:
```bash
python -m core.data_loader
python -m analysis_modes.standard_cycle
```

Run the full application:
```bash
streamlit run gui_modular.py
```

## Performance Considerations

- Large files (>100MB) are processed in chunks
- Cycle detection uses vectorized operations
- Plots use sampling for very large datasets
- Caching is used for expensive computations

## Dependencies

Core dependencies:
- `streamlit`: Web application framework
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `scipy`: Scientific computing
- `plotly`: Interactive visualizations

Optional dependencies:
- `openpyxl`: Excel file support
- `xlsxwriter`: Excel export
- `chardet`: Encoding detection

## Future Improvements

- [ ] Add more analysis modes (EIS, rate capability)
- [ ] Implement data caching for faster reanalysis
- [ ] Add batch processing for multiple files
- [ ] Create REST API for programmatic access
- [ ] Add unit tests for core modules