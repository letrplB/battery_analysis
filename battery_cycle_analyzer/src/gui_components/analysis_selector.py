import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
import logging

from core.data_models import (
    PreprocessedData,
    AnalysisConfig,
    AnalysisResults
)
from analysis_modes.standard_cycle import StandardCycleAnalyzer

from analysis_modes.dqdu_analysis import compute_dqdu_analysis
import plotly.graph_objects as go
import pandas as pd

logger = logging.getLogger(__name__)


class AnalysisSelectorComponent:
    """Handles analysis mode selection and configuration"""
    
    @staticmethod
    def render(preprocessed_data: PreprocessedData) -> None:
        """Render analysis mode selection and configuration"""
        
        # Header with chart icon
        st.markdown("""
        <h2 style="display: flex; align-items: center;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.5rem;">
                <line x1="12" y1="20" x2="12" y2="10"></line>
                <line x1="18" y1="20" x2="18" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="16"></line>
            </svg>
            Analysis Mode
        </h2>
        """, unsafe_allow_html=True)
        
        # Create tabs for different analysis modes
        tabs = st.tabs([
            "Standard Cycle",
            "dQ/dU Analysis"
        ])
        
        with tabs[0]:
            AnalysisSelectorComponent._render_standard_analysis(preprocessed_data)
        
        with tabs[1]:
            AnalysisSelectorComponent._render_dqdu_analysis(preprocessed_data)
    
    @staticmethod
    def _render_standard_analysis(preprocessed_data: PreprocessedData) -> None:
        """Render standard cycle analysis configuration"""
        
        st.subheader("Standard Cycle Analysis")
        st.write("Analyze capacity, retention, and efficiency trends over cycles")
        
        # Configuration
        with st.expander("Analysis Settings", expanded=True):
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
            "Run Standard Analysis",
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
                    
                    st.success("Standard analysis complete!")
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
        
        with st.expander("dQ/dU Settings", expanded=True):
            
            # Cycle selection with dynamic addition
            st.write("**Select Cycles for Analysis:**")
            st.caption("Tip: Skip cycles 1-2 if they contain SEI formation")
            
            # Initialize session state for selected cycles if not exists
            if 'dqdu_selected_cycles' not in st.session_state:
                st.session_state.dqdu_selected_cycles = []
            
            # Add cycle interface
            st.write("**Add cycles to analyze:**")
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                new_cycle = st.number_input(
                    "Cycle number",
                    min_value=1,
                    max_value=max_cycles,
                    value=3,  # Default to cycle 3 (after SEI)
                    key="dq_new_cycle"
                )
            
            with col2:
                add_charge = st.checkbox("Charge", value=True, key="dq_add_charge")
            
            with col3:
                add_discharge = st.checkbox("Discharge", value=True, key="dq_add_discharge")
            
            with col4:
                if st.button("Add", key="dq_add_btn", type="secondary"):
                    if add_charge:
                        cycle_entry = {'cycle': new_cycle, 'phase': 'charge'}
                        if cycle_entry not in st.session_state.dqdu_selected_cycles:
                            st.session_state.dqdu_selected_cycles.append(cycle_entry)
                    if add_discharge:
                        cycle_entry = {'cycle': new_cycle, 'phase': 'discharge'}
                        if cycle_entry not in st.session_state.dqdu_selected_cycles:
                            st.session_state.dqdu_selected_cycles.append(cycle_entry)
                    st.rerun()
            
            # Display selected cycles
            if st.session_state.dqdu_selected_cycles:
                st.write("**Selected cycles:**")
                
                # Sort and display selected cycles
                sorted_cycles = sorted(st.session_state.dqdu_selected_cycles, 
                                     key=lambda x: (x['cycle'], x['phase']))
                
                # Display in a clean format
                for idx, cycle_info in enumerate(sorted_cycles):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• Cycle {cycle_info['cycle']} - {cycle_info['phase'].capitalize()}")
                    with col2:
                        if st.button("Remove", key=f"remove_dq_{idx}", type="secondary"):
                            st.session_state.dqdu_selected_cycles.remove(cycle_info)
                            st.rerun()
            else:
                st.info("No cycles selected yet. Add cycles using the form above.")
            
            selected_cycles = st.session_state.dqdu_selected_cycles
            
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
            "Run dQ/dU Analysis",
            type="primary",
            use_container_width=True,
            key="run_dqdu"
        ):
            if not selected_cycles:
                st.error("Please select at least one cycle for analysis")
            else:
                with st.spinner("Running dQ/dU analysis..."):
                    try:
                        # Prepare cycle selections (list of tuples)
                        cycle_selections = [
                            (cycle['cycle'], cycle['phase']) 
                            for cycle in selected_cycles
                        ]
                        
                        # Prepare parameters dictionary
                        params = {
                            'n_points': interp_points,
                            'voltage_range': voltage_range if use_voltage_filter else None,
                            'smoothing': {
                                'method': smoothing_method.lower(),
                                'window_size': window_size
                            },
                            'peak_detection': enable_peaks,
                            'peak_prominence': peak_prominence
                        }
                        
                        # Run analysis - pass cycle boundaries from preprocessing
                        dqdu_results = compute_dqdu_analysis(
                            preprocessed_data.raw_data.data,
                            cycle_selections,
                            params,
                            cycle_boundaries=preprocessed_data.cycle_boundaries
                        )
                        
                        # Create plot from results
                        dqdu_plot = AnalysisSelectorComponent._create_dqdu_plot(dqdu_results)
                        
                        # Prepare data for export in wide format
                        # Format: |Cycle X Charge U[V]|Cycle X Charge dQ/dU|Cycle X Discharge U[V]|...
                        dqdu_wide_data = {}
                        peak_data_list = []

                        for key, data in dqdu_results.items():
                            if 'error' not in data:
                                cycle_num = data['metadata']['cycle_number']
                                phase = data['metadata']['half_cycle_type'].capitalize()

                                # Create column names for this cycle/phase
                                col_prefix = f"Cycle {cycle_num} {phase}"
                                u_col = f"{col_prefix} U[V]"
                                dq_col = f"{col_prefix} dQ/dU"

                                dqdu_wide_data[u_col] = data['voltage']
                                dqdu_wide_data[dq_col] = data['dq_du']

                                # Add peak data if available
                                if data.get('peaks') and data['peaks']['peak_indices']:
                                    for v, i, p in zip(
                                        data['peaks']['peak_voltages'],
                                        data['peaks']['peak_intensities'],
                                        data['peaks']['prominences']
                                    ):
                                        peak_data_list.append({
                                            'Cycle': cycle_num,
                                            'Phase': phase,
                                            'Peak_Voltage_V': v,
                                            'Peak_Intensity': i,
                                            'Prominence': p
                                        })

                        # Create wide format DataFrame
                        # Sort columns by cycle number and phase (charge before discharge)
                        if dqdu_wide_data:
                            dqdu_df = pd.DataFrame(dqdu_wide_data)
                            # Reorder columns: group by cycle, then charge U, charge dQ, discharge U, discharge dQ
                            sorted_cols = sorted(dqdu_df.columns, key=lambda x: (
                                int(x.split()[1]),  # Cycle number
                                0 if 'Charge' in x else 1,  # Charge before Discharge
                                0 if 'U[V]' in x else 1  # U before dQ/dU
                            ))
                            dqdu_df = dqdu_df[sorted_cols]
                        else:
                            dqdu_df = None

                        peak_df = pd.DataFrame(peak_data_list) if peak_data_list else None
                        
                        # Create results object
                        results = AnalysisResults(
                            mode="dqdu",
                            dqdu_data=dqdu_df,
                            peak_data=peak_df,
                            plots={'dqdu_plot': dqdu_plot},
                            export_data=dqdu_df
                        )
                        
                        st.session_state.analysis_results = results
                        st.session_state.analysis_mode = "dqdu"
                        
                        st.success("dQ/dU analysis complete!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"dQ/dU analysis failed: {str(e)}")
                        logger.exception("dQ/dU analysis error")
    
    @staticmethod
    def _create_dqdu_plot(dqdu_results: Dict) -> go.Figure:
        """Create plotly figure from dQ/dU results"""
        
        fig = go.Figure()
        
        # Color palette for different cycles
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        color_idx = 0
        
        for key, data in dqdu_results.items():
            if 'error' not in data:
                cycle_num = data['metadata']['cycle_number']
                phase = data['metadata']['half_cycle_type']
                color = colors[color_idx % len(colors)]
                
                # Add main dQ/dU trace
                fig.add_trace(go.Scatter(
                    x=data['voltage'],
                    y=data['dq_du'],
                    mode='lines',
                    name=f"Cycle {cycle_num} ({phase})",
                    line=dict(color=color, width=2)
                ))
                
                # Add peaks if available
                if data.get('peaks') and data['peaks']['peak_indices']:
                    fig.add_trace(go.Scatter(
                        x=data['peaks']['peak_voltages'],
                        y=data['peaks']['peak_intensities'],
                        mode='markers',
                        name=f"Peaks C{cycle_num}",
                        marker=dict(
                            color=color,
                            size=10,
                            symbol='diamond',
                            line=dict(color='white', width=1)
                        ),
                        showlegend=False
                    ))
                
                color_idx += 1
        
        # Update layout
        fig.update_layout(
            title="Differential Capacity (dQ/dU) Analysis",
            xaxis_title="Voltage (V)",
            yaxis_title="dQ/dU (mAh/V)",
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            template="plotly_white"
        )
        
        return fig
