import streamlit as st
import tempfile
from typing import Optional
import logging

from ..core.data_loader import DataLoader
from ..core.data_models import RawBatteryData

logger = logging.getLogger(__name__)


class DataInputComponent:
    """Handles file upload and initial data loading"""
    
    @staticmethod
    def render() -> Optional[RawBatteryData]:
        """Render data input UI and return loaded data if available"""
        
        st.header("📁 Data Input")
        
        # Main data file upload
        uploaded_file = st.file_uploader(
            "Upload Basytec data file",
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
                
                with st.spinner("Loading file..."):
                    try:
                        loader = DataLoader()
                        st.session_state.raw_data = loader.load_file(tmp_path)
                        st.success(f"✅ File loaded: {uploaded_file.name}")
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
    def render_test_plan_upload() -> Optional[str]:
        """Render test plan upload UI"""
        
        st.header("📋 Test Plan (Optional)")
        
        test_plan_file = st.file_uploader(
            "Upload test plan file",
            type=['txt'],
            help="Optional: Upload test plan for automatic C-rate configuration",
            key="test_plan_file"
        )
        
        if test_plan_file:
            # Process test plan
            content = test_plan_file.read().decode('utf-8')
            
            with st.expander("Test Plan Content", expanded=False):
                st.text(content[:500] + "..." if len(content) > 500 else content)
            
            return content
        
        return None