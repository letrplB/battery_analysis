# Battery Cycle Analyzer - dQ/dU Plot Integration Plan

## Executive Summary

This document outlines the integration plan for adding automated dQ/dU (differential capacity) plot generation capabilities to the existing Battery Cycle Analyzer. The dQ/dU plots are crucial for understanding battery degradation mechanisms and identifying phase transitions during charge/discharge cycles.

## Current State Analysis

### ✅ Already Implemented (Steps 1-6)
1. **Data Loading & Parsing**: Robust file loading with multiple encoding support
2. **Header & Metadata Extraction**: Automatic extraction of test parameters
3. **Data Organization**: Structured DataFrame with all required columns
4. **Cycle Detection**: State-based and zero-crossing boundary detection
5. **Capacity Calculation**: Trapezoidal integration for charge/discharge cycles
6. **RC Testing & Stability Analysis**: Complete cycle-by-cycle metrics

### 🔄 To Be Implemented (Steps 7+)
The manual process describes extracting specific half-cycles and generating dQ/dU plots through:
- Cycle selection and filtering
- Data interpolation/extrapolation
- Numerical differentiation
- Visualization with proper scaling

## dQ/dU Analysis Requirements

### Core Mathematical Operations
1. **Cycle Extraction**: Select specific half-cycles (charge/discharge) for analysis
2. **Data Interpolation**: Uniform sampling of voltage vs. capacity data (333 points recommended)
3. **Numerical Differentiation**: Calculate dQ/dV (inverse for dQ/dU plotting)
4. **Unit Conversion**: Scale from Ah to mAh for practical units

### Key Features Needed
- Multi-cycle selection (compare cycles at different stages)
- Voltage range filtering (focus on specific voltage windows)
- Smoothing options (reduce noise in derivative calculations)
- Peak detection (identify phase transitions automatically)
- Export capabilities (data and plots)

## Integration Architecture Options

### Option 1: Unified Analysis Pipeline (Recommended) ⭐
```
Data Loading → Base Analysis → Analysis Mode Selection → Output
                     ↓              ↓            ↓
              [Shared Processing]  Standard   dQ/dU
                                  Analysis   Analysis
```

**Advantages:**
- Single data loading and preprocessing step
- Shared cycle detection and filtering logic
- User selects analysis type after data processing
- Memory efficient for large files
- Consistent UI/UX experience

**Implementation:**
1. Extend `analyzer.py` with dQ/dU calculation functions
2. Add analysis mode selector in GUI
3. Create tabbed interface for different analysis types
4. Share common data structures

### Option 2: Parallel Analysis Modules
```
Data Loading → Fork → Standard Analysis → Results
              ↘     → dQ/dU Analysis   → dQ/dU Plots
```

**Advantages:**
- Independent module development
- Can run both analyses simultaneously
- Specialized optimization for each type

**Disadvantages:**
- Duplicate data processing
- Higher memory usage
- More complex UI

### Option 3: Sequential Analysis Pipeline
```
Standard Analysis → Complete → Optional dQ/dU → Enhanced Results
                              Analysis
```

**Advantages:**
- Builds on existing analysis results
- User can decide after seeing standard results
- Progressive enhancement approach

**Disadvantages:**
- Requires completing standard analysis first
- May need to reload/reprocess data

## Recommended Implementation Plan

### Phase 1: Core dQ/dU Functionality (Week 1)

#### 1.1 Create `dqdu_analyzer.py` Module
```python
def extract_cycle_data(df, cycle_number, half_cycle_type='discharge'):
    """Extract specific half-cycle data for dQ/dU analysis."""
    
def interpolate_voltage_capacity(voltage, capacity, n_points=333):
    """Interpolate V-Q data to uniform grid."""
    
def calculate_dq_du(voltage, capacity, smoothing=None):
    """Calculate differential capacity dQ/dU."""
    
def detect_peaks(dq_du, voltage, prominence=0.1):
    """Identify peaks in dQ/dU curve (phase transitions)."""
```

#### 1.2 Extend Data Structures
- Add cycle selection metadata
- Store interpolated data efficiently
- Cache dQ/dU calculations

### Phase 2: GUI Integration (Week 2)

#### 2.1 Add Analysis Mode Selector
```python
# In gui.py
analysis_mode = st.selectbox(
    "Analysis Mode",
    ["Standard Cycle Analysis", "dQ/dU Analysis", "Combined Analysis"]
)
```

#### 2.2 Create dQ/dU Configuration Panel
- Cycle selection (multi-select with comparison)
- Voltage range filter (min/max)
- Interpolation points (default: 333)
- Smoothing options (None, Savitzky-Golay, Moving Average)

#### 2.3 Implement Visualization Tab
- Interactive Plotly charts
- Multi-cycle overlay capability
- Peak annotation
- Export options

### Phase 3: Advanced Features (Week 3)

#### 3.1 Automated Peak Detection
- Implement peak finding algorithms
- Calculate peak positions and intensities
- Track peak evolution across cycles

#### 3.2 Batch Processing
- Process multiple cycles automatically
- Generate evolution plots (peak shift over cycles)
- Statistical analysis of dQ/dU features

#### 3.3 Export Enhancements
- Export interpolated data
- Save dQ/dU calculations
- Generate report with plots and peak tables

## Technical Implementation Details

### Data Processing Pipeline
```python
# Proposed workflow in analyzer.py
def compute_dqdu_analysis(df, cycle_selections, params):
    """
    Main dQ/dU analysis pipeline.
    
    Args:
        df: Main dataframe with battery data
        cycle_selections: List of (cycle_num, half_cycle_type) tuples
        params: Dictionary with analysis parameters
            - n_points: Interpolation points (default: 333)
            - voltage_range: (min, max) tuple or None
            - smoothing: Smoothing method and parameters
            - peak_detection: Enable/disable peak finding
    
    Returns:
        Dictionary with dQ/dU results for each selected cycle
    """
    results = {}
    
    for cycle_num, half_cycle_type in cycle_selections:
        # Extract cycle data
        cycle_data = extract_cycle_for_dqdu(df, cycle_num, half_cycle_type)
        
        # Apply voltage filtering if specified
        if params.get('voltage_range'):
            cycle_data = filter_voltage_range(cycle_data, params['voltage_range'])
        
        # Interpolate to uniform grid
        v_interp, q_interp = interpolate_vq_data(
            cycle_data['U[V]'], 
            cycle_data['Ah-Cyc-Discharge-0'],
            n_points=params.get('n_points', 333)
        )
        
        # Calculate dQ/dU
        dq_du = calculate_differential_capacity(v_interp, q_interp)
        
        # Apply smoothing if requested
        if params.get('smoothing'):
            dq_du = apply_smoothing(dq_du, params['smoothing'])
        
        # Detect peaks if enabled
        peaks = None
        if params.get('peak_detection'):
            peaks = find_dqdu_peaks(v_interp, dq_du)
        
        results[f"cycle_{cycle_num}_{half_cycle_type}"] = {
            'voltage': v_interp,
            'capacity': q_interp,
            'dq_du': dq_du,
            'peaks': peaks,
            'metadata': {
                'cycle_number': cycle_num,
                'half_cycle_type': half_cycle_type,
                'n_points': len(v_interp)
            }
        }
    
    return results
```

### GUI Integration Example
```python
# In gui.py - Add new tab for dQ/dU analysis
if analysis_mode in ["dQ/dU Analysis", "Combined Analysis"]:
    with st.expander("🔬 dQ/dU Analysis Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Cycle selection
            available_cycles = get_available_cycles(results_df)
            selected_cycles = st.multiselect(
                "Select cycles for dQ/dU analysis",
                available_cycles,
                default=available_cycles[:3] if len(available_cycles) >= 3 else available_cycles
            )
            
            # Half-cycle type
            half_cycle_type = st.radio(
                "Half-cycle type",
                ["discharge", "charge"],
                help="Select whether to analyze charge or discharge cycles"
            )
        
        with col2:
            # Advanced parameters
            n_points = st.slider(
                "Interpolation points",
                min_value=100,
                max_value=1000,
                value=333,
                step=10,
                help="Number of points for interpolation (higher = smoother)"
            )
            
            # Smoothing options
            smoothing_method = st.selectbox(
                "Smoothing method",
                ["None", "Savitzky-Golay", "Moving Average"],
                help="Apply smoothing to reduce noise in dQ/dU curves"
            )
            
            if smoothing_method == "Savitzky-Golay":
                window_length = st.slider("Window length", 5, 51, 11, step=2)
                poly_order = st.slider("Polynomial order", 1, 5, 3)
                smoothing_params = {"method": "savgol", "window": window_length, "poly": poly_order}
            elif smoothing_method == "Moving Average":
                window_size = st.slider("Window size", 3, 21, 5, step=2)
                smoothing_params = {"method": "moving_avg", "window": window_size}
            else:
                smoothing_params = None
            
            # Peak detection
            detect_peaks = st.checkbox("Enable peak detection", value=True)
            if detect_peaks:
                peak_prominence = st.slider(
                    "Peak prominence",
                    min_value=0.01,
                    max_value=1.0,
                    value=0.1,
                    step=0.01,
                    help="Minimum prominence for peak detection"
                )
```

## File Structure

```
battery_cycle_analyzer/
├── src/
│   ├── analyzer.py          # [Existing] Core analysis
│   ├── dqdu_analyzer.py     # [New] dQ/dU specific functions
│   ├── gui.py              # [Modified] Enhanced GUI with dQ/dU
│   └── visualization.py     # [New] Advanced plotting functions
├── tests/
│   ├── test_dqdu.py        # [New] dQ/dU unit tests
│   └── test_integration.py  # [New] Integration tests
└── examples/
    └── dqdu_examples.ipynb  # [New] Example notebooks
```

## Dependencies

### New Requirements
```python
# Add to requirements.txt
scipy>=1.10.0      # Already included - for interpolation and signal processing
numpy>=1.24.0      # Already included - for numerical operations
plotly>=5.15.0     # Already included - for interactive plots

# Optional for advanced features
scikit-learn>=1.0  # For advanced peak detection algorithms (optional)
```

## Testing Strategy

### Unit Tests
- Test interpolation accuracy
- Verify differentiation calculations
- Validate peak detection algorithms
- Check unit conversions

### Integration Tests
- End-to-end dQ/dU generation
- Multi-cycle comparison
- Large file handling
- Export functionality

### Validation Tests
- Compare with manual Origin calculations
- Verify against known battery chemistry patterns
- Cross-validate with literature dQ/dU curves

## Risk Mitigation

### Performance Concerns
- **Risk**: Large files with many cycles may be slow
- **Mitigation**: Implement lazy loading and caching strategies

### Numerical Stability
- **Risk**: Differentiation can amplify noise
- **Mitigation**: Implement multiple smoothing options and validation

### User Experience
- **Risk**: Complex interface may confuse users
- **Mitigation**: Progressive disclosure with sensible defaults

## Timeline

### Week 1: Core Implementation
- [ ] Create dqdu_analyzer.py module
- [ ] Implement basic dQ/dU calculations
- [ ] Add unit tests

### Week 2: GUI Integration
- [ ] Extend GUI with dQ/dU options
- [ ] Implement visualization
- [ ] Add export functionality

### Week 3: Advanced Features
- [ ] Peak detection algorithms
- [ ] Batch processing
- [ ] Documentation and examples

## Success Metrics

1. **Accuracy**: dQ/dU plots match manual Origin calculations within 5%
2. **Performance**: Process 1000 cycles in < 30 seconds
3. **Usability**: Users can generate dQ/dU plots in < 5 clicks
4. **Reliability**: Zero crashes on standard test files

## Conclusion

The recommended approach is **Option 1: Unified Analysis Pipeline**, which provides the best balance of:
- User experience (single workflow)
- Performance (shared data processing)
- Maintainability (integrated codebase)
- Flexibility (choose analysis type post-loading)

This implementation will transform the Battery Cycle Analyzer into a comprehensive battery analysis platform supporting both standard cycle analysis and advanced dQ/dU differential capacity analysis, significantly reducing the manual effort required in Origin software.