# Battery Cycle Analyzer - Source Code Structure

## 📁 Directory Structure

```
src/
├── gui_modular.py          # Main entry point - modular GUI application
├── core/                   # Core data processing pipeline
│   ├── data_models.py      # Data structures and models
│   ├── data_loader.py      # File loading and parsing
│   └── preprocessor.py     # Data preprocessing and cycle detection
├── analysis_modes/         # Analysis implementations
│   ├── standard_cycle.py   # Standard capacity/retention analysis
│   └── dqdu_analysis.py    # Differential capacity (dQ/dU) analysis
├── gui_components/         # Modular GUI components
│   ├── data_input.py       # File upload and data loading
│   ├── preprocessing.py    # Parameter configuration
│   ├── analysis_selector.py # Analysis mode selection
│   ├── results_viewer.py   # Results display
│   └── export_manager.py   # Export functionality
└── legacy/                 # Previous implementations (deprecated)
    ├── analyzer.py         # Original analysis functions
    ├── gui.py             # Original monolithic GUI
    └── gui_refactored.py  # Intermediate refactored version
```

## 🚀 Quick Start

Run the main application:
```bash
streamlit run gui_modular.py
```

## 🏗️ Architecture

### Data Flow
1. **Input**: User uploads battery test file
2. **Preprocessing**: Data validation and cycle detection
3. **Analysis**: Mode-specific analysis (standard/dQ/dU)
4. **Output**: Results visualization and export

### Module Responsibilities

#### Core (`core/`)
- **data_models.py**: Defines data structures used throughout the application
- **data_loader.py**: Handles file parsing and initial validation
- **preprocessor.py**: Performs cycle detection and data preparation

#### Analysis Modes (`analysis_modes/`)
- **standard_cycle.py**: Calculates capacity, retention, efficiency
- **dqdu_analysis.py**: Performs differential capacity analysis

#### GUI Components (`gui_components/`)
- **data_input.py**: Manages file upload interface
- **preprocessing.py**: Handles parameter configuration UI
- **analysis_selector.py**: Provides analysis mode selection and settings
- **results_viewer.py**: Displays analysis results and plots
- **export_manager.py**: Manages data export in various formats

## 🔄 Processing Pipeline

```
File Upload → Data Loading → Preprocessing → Analysis → Results → Export
     ↓             ↓              ↓             ↓          ↓         ↓
data_input → data_loader → preprocessor → analysis → viewer → export
                                            modes
```

## 📝 Adding New Features

### Adding a New Analysis Mode
1. Create new file in `analysis_modes/`
2. Implement analysis class/functions
3. Add to `analysis_modes/__init__.py`
4. Update `analysis_selector.py` to include new mode

### Adding a New Export Format
1. Update `export_manager.py`
2. Add format conversion logic
3. Update UI to show new option

## 🧪 Testing

Run individual modules for testing:
```python
python -m core.data_loader
python -m analysis_modes.standard_cycle
```

## 📚 Legacy Code

The `legacy/` folder contains previous implementations:
- **analyzer.py**: Original analysis functions (replaced by core modules)
- **gui.py**: Original monolithic GUI (replaced by modular components)
- **gui_refactored.py**: Intermediate version

These files are kept for reference but should not be used for new development.