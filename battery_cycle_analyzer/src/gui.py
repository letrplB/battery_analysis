"""
Battery Cycle Analyzer - Streamlit GUI Application

This module provides a web-based GUI for analyzing battery cycle data from Basytec Battery Test System.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import traceback
from analyzer import parse_header, load_data, analyze_cycles, export_results
import re
from typing import List, Dict


def decode_uploaded_file(uploaded_file):
    """
    Decode uploaded file with multiple encoding attempts.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Decoded file content as string
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            file_content = uploaded_file.getvalue().decode(encoding)
            return file_content
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"Could not decode file with any of the tried encodings: {encodings}")


def parse_test_plan(file_content: str) -> List[Dict]:
    """
    Parse test plan file to extract C-rate configurations.
    
    Args:
        file_content: Raw test plan file content
        
    Returns:
        List of C-rate configuration dictionaries
    """
    lines = file_content.split('\n')
    crate_configs = []
    current_cycle = 1
    
    # Track current cycle group
    charge_crate = None
    discharge_crate = None
    cycle_count = 1
    
    for line in lines:
        line = line.strip()
        
        # Look for charge commands
        if 'Charge' in line and 'I=' in line:
            # Extract current value (e.g., "I=0.1CA" -> 0.1)
            match = re.search(r'I=([0-9.]+)CA', line)
            if match:
                charge_crate = float(match.group(1))
        
        # Look for discharge commands  
        elif 'Discharge' in line and 'I=' in line:
            # Extract current value (e.g., "I=0.1CA" -> 0.1)
            match = re.search(r'I=([0-9.]+)CA', line)
            if match:
                discharge_crate = float(match.group(1))
        
        # Look for cycle end with count
        elif 'Cycle-end' in line and 'Count=' in line:
            # Extract cycle count (e.g., "Count=3" -> 3)
            match = re.search(r'Count=([0-9]+)', line)
            if match and charge_crate is not None and discharge_crate is not None:
                cycle_count = int(match.group(1))
                
                # Add configuration for this cycle group
                crate_configs.append({
                    'start_cycle': current_cycle,
                    'end_cycle': current_cycle + cycle_count - 1,
                    'charge_crate': charge_crate,
                    'discharge_crate': discharge_crate
                })
                
                # Update current cycle for next group
                current_cycle += cycle_count
                
                # Reset for next group
                charge_crate = None
                discharge_crate = None
    
    # If no configurations found, return default
    if not crate_configs:
        crate_configs = [{'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}]
    
    return crate_configs


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Battery Cycle Analyzer",
        page_icon="🔋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("🔋 Battery Cycle Stability Analyzer")
    st.markdown("""
    This tool analyzes battery cycle data from Basytec Battery Test System files.
    Upload your data file, set parameters, and get detailed cycle analysis with visualizations.
    """)
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📁 Data Input")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Basytec data file",
            type=["txt", "csv"],
            help="Select a .txt or .csv file exported from Basytec Battery Test System (max 300 MB)"
        )
        
        # Display file size warning for large files
        if uploaded_file is not None:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > 100:
                st.warning(f"⚠️ Large file detected ({file_size_mb:.1f} MB). Processing may take longer.")
            elif file_size_mb > 200:
                st.error(f"🚨 Very large file ({file_size_mb:.1f} MB). Consider splitting the data if processing becomes too slow.")
        
        # Test plan uploader
        test_plan_file = st.file_uploader(
            "Upload test plan file (optional)",
            type=["txt"],
            help="Upload the test plan file to automatically extract C-rate configurations",
            key="test_plan_uploader"
        )
        
        st.header("⚙️ Analysis Parameters")
        
        # Active material weight input
        active_material_weight = st.number_input(
            "Active material weight (g)",
            min_value=0.001,
            max_value=1000.0,
            value=1.0,
            step=0.001,
            format="%.3f",
            help="Weight of the active material in grams for specific capacity calculation"
        )
        
        # Theoretical capacity input
        theoretical_capacity = st.number_input(
            "Theoretical capacity (Ah)",
            min_value=0.001,
            max_value=1000.0,
            value=0.050,
            step=0.001,
            format="%.3f",
            help="Theoretical/nominal capacity of the battery in Ah for C-rate calculation"
        )
        
        # C-rate inputs - multiple periods with cycle ranges
        st.subheader("🔋 C-Rate Configuration")
        
        # Parse test plan if uploaded
        if test_plan_file is not None:
            try:
                test_plan_content = decode_uploaded_file(test_plan_file)
                parsed_configs = parse_test_plan(test_plan_content)
                
                # Update session state with parsed configurations
                if 'auto_parsed' not in st.session_state or st.session_state.get('last_test_plan') != test_plan_file.name:
                    st.session_state.crate_configs = parsed_configs
                    st.session_state.auto_parsed = True
                    st.session_state.last_test_plan = test_plan_file.name
                    st.success(f"✅ Parsed {len(parsed_configs)} C-rate periods from test plan!")
                
            except Exception as e:
                st.error(f"Error parsing test plan: {str(e)}")
        
        # Initialize session state for C-rate configurations if not already set
        if 'crate_configs' not in st.session_state:
            st.session_state.crate_configs = [
                {'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}
            ]
        
        if test_plan_file is not None:
            st.info("📋 C-rate configurations loaded from test plan. You can still edit them below if needed.")
        else:
            st.markdown("Define C-rate periods for different cycle ranges:")
        
        # Display existing configurations
        for i, config in enumerate(st.session_state.crate_configs):
            with st.container():
                st.markdown(f"**Period {i+1}:**")
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                with col1:
                    config['start_cycle'] = st.number_input(
                        f"Start Cycle", 
                        min_value=1, 
                        value=config['start_cycle'], 
                        key=f"start_{i}",
                        help="First cycle for this C-rate period"
                    )
                
                with col2:
                    config['end_cycle'] = st.number_input(
                        f"End Cycle", 
                        min_value=config['start_cycle'], 
                        value=config['end_cycle'], 
                        key=f"end_{i}",
                        help="Last cycle for this C-rate period"
                    )
                
                with col3:
                    config['charge_crate'] = st.number_input(
                        f"Charge C-rate", 
                        min_value=0.001, 
                        max_value=100.0, 
                        value=config['charge_crate'], 
                        step=0.001, 
                        format="%.3f", 
                        key=f"charge_{i}",
                        help="C-rate for charging cycles in this period"
                    )
                
                with col4:
                    config['discharge_crate'] = st.number_input(
                        f"Discharge C-rate", 
                        min_value=0.001, 
                        max_value=100.0, 
                        value=config['discharge_crate'], 
                        step=0.001, 
                        format="%.3f", 
                        key=f"discharge_{i}",
                        help="C-rate for discharging cycles in this period"
                    )
                
                with col5:
                    if len(st.session_state.crate_configs) > 1:
                        if st.button("🗑️", key=f"delete_{i}", help="Delete this period"):
                            st.session_state.crate_configs.pop(i)
                            st.rerun()
                
                st.divider()
        
        # Add new configuration button
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ Add C-rate Period"):
                last_config = st.session_state.crate_configs[-1] if st.session_state.crate_configs else {}
                new_start = last_config.get('end_cycle', 1000) + 1
                st.session_state.crate_configs.append({
                    'start_cycle': new_start,
                    'end_cycle': new_start + 100,
                    'charge_crate': 0.1,
                    'discharge_crate': 0.1
                })
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset to Default"):
                st.session_state.crate_configs = [
                    {'start_cycle': 1, 'end_cycle': 1000, 'charge_crate': 0.1, 'discharge_crate': 0.1}
                ]
                st.session_state.auto_parsed = False
                st.rerun()
        
        # Boundary detection method
        boundary_method = st.selectbox(
            "Boundary detection method",
            ["State-based", "Zero-crossing"],
            index=0,
            help="Method for detecting cycle boundaries in the data"
        )
        
        # Baseline cycle selection
        baseline_cycle = st.number_input(
            "Baseline cycle for retention calculation",
            min_value=0,
            max_value=10000,
            value=0,
            step=1,
            help="Cycle number to use as baseline for retention calculation. Use 0 for auto-selection of the best realistic cycle (recommended)."
        )
        
        # Analysis button
        analyze_button = st.button(
            "🔍 Analyze Data",
            type="primary",
            disabled=uploaded_file is None
        )
    
    # Main content area
    if uploaded_file is not None:
        try:
            # Read file content with encoding handling
            file_content = decode_uploaded_file(uploaded_file)
            
            # Display file info
            st.subheader("📄 File Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File name", uploaded_file.name)
            with col2:
                st.metric("File size", f"{len(file_content) / 1024:.1f} KB")
            with col3:
                st.metric("Lines", len(file_content.split('\n')))
            
            # Parse and display metadata
            metadata = parse_header(file_content)
            if metadata:
                st.subheader("📋 Test Metadata")
                
                # Create columns for metadata display
                meta_cols = st.columns(2)
                meta_items = list(metadata.items())
                mid_point = len(meta_items) // 2
                
                with meta_cols[0]:
                    for key, value in meta_items[:mid_point]:
                        st.text(f"{key}: {value}")
                
                with meta_cols[1]:
                    for key, value in meta_items[mid_point:]:
                        st.text(f"{key}: {value}")
            
            # Perform analysis when button is clicked
            if analyze_button:
                with st.spinner("Analyzing battery cycle data..."):
                    try:
                        # Load data
                        df = load_data(file_content)
                        
                        # Display data preview
                        st.subheader("📊 Data Preview")
                        st.text(f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        # Perform cycle analysis
                        # Generate analysis name from uploaded file
                        analysis_name = uploaded_file.name.split('.')[0] if uploaded_file.name else "unknown_file"
                        results_df, summary = analyze_cycles(df, active_material_weight, theoretical_capacity, boundary_method, st.session_state.crate_configs, baseline_cycle, analysis_name)
                        
                        if results_df.empty:
                            st.error("No cycles found in the data. Please check your file and boundary detection method.")
                            return
                        
                        # Display log file information
                        if summary.get('Log_File'):
                            st.info(f"📝 Warnings and detailed logs saved to: `{summary['Log_File']}`")
                        
                        # Display summary statistics
                        st.subheader("📈 Analysis Summary")
                        
                        summary_cols = st.columns(4)
                        with summary_cols[0]:
                            st.metric("Total Half-Cycles", summary['Total_Half_Cycles'])
                        with summary_cols[1]:
                            st.metric("Charge Cycles", summary['Total_Charge_Cycles'])
                        with summary_cols[2]:
                            st.metric("Discharge Cycles", summary['Total_Discharge_Cycles'])
                        with summary_cols[3]:
                            st.metric("Test Duration", f"{summary['Total_Test_Duration_h']:.1f} h")
                        
                        # C-rate periods information
                        st.subheader("🔋 C-Rate Periods")
                        crate_cols = st.columns(min(len(st.session_state.crate_configs), 4))
                        for i, config in enumerate(st.session_state.crate_configs[:4]):  # Show max 4 periods
                            with crate_cols[i]:
                                st.metric(
                                    f"Period {i+1}",
                                    f"Cycles {config['start_cycle']}-{config['end_cycle']}",
                                    f"C: {config['charge_crate']:.3f} | D: {config['discharge_crate']:.3f}"
                                )
                        
                        if len(st.session_state.crate_configs) > 4:
                            st.info(f"... and {len(st.session_state.crate_configs) - 4} more periods")
                        
                        # Additional summary metrics for discharge cycles
                        if summary.get('Total_Discharge_Cycles', 0) > 0:
                            summary_cols2 = st.columns(3)
                            with summary_cols2[0]:
                                st.metric("Initial Discharge Specific Capacity", f"{summary['Initial_Discharge_Specific_mAh_per_g']:.1f} mAh/g")
                            with summary_cols2[1]:
                                st.metric("Final Discharge Specific Capacity", f"{summary['Final_Discharge_Specific_mAh_per_g']:.1f} mAh/g")
                            with summary_cols2[2]:
                                st.metric("Discharge Retention", f"{summary['Discharge_Capacity_Retention_%']:.1f}%")
                        
                        # Additional summary metrics for charge cycles
                        if summary.get('Total_Charge_Cycles', 0) > 0:
                            summary_cols3 = st.columns(3)
                            with summary_cols3[0]:
                                st.metric("Initial Charge Specific Capacity", f"{summary['Initial_Charge_Specific_mAh_per_g']:.1f} mAh/g")
                            with summary_cols3[1]:
                                st.metric("Final Charge Specific Capacity", f"{summary['Final_Charge_Specific_mAh_per_g']:.1f} mAh/g")
                            with summary_cols3[2]:
                                st.metric("Charge Retention", f"{summary['Charge_Capacity_Retention_%']:.1f}%")
                        
                        # Display results table
                        st.subheader("📋 Cycle Results")
                        st.dataframe(results_df, use_container_width=True)
                        
                        # Create visualizations
                        st.subheader("📊 Visualizations")
                        
                        # Create tabs for different plots
                        tab1, tab2, tab3, tab4 = st.tabs(["Capacity vs Cycle", "Specific Capacity", "Voltage Analysis", "Cycle Duration"])
                        
                        with tab1:
                            # Separate charge and discharge for plotting
                            charge_data = results_df[results_df['HalfCycleType'] == 'charge']
                            discharge_data = results_df[results_df['HalfCycleType'] == 'discharge']
                            
                            fig1 = go.Figure()
                            
                            if len(discharge_data) > 0:
                                fig1.add_trace(go.Scatter(
                                    x=discharge_data['Cycle'], 
                                    y=discharge_data['Capacity_Ah'],
                                    mode='lines+markers',
                                    name='Discharge',
                                    line=dict(color='blue'),
                                    text=discharge_data['Cycle'],
                                    hovertemplate='Cycle: %{text}<br>Capacity: %{y:.4f} Ah<extra></extra>'
                                ))
                            
                            if len(charge_data) > 0:
                                fig1.add_trace(go.Scatter(
                                    x=charge_data['Cycle'], 
                                    y=charge_data['Capacity_Ah'],
                                    mode='lines+markers',
                                    name='Charge',
                                    line=dict(color='red'),
                                    text=charge_data['Cycle'],
                                    hovertemplate='Cycle: %{text}<br>Capacity: %{y:.4f} Ah<extra></extra>'
                                ))
                            
                            fig1.update_layout(
                                title='Capacity vs Cycle Number',
                                xaxis_title='Cycle Number',
                                yaxis_title='Capacity (Ah)',
                                height=500
                            )
                            st.plotly_chart(fig1, use_container_width=True)
                        
                        with tab2:
                            fig2 = go.Figure()
                            
                            if len(discharge_data) > 0:
                                fig2.add_trace(go.Scatter(
                                    x=discharge_data['Cycle'], 
                                    y=discharge_data['Specific_mAh_per_g'],
                                    mode='lines+markers',
                                    name='Discharge',
                                    line=dict(color='blue'),
                                    text=discharge_data['Cycle'],
                                    hovertemplate='Cycle: %{text}<br>Specific Capacity: %{y:.1f} mAh/g<extra></extra>'
                                ))
                            
                            if len(charge_data) > 0:
                                fig2.add_trace(go.Scatter(
                                    x=charge_data['Cycle'], 
                                    y=charge_data['Specific_mAh_per_g'],
                                    mode='lines+markers',
                                    name='Charge',
                                    line=dict(color='red'),
                                    text=charge_data['Cycle'],
                                    hovertemplate='Cycle: %{text}<br>Specific Capacity: %{y:.1f} mAh/g<extra></extra>'
                                ))
                            
                            fig2.update_layout(
                                title='Specific Capacity vs Cycle Number',
                                xaxis_title='Cycle Number',
                                yaxis_title='Specific Capacity (mAh/g)',
                                height=500
                            )
                            st.plotly_chart(fig2, use_container_width=True)
                        
                        with tab3:
                            fig4 = make_subplots(specs=[[{"secondary_y": False}]])
                            
                            if len(discharge_data) > 0:
                                fig4.add_trace(go.Scatter(
                                    x=discharge_data['Cycle'], 
                                    y=discharge_data['Voltage_Max_V'], 
                                    mode='lines+markers', 
                                    name='Discharge Max V', 
                                    line=dict(color='darkblue')
                                ))
                                fig4.add_trace(go.Scatter(
                                    x=discharge_data['Cycle'], 
                                    y=discharge_data['Voltage_Min_V'], 
                                    mode='lines+markers', 
                                    name='Discharge Min V', 
                                    line=dict(color='lightblue')
                                ))
                                fig4.add_trace(go.Scatter(
                                    x=discharge_data['Cycle'], 
                                    y=discharge_data['Voltage_Avg_V'], 
                                    mode='lines+markers', 
                                    name='Discharge Avg V', 
                                    line=dict(color='blue')
                                ))
                            
                            if len(charge_data) > 0:
                                fig4.add_trace(go.Scatter(
                                    x=charge_data['Cycle'], 
                                    y=charge_data['Voltage_Max_V'], 
                                    mode='lines+markers', 
                                    name='Charge Max V', 
                                    line=dict(color='darkred')
                                ))
                                fig4.add_trace(go.Scatter(
                                    x=charge_data['Cycle'], 
                                    y=charge_data['Voltage_Min_V'], 
                                    mode='lines+markers', 
                                    name='Charge Min V', 
                                    line=dict(color='pink')
                                ))
                                fig4.add_trace(go.Scatter(
                                    x=charge_data['Cycle'], 
                                    y=charge_data['Voltage_Avg_V'], 
                                    mode='lines+markers', 
                                    name='Charge Avg V', 
                                    line=dict(color='red')
                                ))
                            
                            fig4.update_layout(
                                title='Voltage Analysis vs Cycle Number',
                                xaxis_title='Cycle Number',
                                yaxis_title='Voltage (V)',
                                height=500
                            )
                            st.plotly_chart(fig4, use_container_width=True)
                        
                        with tab4:
                            fig5 = go.Figure()
                            
                            if len(discharge_data) > 0:
                                fig5.add_trace(go.Scatter(
                                    x=discharge_data['Cycle'], 
                                    y=discharge_data['Duration_h'],
                                    mode='lines+markers',
                                    name='Discharge',
                                    line=dict(color='blue'),
                                    text=discharge_data['Cycle'],
                                    hovertemplate='Cycle: %{text}<br>Duration: %{y:.2f} h<extra></extra>'
                                ))
                            
                            if len(charge_data) > 0:
                                fig5.add_trace(go.Scatter(
                                    x=charge_data['Cycle'], 
                                    y=charge_data['Duration_h'],
                                    mode='lines+markers',
                                    name='Charge',
                                    line=dict(color='red'),
                                    text=charge_data['Cycle'],
                                    hovertemplate='Cycle: %{text}<br>Duration: %{y:.2f} h<extra></extra>'
                                ))
                            
                            fig5.update_layout(
                                title='Cycle Duration vs Cycle Number',
                                xaxis_title='Cycle Number',
                                yaxis_title='Duration (h)',
                                height=500
                            )
                            st.plotly_chart(fig5, use_container_width=True)
                        
                        # Download section
                        st.subheader("💾 Download Results")
                        
                        # Prepare CSV for download
                        csv_buffer = io.StringIO()
                        
                        # Write metadata and summary as comments
                        csv_buffer.write("# Battery Cycle Analysis Results\n")
                        csv_buffer.write("# Generated from Basytec Battery Test System data\n")
                        csv_buffer.write("#\n")
                        
                        for key, value in metadata.items():
                            csv_buffer.write(f"# {key}: {value}\n")
                        
                        csv_buffer.write("#\n")
                        csv_buffer.write("# Analysis Parameters:\n")
                        csv_buffer.write(f"# Active Material Weight: {active_material_weight} g\n")
                        csv_buffer.write(f"# Theoretical Capacity: {theoretical_capacity} Ah\n")
                        csv_buffer.write(f"# Boundary Detection Method: {boundary_method}\n")
                        csv_buffer.write("#\n")
                        csv_buffer.write("# C-Rate Configurations:\n")
                        for i, config in enumerate(st.session_state.crate_configs):
                            csv_buffer.write(f"# Period {i+1}: Cycles {config['start_cycle']}-{config['end_cycle']}, Charge: {config['charge_crate']}, Discharge: {config['discharge_crate']}\n")
                        csv_buffer.write("#\n")
                        csv_buffer.write("# Summary Statistics:\n")
                        for key, value in summary.items():
                            csv_buffer.write(f"# {key}: {value}\n")
                        
                        csv_buffer.write("#\n")
                        csv_buffer.write("# Cycle Data:\n")
                        
                        # Write the DataFrame
                        results_df.to_csv(csv_buffer, index=False)
                        csv_content = csv_buffer.getvalue()
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv_content,
                            file_name=f"cycle_analysis_{uploaded_file.name.split('.')[0]}.csv",
                            mime="text/csv"
                        )
                        
                        # Success message
                        st.success(f"✅ Analysis completed successfully! Found {len(results_df)} cycles.")
                        
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.text("Error details:")
                        st.code(traceback.format_exc())
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.text("Error details:")
            st.code(traceback.format_exc())
    
    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload a Basytec data file to begin analysis.")
        
        st.subheader("📖 Instructions")
        st.markdown("""
        1. **Upload your data file**: Select a .txt or .csv file exported from Basytec Battery Test System
        2. **Upload test plan (optional)**: Upload the test plan file to automatically extract C-rate configurations
        3. **Set parameters**: 
           - Enter the active material weight in grams
           - Configure C-rate periods (auto-filled from test plan if uploaded)
           - Choose the boundary detection method
        4. **Analyze**: Click the "Analyze Data" button to process your data
        5. **Review results**: Examine the summary statistics, cycle data, and visualizations
        6. **Download**: Save the results as a CSV file for further analysis
        
        ### Supported File Formats
        **Data files**: .txt or .csv files with:
        - Metadata headers starting with `~`
        - Space or tab-separated data columns
        - Required columns: `Time[h]`, `Command`, `U[V]`, `I[A]`, `State`
        
        **Test plan files**: .txt files with cycle definitions containing:
        - Charge/Discharge commands with current specifications (e.g., `I=0.1CA`)
        - Cycle-end commands with count specifications (e.g., `Count=3`)
        
        ### Boundary Detection Methods
        - **State-based**: Uses the `State` column to detect cycle boundaries (recommended)
        - **Zero-crossing**: Detects boundaries based on current sign changes
        """)
        
        # Example test plan format
        with st.expander("📋 Test Plan File Format Example"):
            st.code("""
Charge                                I=0.1CA    U>3.9V
Discharge                             I=0.1CA    U<1.5V  
Cycle-end                             Count=3

Charge                                I=0.2CA    U>3.9V
Discharge                             I=0.2CA    U<1.5V
Cycle-end                             Count=5
            """, language="text")


if __name__ == "__main__":
    main() 