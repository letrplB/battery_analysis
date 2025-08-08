# Battery Cycle Analyzer

A modern, modular Python application for analyzing battery cycle stability data from various battery test systems. Features automated parsing, cycle detection, capacity calculation, differential capacity (dQ/dU) analysis, and professional visualizations through a clean web interface.

**Note:** This package is part of the [battery_analysis](https://github.com/letrplB/battery_analysis) repository, which contains multiple battery analysis tools sharing a common environment.

## Features

- **Multi-format Support**: Basytec, Arbin, Neware, BioLogic, Maccor, and generic CSV formats
- **Advanced Analysis Modes**:
  - Standard cycle analysis (capacity, retention, efficiency)
  - Differential capacity (dQ/dU) analysis for degradation mechanisms
  - Combined analysis mode for comprehensive insights
- **Professional Interface**: Clean, icon-based UI with Lucide icons
- **Flexible Export**: CSV, Excel, JSON formats with detailed reports

## Quick Start

### Requirements

- Python 3.8 or higher
- pip (Python package installer)

### Setup from GitHub

**For detailed setup instructions after cloning from GitHub, see [SETUP.md](SETUP.md)**

### Quick Installation

1. Clone the main repository:
   ```bash
   git clone https://github.com/letrplB/battery_analysis.git
   cd battery_analysis
   ```

2. Create and activate virtual environment (at repository root):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies (from repository root):
   ```bash
   pip install -r requirements.txt
   ```

4. Navigate to this package:
   ```bash
   cd battery_cycle_analyzer
   ```

### Running the Application

```bash
streamlit run src/gui_modular.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage Guide

### 1. Data Input

- **Select Device Type**: Choose your battery tester (Basytec, Arbin, Neware, etc.)
- **Upload Data File**: Drag and drop or browse for your test data (.txt or .csv)
- **Optional Test Plan**: Upload test plan file for automatic C-rate configuration

### 2. Analysis Parameters

Configure your analysis settings:
- **Active Material Weight** (grams)
- **Theoretical Capacity** (Ah)
- **C-Rate Configuration** (manual or from test plan)
- **Boundary Detection Method** (State-based or Zero-crossing)
- **Baseline Cycle** for retention calculations

### 3. Analysis Modes

Choose from three analysis modes:

#### Standard Cycle Analysis
- Capacity vs. cycle trends
- Retention and efficiency tracking
- Voltage range evolution
- Cycle-by-cycle statistics

#### dQ/dU Analysis
- Differential capacity curves
- Peak detection for phase transitions
- Degradation mechanism identification
- Multi-cycle comparison

#### Combined Analysis
- Both standard and dQ/dU analysis
- Optimized settings for comprehensive analysis
- Unified reporting

### 4. Export Results

Download your analysis results in multiple formats:
- **CSV**: Raw data and analysis results
- **Excel**: Multi-sheet workbook with all data
- **JSON**: Machine-readable format
- **Report**: Text summary of findings

## Supported File Formats

### Basytec Format
- Metadata headers starting with `~`
- Space/tab-separated columns
- European decimal format (comma as decimal separator)

### Arbin Format
- Standard CSV structure
- Time in seconds (automatically converted to hours)

### Other Formats
- Neware, BioLogic, Maccor: Device-specific parsers
- Generic CSV: Flexible column mapping

## Project Structure

```
battery_cycle_analyzer/
├── src/
│   ├── gui_modular.py           # Main application entry
│   ├── core/                    # Core functionality
│   │   ├── data_loader.py       # File loading logic
│   │   ├── data_cleaner.py      # Data cleaning utilities
│   │   ├── preprocessor.py      # Data preprocessing
│   │   ├── data_models.py       # Data structures
│   │   └── test_plan_parser.py  # Test plan parsing
│   ├── analysis_modes/          # Analysis algorithms
│   │   ├── standard_cycle.py    # Standard analysis
│   │   └── dqdu_analysis.py     # dQ/dU analysis
│   └── gui_components/          # UI components
│       ├── data_input.py        # File upload interface
│       ├── preprocessing.py     # Parameter configuration
│       ├── analysis_selector.py # Analysis mode selection
│       ├── results_viewer.py    # Results display
│       └── export_manager.py    # Export functionality
├── data/                        # Data directory
│   └── output/                  # Export location
├── logs/                        # Application logs
└── README.md                    # This file
```

## Advanced Configuration

### Streamlit Configuration

The application uses Streamlit's configuration system. Create a `.streamlit/config.toml` file to customize:

```toml
[theme]
primaryColor = "#3b82f6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### Custom Device Profiles

Add support for new device types by extending the `DeviceType` enum in `src/core/data_cleaner.py` and implementing the corresponding parser.

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
streamlit run src/gui_modular.py --server.port 8502
```

**Large File Processing**
- Files over 100MB may take time to process
- Consider splitting very large datasets

**Memory Issues**
- Close other applications
- Process files in smaller batches

### Debug Mode

Enable detailed logging by setting the log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please ensure:
- Code follows the existing modular architecture
- New features include appropriate error handling
- UI changes maintain the clean, professional aesthetic

## License

This tool is provided for research and educational purposes.

## Support

For issues or questions, please check the logs directory for detailed error messages or create an issue in the project repository.