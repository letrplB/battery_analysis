import streamlit as st
import tempfile
from typing import Optional
import logging

from core.data_loader import DataLoader
from core.data_models import RawBatteryData
from core.test_plan_parser import TestPlanParser, TestPlanConfig
from core.data_cleaner import DeviceType

logger = logging.getLogger(__name__)


class DataInputComponent:
    """Handles file upload and initial data loading"""
    
    @staticmethod
    def render() -> Optional[RawBatteryData]:
        """Render data input UI and return loaded data if available"""
        
        st.header("📁 Data Input")
        
        # Device type selection
        device_type = st.selectbox(
            "Battery Tester Device",
            options=[
                DeviceType.BASYTEC,
                DeviceType.ARBIN,
                DeviceType.NEWARE,
                DeviceType.BIOLOGIC,
                DeviceType.MACCOR,
                DeviceType.GENERIC
            ],
            format_func=lambda x: x.value.title(),
            help="Select the type of battery tester that generated this data",
            key="device_type"
        )
        
        # Main data file upload
        uploaded_file = st.file_uploader(
            f"Upload {device_type.value.title()} data file",
            type=['txt', 'csv'],
            help="Upload your battery test data file",
            key="main_data_file"
        )
        
        if uploaded_file:
            # Check if file changed
            file_changed = False
            if 'last_uploaded_file' not in st.session_state:
                file_changed = True
            elif st.session_state.last_uploaded_file != uploaded_file.name:
                file_changed = True
            
            if file_changed:
                st.session_state.last_uploaded_file = uploaded_file.name
                st.session_state.raw_data = None  # Reset data
            
            # Load data if not already loaded
            if st.session_state.raw_data is None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                with st.spinner(f"Loading {device_type.value.title()} file..."):
                    try:
                        loader = DataLoader(device_type=device_type)
                        st.session_state.raw_data = loader.load_file(tmp_path)
                        st.success(f"✅ File loaded: {uploaded_file.name}")
                        
                        # Show device-specific info
                        if device_type == DeviceType.BASYTEC:
                            st.info("🔧 Using Basytec profile: European decimal format (comma separator)")
                        elif device_type == DeviceType.ARBIN:
                            st.info("🔧 Using Arbin profile: Time in seconds will be converted to hours")
                        elif device_type == DeviceType.NEWARE:
                            st.info("🔧 Using Neware profile")
                            
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
                        return None
            
            # Display file info
            if st.session_state.raw_data:
                raw_data = st.session_state.raw_data
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Size", f"{raw_data.metadata.file_size_kb:.1f} KB")
                with col2:
                    st.metric("Total Lines", f"{raw_data.metadata.total_lines:,}")
                with col3:
                    st.metric("Data Rows", f"{len(raw_data.data):,}")
                
                # Show metadata in expander
                with st.expander("📋 File Metadata", expanded=False):
                    metadata = raw_data.metadata
                    if metadata.test_name:
                        st.write(f"**Test Name:** {metadata.test_name}")
                    if metadata.battery_name:
                        st.write(f"**Battery:** {metadata.battery_name}")
                    if metadata.test_start:
                        st.write(f"**Start:** {metadata.test_start}")
                    if metadata.test_end:
                        st.write(f"**End:** {metadata.test_end}")
                    if metadata.test_channel:
                        st.write(f"**Channel:** {metadata.test_channel}")
                    if metadata.operator_test:
                        st.write(f"**Operator:** {metadata.operator_test}")
                
                # Show data preview
                with st.expander("👀 Data Preview", expanded=False):
                    st.dataframe(
                        raw_data.data.head(10),
                        use_container_width=True,
                        height=300
                    )
                
                return raw_data
        
        return None
    
    @staticmethod
    def render_test_plan_upload() -> Optional[TestPlanConfig]:
        """Render test plan upload UI and parse configuration"""
        
        st.header("📋 Test Plan (Optional)")
        
        test_plan_file = st.file_uploader(
            "Upload test plan file",
            type=['txt'],
            help="Optional: Upload test plan for automatic C-rate configuration",
            key="test_plan_file"
        )
        
        if test_plan_file:
            try:
                # Read file content with proper encoding handling
                raw_bytes = test_plan_file.read()
                
                # Try different encodings
                content = None
                for encoding in ['utf-8', 'iso-8859-1', 'latin-1', 'cp1252']:
                    try:
                        content = raw_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    # Fallback: decode with errors ignored
                    content = raw_bytes.decode('utf-8', errors='ignore')
                
                # Parse test plan
                parser = TestPlanParser()
                config = parser.parse(content)
                
                # Store in session state
                st.session_state.test_plan_config = config
                
                # Display parsed configuration
                if config.c_rate_periods:
                    st.success(f"✅ Parsed {len(config.c_rate_periods)} C-rate periods from test plan")
                    
                    with st.expander("📊 Parsed C-Rate Configuration", expanded=True):
                        for i, period in enumerate(config.c_rate_periods, 1):
                            st.write(
                                f"**Period {i}:** Cycles {period.start_cycle}-{period.end_cycle} | "
                                f"Charge: {period.charge_rate:.3f}C | Discharge: {period.discharge_rate:.3f}C"
                            )
                        
                        if config.total_cycles:
                            st.write(f"**Total Cycles:** {config.total_cycles}")
                
                # Show raw content in expander
                with st.expander("📄 Test Plan Content", expanded=False):
                    st.text(content[:500] + "..." if len(content) > 500 else content)
                
                return config
                
            except Exception as e:
                st.error(f"❌ Error parsing test plan: {str(e)}")
                logger.exception("Test plan parsing error")
                return None
        
        return None