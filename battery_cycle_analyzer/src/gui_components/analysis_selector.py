import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
import logging

from core.data_models import (
    PreprocessedData,
    AnalysisConfig,
    AnalysisResults
)
from analysis_modes.standard_cycle import StandardCycleAnalyzer

# Import existing dQ/dU analyzer (to be refactored later)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from dqdu_analyzer import compute_dqdu_analysis

logger = logging.getLogger(__name__)


class AnalysisSelectorComponent:
    """Handles analysis mode selection and configuration"""
    
    @staticmethod
    def render(preprocessed_data: PreprocessedData) -> None:
        """Render analysis mode selection and configuration"""
        
        st.header("🔬 Analysis Mode")
        
        # Create tabs for different analysis modes
        tabs = st.tabs([
            "📊 Standard Cycle",
            "📈 dQ/dU Analysis", 
            "🔄 Combined"
        ])
        
        with tabs[0]:
            AnalysisSelectorComponent._render_standard_analysis(preprocessed_data)
        
        with tabs[1]:
            AnalysisSelectorComponent._render_dqdu_analysis(preprocessed_data)
        
        with tabs[2]:
            AnalysisSelectorComponent._render_combined_analysis(preprocessed_data)
    
    @staticmethod
    def _render_standard_analysis(preprocessed_data: PreprocessedData) -> None:
        """Render standard cycle analysis configuration"""
        
        st.subheader("Standard Cycle Analysis")
        st.write("Analyze capacity, retention, and efficiency trends over cycles")
        
        # Configuration
        with st.expander("⚙️ Analysis Settings", expanded=True):
            st.write("**Select plots to generate:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                plot_capacity = st.checkbox(
                    "Capacity vs Cycle",
                    value=True,
                    help="Show discharge and charge capacity trends"
                )
                plot_retention = st.checkbox(
                    "Retention vs Cycle",
                    value=True,
                    help="Show capacity retention relative to baseline"
                )
            
            with col2:
                plot_efficiency = st.checkbox(
                    "Efficiency vs Cycle",
                    value=True,
                    help="Show coulombic efficiency trends"
                )
                plot_voltage = st.checkbox(
                    "Voltage Range vs Cycle",
                    value=True,
                    help="Show voltage window evolution"
                )
            
            # Additional options
            st.markdown("---")
            show_table = st.checkbox(
                "Show detailed cycle table",
                value=True,
                help="Display full cycle-by-cycle data"
            )
        
        # Prepare config
        plot_types = []
        if plot_capacity: plot_types.append('capacity_vs_cycle')
        if plot_retention: plot_types.append('retention_vs_cycle')
        if plot_efficiency: plot_types.append('efficiency_vs_cycle')
        if plot_voltage: plot_types.append('voltage_range_vs_cycle')
        
        # Run button
        if st.button(
            "▶️ Run Standard Analysis",
            type="primary",
            use_container_width=True,
            key="run_standard"
        ):
            with st.spinner("Running standard cycle analysis..."):
                try:
                    config = AnalysisConfig(
                        mode="standard",
                        plot_types=plot_types
                    )
                    
                    analyzer = StandardCycleAnalyzer()
                    results = analyzer.analyze(preprocessed_data, config)
                    
                    # Store results
                    st.session_state.analysis_results = results
                    st.session_state.analysis_mode = "standard"
                    st.session_state.show_cycle_table = show_table
                    
                    st.success("✅ Standard analysis complete!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    logger.exception("Standard analysis error")
    
    @staticmethod
    def _render_dqdu_analysis(preprocessed_data: PreprocessedData) -> None:
        """Render dQ/dU analysis configuration"""
        
        st.subheader("Differential Capacity (dQ/dU) Analysis")
        st.write("Analyze battery degradation mechanisms through differential capacity")
        
        # Get max cycles
        max_cycles = len(preprocessed_data.cycle_boundaries)
        
        with st.expander("⚙️ dQ/dU Settings", expanded=True):
            
            # Cycle selection
            st.write("**Select Cycles for Analysis:**")
            
            col1, col2, col3 = st.columns(3)
            
            selected_cycles = []
            
            with col1:
                st.write("**Cycle 1**")
                c1_charge = st.checkbox("Charge", value=True, key="dq_c1_ch")
                c1_discharge = st.checkbox("Discharge", value=False, key="dq_c1_dis")
                if c1_charge:
                    selected_cycles.append({'cycle': 1, 'phase': 'charge'})
                if c1_discharge:
                    selected_cycles.append({'cycle': 1, 'phase': 'discharge'})
            
            with col2:
                cycle_2 = st.number_input(
                    "**Cycle 2**",
                    min_value=2,
                    max_value=max_cycles,
                    value=min(2, max_cycles),
                    key="dq_cycle_2"
                )
                c2_charge = st.checkbox("Charge", value=False, key="dq_c2_ch")
                c2_discharge = st.checkbox("Discharge", value=True, key="dq_c2_dis")
                if c2_charge:
                    selected_cycles.append({'cycle': cycle_2, 'phase': 'charge'})
                if c2_discharge:
                    selected_cycles.append({'cycle': cycle_2, 'phase': 'discharge'})
            
            with col3:
                cycle_3 = st.number_input(
                    "**Cycle 3**",
                    min_value=3,
                    max_value=max_cycles,
                    value=min(3, max_cycles),
                    key="dq_cycle_3"
                )
                c3_charge = st.checkbox("Charge", value=False, key="dq_c3_ch")
                c3_discharge = st.checkbox("Discharge", value=False, key="dq_c3_dis")
                if c3_charge:
                    selected_cycles.append({'cycle': cycle_3, 'phase': 'charge'})
                if c3_discharge:
                    selected_cycles.append({'cycle': cycle_3, 'phase': 'discharge'})
            
            st.markdown("---")
            
            # Advanced settings
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Voltage Filtering:**")
                use_voltage_filter = st.checkbox(
                    "Apply voltage range filter",
                    value=False,
                    key="dq_voltage_filter"
                )
                
                if use_voltage_filter:
                    voltage_range = st.slider(
                        "Voltage range (V)",
                        min_value=0.0,
                        max_value=5.0,
                        value=(2.5, 4.2),
                        step=0.1,
                        key="dq_voltage_range"
                    )
                else:
                    voltage_range = None
                
                st.write("**Smoothing:**")
                smoothing_method = st.selectbox(
                    "Method",
                    ["None", "Moving Average", "Savitzky-Golay"],
                    key="dq_smoothing"
                )
                
                if smoothing_method != "None":
                    window_size = st.number_input(
                        "Window size",
                        min_value=3,
                        max_value=51,
                        value=5,
                        step=2,
                        key="dq_window"
                    )
                else:
                    window_size = 5
            
            with col2:
                st.write("**Peak Detection:**")
                enable_peaks = st.checkbox(
                    "Enable peak detection",
                    value=False,
                    key="dq_peaks"
                )
                
                if enable_peaks:
                    peak_prominence = st.slider(
                        "Peak prominence",
                        min_value=0.01,
                        max_value=1.0,
                        value=0.1,
                        step=0.01,
                        key="dq_prominence"
                    )
                else:
                    peak_prominence = 0.1
                
                st.write("**Interpolation:**")
                interp_points = st.number_input(
                    "Points",
                    min_value=100,
                    max_value=1000,
                    value=333,
                    step=50,
                    key="dq_interp",
                    help="Number of interpolation points"
                )
        
        # Run button
        if st.button(
            "▶️ Run dQ/dU Analysis",
            type="primary",
            use_container_width=True,
            key="run_dqdu"
        ):
            if not selected_cycles:
                st.error("Please select at least one cycle for analysis")
            else:
                with st.spinner("Running dQ/dU analysis..."):
                    try:
                        # Run analysis
                        dqdu_results = compute_dqdu_analysis(
                            preprocessed_data.raw_data.data,
                            selected_cycles,
                            preprocessed_data.parameters.active_material_weight,
                            voltage_filter=use_voltage_filter,
                            voltage_range=voltage_range,
                            smoothing_method=smoothing_method.lower().replace(' ', '_'),
                            smoothing_window=window_size,
                            peak_detection=enable_peaks,
                            peak_prominence=peak_prominence,
                            interpolation_points=interp_points
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
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"dQ/dU analysis failed: {str(e)}")
                        logger.exception("dQ/dU analysis error")
    
    @staticmethod
    def _render_combined_analysis(preprocessed_data: PreprocessedData) -> None:
        """Render combined analysis configuration"""
        
        st.subheader("Combined Analysis")
        st.info(
            "Run both standard cycle and dQ/dU analyses with optimized settings. "
            "This provides a comprehensive view of battery performance and degradation."
        )
        
        with st.expander("ℹ️ What will be analyzed", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Standard Cycle Analysis:**")
                st.write("- Capacity trends")
                st.write("- Retention analysis")
                st.write("- Efficiency tracking")
                st.write("- Voltage evolution")
            
            with col2:
                st.write("**dQ/dU Analysis:**")
                st.write("- Cycles 1, 2, and 3")
                st.write("- Both charge and discharge")
                st.write("- Peak detection enabled")
                st.write("- Optimized smoothing")
        
        if st.button(
            "▶️ Run Combined Analysis",
            type="primary",
            use_container_width=True,
            key="run_combined"
        ):
            st.info("Combined analysis will be implemented in the next iteration")
            # TODO: Implement combined analysis