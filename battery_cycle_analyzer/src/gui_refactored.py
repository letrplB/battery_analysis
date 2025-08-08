import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import logging
from typing import Optional, Dict, Any, List, Tuple
import plotly.graph_objects as go

# Import core modules
from core.data_models import (
    ProcessingParameters,
    AnalysisConfig,
    PreprocessedData,
    AnalysisResults
)
from core.data_loader import DataLoader
from core.preprocessor import DataPreprocessor
from analysis_modes.standard_cycle import StandardCycleAnalyzer

# Import existing modules for dQ/dU (we'll refactor these later)
import sys
sys.path.append(str(Path(__file__).parent))
from dqdu_analyzer import compute_dqdu_analysis


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize session state variables"""
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = None
    if 'preprocessed_data' not in st.session_state:
        st.session_state.preprocessed_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = None
    if 'c_rates' not in st.session_state:
        st.session_state.c_rates = [(1, 30, 0.333, 0.333)]


def render_sidebar():
    """Render sidebar with data input and preprocessing controls"""
    
    with st.sidebar:
        st.title("📊 Data Input & Preprocessing")
        
        # File upload section
        st.header("📁 Data Input")
        uploaded_file = st.file_uploader(
            "Upload Basytec data file",
            type=['txt', 'csv'],
            help="Upload your battery test data file"
        )
        
        if uploaded_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Load data if not already loaded
            if st.session_state.raw_data is None:
                with st.spinner("Loading file..."):
                    try:
                        loader = DataLoader()
                        st.session_state.raw_data = loader.load_file(tmp_path)
                        st.success(f"✅ File loaded: {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
                        return
            
            # Display file info
            if st.session_state.raw_data:
                raw_data = st.session_state.raw_data
                st.info(f"""
                **File Info:**
                - Size: {raw_data.metadata.file_size_kb:.1f} KB
                - Lines: {raw_data.metadata.total_lines:,}
                - Data rows: {len(raw_data.data):,}
                """)
        
        # Test plan upload (optional)
        st.header("📋 Test Plan (Optional)")
        test_plan_file = st.file_uploader(
            "Upload test plan file",
            type=['txt'],
            help="Optional: Upload test plan for C-rate configuration"
        )
        
        # Analysis parameters
        st.header("⚙️ Analysis Parameters")
        
        active_material = st.number_input(
            "Active material weight (g)",
            min_value=0.001,
            value=0.035,
            step=0.001,
            format="%.3f",
            help="Weight of active material in grams"
        )
        
        theoretical_capacity = st.number_input(
            "Theoretical capacity (Ah)",
            min_value=0.001,
            value=0.050,
            step=0.001,
            format="%.3f",
            help="Theoretical capacity in Ah"
        )
        
        # C-rate configuration
        st.subheader("🔋 C-Rate Configuration")
        
        # Simple mode for common cases
        use_custom_crates = st.checkbox("Use custom C-rates", value=False)
        
        if not use_custom_crates:
            # Simple uniform C-rate
            c_rate = st.number_input(
                "C-rate for all cycles",
                min_value=0.1,
                max_value=10.0,
                value=0.333,
                step=0.1,
                format="%.3f"
            )
            st.session_state.c_rates = [(1, 1000, c_rate, c_rate)]
        else:
            # Advanced C-rate configuration
            render_crate_configuration()
        
        # Boundary detection method
        st.subheader("🔍 Boundary Detection")
        boundary_method = st.selectbox(
            "Detection method",
            ["State-based", "Zero-crossing"],
            help="Method for detecting cycle boundaries"
        )
        
        # Baseline cycle for retention
        baseline_cycle = st.number_input(
            "Baseline cycle for retention",
            min_value=1,
            value=30,
            help="Cycle number to use as 100% retention baseline"
        )
        
        # Preprocessing button
        st.markdown("---")
        
        if st.button(
            "🚀 Prepare Data",
            type="primary",
            disabled=(st.session_state.raw_data is None),
            use_container_width=True
        ):
            if st.session_state.raw_data:
                with st.spinner("Preprocessing data..."):
                    try:
                        # Create parameters
                        params = ProcessingParameters(
                            active_material_weight=active_material,
                            theoretical_capacity=theoretical_capacity,
                            c_rates=st.session_state.c_rates,
                            boundary_method=boundary_method,
                            baseline_cycle=baseline_cycle
                        )
                        
                        # Run preprocessing
                        preprocessor = DataPreprocessor()
                        st.session_state.preprocessed_data = preprocessor.preprocess(
                            st.session_state.raw_data,
                            params
                        )
                        
                        # Show results
                        prep_data = st.session_state.preprocessed_data
                        st.success(f"✅ Data prepared: {len(prep_data.cycle_boundaries)} cycles detected")
                        
                        # Show warnings if any
                        if prep_data.validation_warnings:
                            with st.expander("⚠️ Validation Warnings"):
                                for warning in prep_data.validation_warnings:
                                    st.warning(warning)
                                    
                    except Exception as e:
                        st.error(f"Preprocessing failed: {str(e)}")
        
        # Show preprocessing status
        if st.session_state.preprocessed_data:
            st.success("✅ Data ready for analysis")
        elif st.session_state.raw_data:
            st.info("ℹ️ Click 'Prepare Data' to continue")


def render_crate_configuration():
    """Render C-rate configuration interface"""
    
    st.write("Define C-rate periods:")
    
    # Add new period button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Period"):
            st.session_state.c_rates.append((1, 30, 0.333, 0.333))
    with col2:
        if st.button("🔄 Reset to Default"):
            st.session_state.c_rates = [(1, 30, 0.333, 0.333)]
    
    # Display current periods
    updated_rates = []
    for i, (start, end, charge, discharge) in enumerate(st.session_state.c_rates):
        with st.expander(f"Period {i+1}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                new_start = st.number_input(
                    "Start cycle",
                    min_value=1,
                    value=start,
                    key=f"start_{i}"
                )
                new_charge = st.number_input(
                    "Charge C-rate",
                    min_value=0.1,
                    max_value=10.0,
                    value=charge,
                    step=0.1,
                    format="%.3f",
                    key=f"charge_{i}"
                )
            with col2:
                new_end = st.number_input(
                    "End cycle",
                    min_value=1,
                    value=end,
                    key=f"end_{i}"
                )
                new_discharge = st.number_input(
                    "Discharge C-rate",
                    min_value=0.1,
                    max_value=10.0,
                    value=discharge,
                    step=0.1,
                    format="%.3f",
                    key=f"discharge_{i}"
                )
            
            if st.button(f"❌ Remove", key=f"remove_{i}"):
                continue
            
            updated_rates.append((new_start, new_end, new_charge, new_discharge))
    
    st.session_state.c_rates = updated_rates


def render_main_panel():
    """Render main panel with analysis mode selection and results"""
    
    st.title("🔋 Battery Cycle Analyzer")
    
    # Check if data is preprocessed
    if st.session_state.preprocessed_data is None:
        st.info("""
        👈 **Getting Started:**
        1. Upload your battery test file in the sidebar
        2. Configure analysis parameters
        3. Click "Prepare Data" to preprocess
        """)
        return
    
    # Show preprocessed data summary
    prep_data = st.session_state.preprocessed_data
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cycles", len(prep_data.cycle_boundaries))
    with col2:
        if prep_data.cycle_metadata is not None and not prep_data.cycle_metadata.empty:
            avg_capacity = prep_data.cycle_metadata['Specific_Discharge_mAhg'].mean()
            st.metric("Avg Capacity", f"{avg_capacity:.1f} mAh/g")
    with col3:
        st.metric("Data Points", len(prep_data.raw_data.data))
    
    st.markdown("---")
    
    # Analysis mode selection
    st.header("🔬 Analysis Mode")
    
    tabs = st.tabs(["📊 Standard Cycle", "📈 dQ/dU Analysis", "🔄 Combined"])
    
    with tabs[0]:
        render_standard_analysis()
    
    with tabs[1]:
        render_dqdu_analysis()
    
    with tabs[2]:
        render_combined_analysis()


def render_standard_analysis():
    """Render standard cycle analysis interface"""
    
    st.subheader("Standard Cycle Analysis")
    
    # Analysis configuration
    with st.expander("⚙️ Analysis Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            plot_capacity = st.checkbox("Capacity vs Cycle", value=True)
            plot_retention = st.checkbox("Retention vs Cycle", value=True)
        
        with col2:
            plot_efficiency = st.checkbox("Efficiency vs Cycle", value=True)
            plot_voltage = st.checkbox("Voltage Range vs Cycle", value=True)
    
    # Collect selected plots
    plot_types = []
    if plot_capacity: plot_types.append('capacity_vs_cycle')
    if plot_retention: plot_types.append('retention_vs_cycle')
    if plot_efficiency: plot_types.append('efficiency_vs_cycle')
    if plot_voltage: plot_types.append('voltage_range_vs_cycle')
    
    # Run analysis button
    if st.button("▶️ Run Standard Analysis", type="primary", use_container_width=True):
        with st.spinner("Running analysis..."):
            try:
                # Create config
                config = AnalysisConfig(
                    mode="standard",
                    plot_types=plot_types
                )
                
                # Run analysis
                analyzer = StandardCycleAnalyzer()
                results = analyzer.analyze(st.session_state.preprocessed_data, config)
                
                # Store results
                st.session_state.analysis_results = results
                st.session_state.analysis_mode = "standard"
                
                st.success("✅ Analysis complete!")
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
    
    # Display results if available
    if st.session_state.analysis_results and st.session_state.analysis_mode == "standard":
        display_standard_results(st.session_state.analysis_results)


def render_dqdu_analysis():
    """Render dQ/dU analysis interface"""
    
    st.subheader("Differential Capacity (dQ/dU) Analysis")
    
    # Get available cycles
    if st.session_state.preprocessed_data:
        max_cycles = len(st.session_state.preprocessed_data.cycle_boundaries)
    else:
        max_cycles = 100
    
    # Analysis configuration
    with st.expander("⚙️ dQ/dU Settings", expanded=True):
        
        # Cycle selection
        st.write("**Select Cycles for Analysis:**")
        col1, col2, col3 = st.columns(3)
        
        selected_cycles = []
        with col1:
            if st.checkbox(f"Cycle 1 (charge)", value=True, key="dq_c1_charge"):
                selected_cycles.append(('1', 'charge'))
            if st.checkbox(f"Cycle 1 (discharge)", value=False, key="dq_c1_discharge"):
                selected_cycles.append(('1', 'discharge'))
        
        with col2:
            cycle_2 = st.number_input("Cycle 2", min_value=2, max_value=max_cycles, value=min(2, max_cycles))
            if st.checkbox(f"Cycle {cycle_2} (charge)", value=False, key="dq_c2_charge"):
                selected_cycles.append((str(cycle_2), 'charge'))
            if st.checkbox(f"Cycle {cycle_2} (discharge)", value=True, key="dq_c2_discharge"):
                selected_cycles.append((str(cycle_2), 'discharge'))
        
        with col3:
            cycle_3 = st.number_input("Cycle 3", min_value=3, max_value=max_cycles, value=min(3, max_cycles))
            if st.checkbox(f"Cycle {cycle_3} (charge)", value=False, key="dq_c3_charge"):
                selected_cycles.append((str(cycle_3), 'charge'))
            if st.checkbox(f"Cycle {cycle_3} (discharge)", value=False, key="dq_c3_discharge"):
                selected_cycles.append((str(cycle_3), 'discharge'))
        
        st.markdown("---")
        
        # Voltage filtering
        use_voltage_filter = st.checkbox("Apply voltage range filter", value=False)
        voltage_range = (2.5, 4.2)
        if use_voltage_filter:
            voltage_range = st.slider(
                "Voltage range (V)",
                min_value=0.0,
                max_value=5.0,
                value=(2.5, 4.2),
                step=0.1
            )
        
        # Smoothing
        col1, col2 = st.columns(2)
        with col1:
            smoothing_method = st.selectbox(
                "Smoothing method",
                ["None", "Moving Average", "Savitzky-Golay"],
                index=0
            )
        
        with col2:
            if smoothing_method != "None":
                window_size = st.number_input(
                    "Window size",
                    min_value=3,
                    max_value=51,
                    value=5,
                    step=2
                )
            else:
                window_size = 5
        
        # Peak detection
        enable_peak_detection = st.checkbox("Enable peak detection", value=False)
        if enable_peak_detection:
            peak_prominence = st.slider(
                "Peak prominence",
                min_value=0.01,
                max_value=1.0,
                value=0.1,
                step=0.01
            )
        else:
            peak_prominence = 0.1
        
        # Interpolation
        interpolation_points = st.number_input(
            "Interpolation points",
            min_value=100,
            max_value=1000,
            value=333,
            help="Number of points for interpolation"
        )
    
    # Run analysis button
    if st.button("▶️ Run dQ/dU Analysis", type="primary", use_container_width=True):
        if not selected_cycles:
            st.error("Please select at least one cycle for analysis")
        else:
            with st.spinner("Running dQ/dU analysis..."):
                try:
                    # Prepare cycle list
                    cycles_to_analyze = []
                    for cycle_str, phase in selected_cycles:
                        cycles_to_analyze.append({
                            'cycle': int(cycle_str),
                            'phase': phase
                        })
                    
                    # Run dQ/dU analysis using existing function
                    # (We'll refactor this to use the new structure later)
                    dqdu_results = compute_dqdu_analysis(
                        st.session_state.preprocessed_data.raw_data.data,
                        cycles_to_analyze,
                        st.session_state.preprocessed_data.parameters.active_material_weight,
                        voltage_filter=use_voltage_filter,
                        voltage_range=voltage_range if use_voltage_filter else None,
                        smoothing_method=smoothing_method.lower().replace(' ', '_'),
                        smoothing_window=window_size,
                        peak_detection=enable_peak_detection,
                        peak_prominence=peak_prominence,
                        interpolation_points=interpolation_points
                    )
                    
                    # Create results object
                    results = AnalysisResults(
                        mode="dqdu",
                        dqdu_data=dqdu_results.get('dqdu_data'),
                        peak_data=dqdu_results.get('peak_data'),
                        plots={'dqdu_plot': dqdu_results.get('plot')},
                        export_data=dqdu_results.get('export_data')
                    )
                    
                    st.session_state.analysis_results = results
                    st.session_state.analysis_mode = "dqdu"
                    
                    st.success("✅ dQ/dU analysis complete!")
                    
                except Exception as e:
                    st.error(f"dQ/dU analysis failed: {str(e)}")
    
    # Display results if available
    if st.session_state.analysis_results and st.session_state.analysis_mode == "dqdu":
        display_dqdu_results(st.session_state.analysis_results)


def render_combined_analysis():
    """Render combined analysis interface"""
    
    st.subheader("Combined Analysis")
    st.info("Run both standard cycle and dQ/dU analysis together")
    
    # This would combine settings from both analyses
    # For now, we'll keep it simple
    if st.button("▶️ Run Combined Analysis", type="primary", use_container_width=True):
        st.info("Combined analysis will run both standard and dQ/dU analyses with default settings")
        # Implementation would go here


def display_standard_results(results: AnalysisResults):
    """Display standard analysis results"""
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Summary statistics
    if results.summary_stats:
        st.subheader("Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Cycles",
                results.summary_stats.get('total_cycles', 0)
            )
        
        with col2:
            st.metric(
                "Avg Capacity",
                f"{results.summary_stats.get('avg_discharge_capacity_mAhg', 0):.1f} mAh/g"
            )
        
        with col3:
            st.metric(
                "Final Retention",
                f"{results.summary_stats.get('final_retention_%', 0):.1f}%"
            )
        
        with col4:
            st.metric(
                "Avg Efficiency",
                f"{results.summary_stats.get('avg_efficiency_%', 0):.1f}%"
            )
    
    # Plots
    if results.plots:
        st.subheader("Visualizations")
        
        for plot_name, fig in results.plots.items():
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    # Cycle data table
    if results.cycle_data is not None and not results.cycle_data.empty:
        st.subheader("Cycle Data")
        
        # Format the dataframe for display
        display_df = results.cycle_data[
            ['Cycle', 'Specific_Discharge_mAhg', 'Specific_Charge_mAhg', 
             'Efficiency_%', 'Retention_%', 'Voltage_Min', 'Voltage_Max']
        ].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
    
    # Export option
    if results.export_data is not None:
        st.subheader("Export Data")
        
        csv = results.export_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="battery_analysis_results.csv",
            mime="text/csv",
            use_container_width=True
        )


def display_dqdu_results(results: AnalysisResults):
    """Display dQ/dU analysis results"""
    
    st.markdown("---")
    st.header("📈 dQ/dU Analysis Results")
    
    # Plot
    if results.plots and 'dqdu_plot' in results.plots:
        st.plotly_chart(results.plots['dqdu_plot'], use_container_width=True)
    
    # Peak data
    if results.peak_data is not None and not results.peak_data.empty:
        st.subheader("Detected Peaks")
        st.dataframe(results.peak_data, use_container_width=True)
    
    # Export option
    if results.export_data is not None:
        st.subheader("Export Data")
        
        csv = results.export_data.to_csv(index=False)
        st.download_button(
            label="📥 Download dQ/dU Results (CSV)",
            data=csv,
            file_name="dqdu_analysis_results.csv",
            mime="text/csv",
            use_container_width=True
        )


def main():
    """Main application entry point"""
    
    st.set_page_config(
        page_title="Battery Cycle Analyzer",
        page_icon="🔋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_sidebar()
    render_main_panel()


if __name__ == "__main__":
    main()