import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, List
import logging

from ..core.data_models import (
    PreprocessedData,
    AnalysisConfig,
    AnalysisResults
)


class StandardCycleAnalyzer:
    """Performs standard cycle analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze(
        self,
        preprocessed_data: PreprocessedData,
        config: AnalysisConfig
    ) -> AnalysisResults:
        """Run standard cycle analysis"""
        
        cycle_data = preprocessed_data.cycle_metadata.copy()
        
        if cycle_data.empty:
            return AnalysisResults(
                mode="standard",
                warnings=["No cycles found in data"]
            )
        
        # Calculate retention relative to baseline cycle
        baseline_cycle = preprocessed_data.parameters.baseline_cycle
        if baseline_cycle <= len(cycle_data):
            baseline_capacity = cycle_data.iloc[baseline_cycle - 1]['Specific_Discharge_mAhg']
            cycle_data['Retention_%'] = (
                cycle_data['Specific_Discharge_mAhg'] / baseline_capacity * 100
            )
        else:
            # Use first cycle as baseline
            baseline_capacity = cycle_data.iloc[0]['Specific_Discharge_mAhg']
            cycle_data['Retention_%'] = (
                cycle_data['Specific_Discharge_mAhg'] / baseline_capacity * 100
            )
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(cycle_data)
        
        # Generate plots based on config
        plots = self._generate_plots(cycle_data, config)
        
        # Prepare export data
        export_data = self._prepare_export_data(
            cycle_data,
            preprocessed_data.raw_data.metadata
        )
        
        return AnalysisResults(
            mode="standard",
            cycle_data=cycle_data,
            summary_stats=summary_stats,
            plots=plots,
            export_data=export_data,
            warnings=preprocessed_data.validation_warnings
        )
    
    def _calculate_summary_stats(self, cycle_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics"""
        
        return {
            'total_cycles': len(cycle_data),
            'avg_discharge_capacity_mAhg': cycle_data['Specific_Discharge_mAhg'].mean(),
            'avg_charge_capacity_mAhg': cycle_data['Specific_Charge_mAhg'].mean(),
            'avg_efficiency_%': cycle_data['Efficiency_%'].mean(),
            'final_retention_%': cycle_data['Retention_%'].iloc[-1] if 'Retention_%' in cycle_data else None,
            'capacity_fade_per_cycle_%': (
                (100 - cycle_data['Retention_%'].iloc[-1]) / len(cycle_data)
                if 'Retention_%' in cycle_data else None
            ),
            'avg_voltage_range_V': (
                cycle_data['Voltage_Max'].mean() - cycle_data['Voltage_Min'].mean()
            ),
            'total_test_duration_h': cycle_data['Duration_h'].sum()
        }
    
    def _generate_plots(
        self,
        cycle_data: pd.DataFrame,
        config: AnalysisConfig
    ) -> Dict[str, Any]:
        """Generate analysis plots"""
        
        plots = {}
        
        # Default plot types if not specified
        if not config.plot_types:
            config.plot_types = [
                'capacity_vs_cycle',
                'retention_vs_cycle',
                'efficiency_vs_cycle',
                'voltage_range_vs_cycle'
            ]
        
        if 'capacity_vs_cycle' in config.plot_types:
            plots['capacity_vs_cycle'] = self._plot_capacity_vs_cycle(cycle_data)
        
        if 'retention_vs_cycle' in config.plot_types and 'Retention_%' in cycle_data:
            plots['retention_vs_cycle'] = self._plot_retention_vs_cycle(cycle_data)
        
        if 'efficiency_vs_cycle' in config.plot_types:
            plots['efficiency_vs_cycle'] = self._plot_efficiency_vs_cycle(cycle_data)
        
        if 'voltage_range_vs_cycle' in config.plot_types:
            plots['voltage_range_vs_cycle'] = self._plot_voltage_range_vs_cycle(cycle_data)
        
        return plots
    
    def _plot_capacity_vs_cycle(self, cycle_data: pd.DataFrame) -> go.Figure:
        """Create capacity vs cycle plot"""
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=cycle_data['Cycle'],
            y=cycle_data['Specific_Discharge_mAhg'],
            mode='lines+markers',
            name='Discharge',
            line=dict(color='blue'),
            marker=dict(size=4)
        ))
        
        fig.add_trace(go.Scatter(
            x=cycle_data['Cycle'],
            y=cycle_data['Specific_Charge_mAhg'],
            mode='lines+markers',
            name='Charge',
            line=dict(color='red'),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title='Specific Capacity vs Cycle Number',
            xaxis_title='Cycle Number',
            yaxis_title='Specific Capacity (mAh/g)',
            hovermode='x unified',
            showlegend=True
        )
        
        return fig
    
    def _plot_retention_vs_cycle(self, cycle_data: pd.DataFrame) -> go.Figure:
        """Create retention vs cycle plot"""
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=cycle_data['Cycle'],
            y=cycle_data['Retention_%'],
            mode='lines+markers',
            name='Retention',
            line=dict(color='green'),
            marker=dict(size=4)
        ))
        
        # Add 80% retention line
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="red",
            annotation_text="80% Retention"
        )
        
        fig.update_layout(
            title='Capacity Retention vs Cycle Number',
            xaxis_title='Cycle Number',
            yaxis_title='Retention (%)',
            hovermode='x unified',
            yaxis=dict(range=[0, 105])
        )
        
        return fig
    
    def _plot_efficiency_vs_cycle(self, cycle_data: pd.DataFrame) -> go.Figure:
        """Create efficiency vs cycle plot"""
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=cycle_data['Cycle'],
            y=cycle_data['Efficiency_%'],
            mode='lines+markers',
            name='Coulombic Efficiency',
            line=dict(color='purple'),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title='Coulombic Efficiency vs Cycle Number',
            xaxis_title='Cycle Number',
            yaxis_title='Efficiency (%)',
            hovermode='x unified',
            yaxis=dict(range=[0, 105])
        )
        
        return fig
    
    def _plot_voltage_range_vs_cycle(self, cycle_data: pd.DataFrame) -> go.Figure:
        """Create voltage range vs cycle plot"""
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=cycle_data['Cycle'],
            y=cycle_data['Voltage_Max'],
            mode='lines',
            name='Max Voltage',
            line=dict(color='red'),
            fill=None
        ))
        
        fig.add_trace(go.Scatter(
            x=cycle_data['Cycle'],
            y=cycle_data['Voltage_Min'],
            mode='lines',
            name='Min Voltage',
            line=dict(color='blue'),
            fill='tonexty',
            fillcolor='rgba(0,100,200,0.2)'
        ))
        
        fig.update_layout(
            title='Voltage Range vs Cycle Number',
            xaxis_title='Cycle Number',
            yaxis_title='Voltage (V)',
            hovermode='x unified',
            showlegend=True
        )
        
        return fig
    
    def _prepare_export_data(
        self,
        cycle_data: pd.DataFrame,
        metadata: Any
    ) -> pd.DataFrame:
        """Prepare data for CSV export"""
        
        export_df = cycle_data.copy()
        
        # Add metadata as columns
        export_df['Test_Name'] = metadata.test_name
        export_df['Battery'] = metadata.battery_name
        export_df['Test_Start'] = metadata.test_start
        export_df['Test_End'] = metadata.test_end
        
        return export_df