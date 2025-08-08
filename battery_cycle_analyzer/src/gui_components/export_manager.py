import streamlit as st
import pandas as pd
from typing import Optional
import io
import logging

from ..core.data_models import AnalysisResults, PreprocessedData

logger = logging.getLogger(__name__)


class ExportManagerComponent:
    """Handles data export functionality"""
    
    @staticmethod
    def render(
        results: Optional[AnalysisResults],
        preprocessed_data: Optional[PreprocessedData],
        mode: Optional[str]
    ) -> None:
        """Render export options"""
        
        if not results:
            return
        
        st.markdown("---")
        st.subheader("💾 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export main results
            if results.export_data is not None:
                csv_data = results.export_data.to_csv(index=False)
                
                filename = f"battery_{mode}_results.csv"
                if mode == "standard":
                    label = "📥 Download Cycle Analysis"
                elif mode == "dqdu":
                    label = "📥 Download dQ/dU Results"
                else:
                    label = "📥 Download Results"
                
                st.download_button(
                    label=label,
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True,
                    help="Download analysis results as CSV"
                )
        
        with col2:
            # Export raw data (if requested)
            if st.checkbox("Include raw data", value=False, key="export_raw"):
                if preprocessed_data and preprocessed_data.raw_data:
                    raw_csv = preprocessed_data.raw_data.data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Raw Data",
                        data=raw_csv,
                        file_name="battery_raw_data.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download original data as CSV"
                    )
        
        with col3:
            # Export report
            if st.checkbox("Generate report", value=False, key="export_report"):
                report = ExportManagerComponent._generate_report(
                    results, preprocessed_data, mode
                )
                st.download_button(
                    label="📥 Download Report",
                    data=report,
                    file_name=f"battery_{mode}_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Download analysis report"
                )
        
        # Advanced export options
        with st.expander("🔧 Advanced Export Options", expanded=False):
            st.write("**Export Format:**")
            export_format = st.selectbox(
                "Select format",
                ["CSV", "Excel", "JSON"],
                key="export_format"
            )
            
            if export_format == "Excel":
                if results.export_data is not None:
                    excel_buffer = ExportManagerComponent._create_excel(
                        results, preprocessed_data, mode
                    )
                    st.download_button(
                        label="📥 Download Excel File",
                        data=excel_buffer,
                        file_name=f"battery_{mode}_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            elif export_format == "JSON":
                if results.export_data is not None:
                    json_data = results.export_data.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Download JSON File",
                        data=json_data,
                        file_name=f"battery_{mode}_results.json",
                        mime="application/json",
                        use_container_width=True
                    )
    
    @staticmethod
    def _generate_report(
        results: AnalysisResults,
        preprocessed_data: PreprocessedData,
        mode: str
    ) -> str:
        """Generate text report of analysis"""
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("BATTERY CYCLE ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Metadata
        if preprocessed_data and preprocessed_data.raw_data:
            metadata = preprocessed_data.raw_data.metadata
            report_lines.append("FILE INFORMATION:")
            report_lines.append(f"  File: {metadata.file_name}")
            report_lines.append(f"  Test: {metadata.test_name or 'N/A'}")
            report_lines.append(f"  Battery: {metadata.battery_name or 'N/A'}")
            report_lines.append(f"  Start: {metadata.test_start or 'N/A'}")
            report_lines.append(f"  End: {metadata.test_end or 'N/A'}")
            report_lines.append("")
        
        # Parameters
        if preprocessed_data:
            params = preprocessed_data.parameters
            report_lines.append("ANALYSIS PARAMETERS:")
            report_lines.append(f"  Active Material: {params.active_material_weight:.3f} g")
            report_lines.append(f"  Theoretical Capacity: {params.theoretical_capacity:.3f} Ah")
            report_lines.append(f"  Boundary Method: {params.boundary_method}")
            report_lines.append(f"  Baseline Cycle: {params.baseline_cycle}")
            report_lines.append("")
        
        # Results based on mode
        if mode == "standard" and results.summary_stats:
            report_lines.append("SUMMARY STATISTICS:")
            stats = results.summary_stats
            report_lines.append(f"  Total Cycles: {stats.get('total_cycles', 0)}")
            report_lines.append(f"  Avg Discharge Capacity: {stats.get('avg_discharge_capacity_mAhg', 0):.1f} mAh/g")
            report_lines.append(f"  Avg Charge Capacity: {stats.get('avg_charge_capacity_mAhg', 0):.1f} mAh/g")
            report_lines.append(f"  Avg Efficiency: {stats.get('avg_efficiency_%', 0):.1f}%")
            report_lines.append(f"  Final Retention: {stats.get('final_retention_%', 0):.1f}%")
            report_lines.append(f"  Capacity Fade/Cycle: {stats.get('capacity_fade_per_cycle_%', 0):.3f}%")
            report_lines.append(f"  Test Duration: {stats.get('total_test_duration_h', 0):.1f} hours")
            report_lines.append("")
        
        elif mode == "dqdu":
            report_lines.append("dQ/dU ANALYSIS RESULTS:")
            if results.peak_data is not None and not results.peak_data.empty:
                report_lines.append(f"  Peaks Detected: {len(results.peak_data)}")
                report_lines.append("")
                report_lines.append("  Peak Details:")
                for _, peak in results.peak_data.iterrows():
                    report_lines.append(f"    - Voltage: {peak.get('voltage', 0):.3f} V")
            else:
                report_lines.append("  No peaks detected")
            report_lines.append("")
        
        # Warnings
        if results.warnings:
            report_lines.append("WARNINGS:")
            for warning in results.warnings:
                report_lines.append(f"  - {warning}")
            report_lines.append("")
        
        report_lines.append("=" * 60)
        report_lines.append("End of Report")
        
        return "\n".join(report_lines)
    
    @staticmethod
    def _create_excel(
        results: AnalysisResults,
        preprocessed_data: PreprocessedData,
        mode: str
    ) -> bytes:
        """Create Excel file with multiple sheets"""
        
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Main results sheet
            if results.export_data is not None:
                results.export_data.to_excel(
                    writer,
                    sheet_name='Analysis Results',
                    index=False
                )
            
            # Cycle data sheet (for standard analysis)
            if mode == "standard" and results.cycle_data is not None:
                results.cycle_data.to_excel(
                    writer,
                    sheet_name='Cycle Data',
                    index=False
                )
            
            # dQ/dU data sheet
            if mode == "dqdu" and results.dqdu_data is not None:
                results.dqdu_data.to_excel(
                    writer,
                    sheet_name='dQdU Data',
                    index=False
                )
            
            # Peak data sheet
            if results.peak_data is not None and not results.peak_data.empty:
                results.peak_data.to_excel(
                    writer,
                    sheet_name='Peak Data',
                    index=False
                )
            
            # Metadata sheet
            if preprocessed_data:
                metadata_df = pd.DataFrame([{
                    'Parameter': 'Active Material (g)',
                    'Value': preprocessed_data.parameters.active_material_weight
                }, {
                    'Parameter': 'Theoretical Capacity (Ah)',
                    'Value': preprocessed_data.parameters.theoretical_capacity
                }, {
                    'Parameter': 'Boundary Method',
                    'Value': preprocessed_data.parameters.boundary_method
                }, {
                    'Parameter': 'Baseline Cycle',
                    'Value': preprocessed_data.parameters.baseline_cycle
                }])
                
                metadata_df.to_excel(
                    writer,
                    sheet_name='Parameters',
                    index=False
                )
        
        buffer.seek(0)
        return buffer.getvalue()