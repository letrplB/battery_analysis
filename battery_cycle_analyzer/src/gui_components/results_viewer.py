import streamlit as st
import pandas as pd
from typing import Optional
import logging

from core.data_models import AnalysisResults

logger = logging.getLogger(__name__)


class ResultsViewerComponent:
    """Handles display of analysis results"""
    
    @staticmethod
    def render(results: Optional[AnalysisResults], mode: Optional[str]) -> None:
        """Render analysis results based on mode"""
        
        if not results or not mode:
            return
        
        st.markdown("---")
        # Header with chart icon
        st.markdown("""
        <h2 style="display: flex; align-items: center;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.5rem;">
                <path d="M3 3v18h18"></path>
                <polyline points="9 18 15 12 21 18"></polyline>
            </svg>
            Analysis Results
        </h2>
        """, unsafe_allow_html=True)
        
        if mode == "standard":
            ResultsViewerComponent._render_standard_results(results)
        elif mode == "dqdu":
            ResultsViewerComponent._render_dqdu_results(results)
    
    @staticmethod
    def _render_standard_results(results: AnalysisResults, key_suffix: str = "") -> None:
        """Display standard cycle analysis results"""
        
        # Summary metrics
        if results.summary_stats:
            st.subheader("Summary Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Cycles",
                    f"{results.summary_stats.get('total_cycles', 0):,}"
                )
                st.metric(
                    "Test Duration",
                    f"{results.summary_stats.get('total_test_duration_h', 0):.1f} h"
                )
            
            with col2:
                avg_cap = results.summary_stats.get('avg_discharge_capacity_mAhg', 0)
                st.metric(
                    "Avg Capacity",
                    f"{avg_cap:.1f} mAh/g"
                )
                st.metric(
                    "Voltage Range",
                    f"{results.summary_stats.get('avg_voltage_range_V', 0):.2f} V"
                )
            
            with col3:
                retention = results.summary_stats.get('final_retention_%', 0)
                st.metric(
                    "Final Retention",
                    f"{retention:.1f}%",
                    delta=f"{retention - 100:.1f}%"
                )
                fade = results.summary_stats.get('capacity_fade_per_cycle_%', 0)
                st.metric(
                    "Fade/Cycle",
                    f"{fade:.3f}%"
                )
            
            with col4:
                efficiency = results.summary_stats.get('avg_efficiency_%', 0)
                st.metric(
                    "Avg Efficiency",
                    f"{efficiency:.1f}%"
                )
                # Calculate efficiency stability
                if results.cycle_data is not None and 'Efficiency_%' in results.cycle_data:
                    eff_std = results.cycle_data['Efficiency_%'].std()
                    st.metric(
                        "Efficiency σ",
                        f"±{eff_std:.2f}%"
                    )
        
        # Plots
        if results.plots:
            st.subheader("Visualizations")
            
            # Create tabs for different plots
            plot_names = list(results.plots.keys())
            plot_labels = {
                'capacity_vs_cycle': 'Capacity',
                'retention_vs_cycle': 'Retention',
                'efficiency_vs_cycle': 'Efficiency',
                'voltage_range_vs_cycle': 'Voltage'
            }
            
            tabs = st.tabs([plot_labels.get(name, name) for name in plot_names])
            
            for tab, (plot_name, fig) in zip(tabs, results.plots.items()):
                with tab:
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"{plot_name}{key_suffix}")
        
        # Cycle data table
        if st.session_state.get('show_cycle_table', True):
            if results.cycle_data is not None and not results.cycle_data.empty:
                st.subheader("Cycle Data Table")
                
                # Select columns to display
                display_columns = [
                    'Cycle',
                    'Specific_Discharge_mAhg',
                    'Specific_Charge_mAhg',
                    'Efficiency_%',
                    'Retention_%',
                    'Voltage_Min',
                    'Voltage_Max',
                    'Duration_h',
                    'C_Rate_Discharge',
                    'C_Rate_Charge'
                ]
                
                # Filter to existing columns
                available_columns = [col for col in display_columns if col in results.cycle_data.columns]
                display_df = results.cycle_data[available_columns].round(2)
                
                # Add formatting
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400,
                    column_config={
                        "Cycle": st.column_config.NumberColumn("Cycle", format="%d"),
                        "Specific_Discharge_mAhg": st.column_config.NumberColumn(
                            "Discharge (mAh/g)", format="%.1f"
                        ),
                        "Specific_Charge_mAhg": st.column_config.NumberColumn(
                            "Charge (mAh/g)", format="%.1f"
                        ),
                        "Efficiency_%": st.column_config.NumberColumn(
                            "Efficiency (%)", format="%.1f"
                        ),
                        "Retention_%": st.column_config.NumberColumn(
                            "Retention (%)", format="%.1f"
                        ),
                        "Voltage_Min": st.column_config.NumberColumn(
                            "V Min", format="%.3f"
                        ),
                        "Voltage_Max": st.column_config.NumberColumn(
                            "V Max", format="%.3f"
                        ),
                        "Duration_h": st.column_config.NumberColumn(
                            "Duration (h)", format="%.1f"
                        ),
                    }
                )
    
    @staticmethod
    def _render_dqdu_results(results: AnalysisResults, key_suffix: str = "") -> None:
        """Display dQ/dU analysis results"""
        
        # Display the dQ/dU plot
        if results.plots and 'dqdu_plot' in results.plots:
            st.subheader("dQ/dU Analysis Plot")
            st.plotly_chart(results.plots['dqdu_plot'], use_container_width=True, key=f"dqdu_plot{key_suffix}")
        
        # Peak detection results
        if results.peak_data is not None and not results.peak_data.empty:
            st.subheader("Detected Peaks")
            
            # Summary of peaks
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Peaks", len(results.peak_data))
            with col2:
                if 'voltage' in results.peak_data.columns:
                    avg_voltage = results.peak_data['voltage'].mean()
                    st.metric("Avg Peak Voltage", f"{avg_voltage:.3f} V")
            with col3:
                if 'prominence' in results.peak_data.columns:
                    max_prominence = results.peak_data['prominence'].max()
                    st.metric("Max Prominence", f"{max_prominence:.3f}")
            
            # Peak data table
            st.dataframe(
                results.peak_data.round(3),
                use_container_width=True,
                height=300
            )
        
        # dQ/dU data
        if results.dqdu_data is not None and not results.dqdu_data.empty:
            with st.expander("dQ/dU Data", expanded=False):
                st.dataframe(
                    results.dqdu_data.round(3),
                    use_container_width=True,
                    height=400
                )
