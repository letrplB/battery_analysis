import streamlit as st
import logging
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import GUI components
from gui_components.data_input import DataInputComponent
from gui_components.preprocessing import PreprocessingComponent
from gui_components.analysis_selector import AnalysisSelectorComponent
from gui_components.results_viewer import ResultsViewerComponent
from gui_components.export_manager import ExportManagerComponent

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
        st.session_state.c_rates = [(1, 1000, 0.333, 0.333)]


def render_sidebar():
    """Render sidebar with data input and preprocessing"""
    
    with st.sidebar:
        st.title("📊 Data Preparation")
        
        # Data input section
        raw_data = DataInputComponent.render()
        
        # Test plan upload (optional) - moved before parameters so C-rates can be used
        test_plan_config = DataInputComponent.render_test_plan_upload()
        
        # Preprocessing parameters
        parameters = None
        if raw_data:
            parameters = PreprocessingComponent.render_parameters()
        
        # Preprocessing execution
        if raw_data and parameters:
            PreprocessingComponent.render_preprocessing_button(raw_data, parameters)


def render_main_panel():
    """Render main panel with analysis and results"""
    
    st.title("🔋 Battery Cycle Analyzer")
    st.write("Advanced battery cycle analysis with modular processing pipeline")
    
    # Check if data is preprocessed
    if st.session_state.preprocessed_data is None:
        # Show welcome message
        st.info("""
        ### 👋 Welcome to Battery Cycle Analyzer
        
        **Getting Started:**
        1. 📁 Upload your battery test file in the sidebar
        2. ⚙️ Configure analysis parameters
        3. 🚀 Click "Prepare Data" to preprocess
        4. 🔬 Select analysis mode and run analysis
        """)
        
        # Show sample workflow
        with st.expander("📚 Sample Workflow", expanded=False):
            st.markdown("""
            1. **Upload Data**: Select your Basytec .txt or .csv file
            2. **Set Parameters**: 
               - Active material weight (e.g., 0.035 g)
               - Theoretical capacity (e.g., 0.050 Ah)
               - C-rate configuration
            3. **Prepare Data**: Click button to detect cycles and validate
            4. **Choose Analysis**:
               - Standard: Capacity, retention, efficiency trends
               - dQ/dU: Differential capacity for degradation analysis
               - Combined: Both analyses together
            5. **Export Results**: Download CSV, Excel, or report
            """)
        
        return
    
    # Show preprocessing summary
    prep_data = st.session_state.preprocessed_data
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Cycles", len(prep_data.cycle_boundaries))
    with col2:
        if prep_data.cycle_metadata is not None and not prep_data.cycle_metadata.empty:
            avg_cap = prep_data.cycle_metadata['Specific_Discharge_mAhg'].mean()
            st.metric("⚡ Avg Capacity", f"{avg_cap:.1f} mAh/g")
        else:
            st.metric("⚡ Avg Capacity", "N/A")
    with col3:
        st.metric("📈 Data Points", f"{len(prep_data.raw_data.data):,}")
    with col4:
        st.metric("⚖️ Active Material", f"{prep_data.parameters.active_material_weight:.3f} g")
    
    st.markdown("---")
    
    # Analysis section
    AnalysisSelectorComponent.render(prep_data)
    
    # Results section
    if st.session_state.analysis_results and st.session_state.analysis_mode:
        ResultsViewerComponent.render(
            st.session_state.analysis_results,
            st.session_state.analysis_mode
        )
        
        # Export section
        ExportManagerComponent.render(
            st.session_state.analysis_results,
            st.session_state.preprocessed_data,
            st.session_state.analysis_mode
        )


def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="Battery Cycle Analyzer",
        page_icon="🔋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_sidebar()
    render_main_panel()


if __name__ == "__main__":
    main()