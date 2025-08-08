import streamlit as st
from typing import Optional, List, Tuple
import logging

from core.data_models import (
    RawBatteryData,
    ProcessingParameters,
    PreprocessedData
)
from core.preprocessor import DataPreprocessor

logger = logging.getLogger(__name__)


class PreprocessingComponent:
    """Handles data preprocessing configuration and execution"""
    
    @staticmethod
    def render_parameters() -> Optional[ProcessingParameters]:
        """Render preprocessing parameter configuration"""
        
        # Header with settings icon
        st.markdown("""
        <h2 style="display: flex; align-items: center;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.5rem;">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M12 1v6M12 17v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M1 12h6M17 12h6M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24"></path>
            </svg>
            Analysis Parameters
        </h2>
        """, unsafe_allow_html=True)
        
        # Active material weight
        active_material = st.number_input(
            "Active material weight (g)",
            min_value=0.001,
            max_value=10.0,
            value=0.035,
            step=0.001,
            format="%.3f",
            help="Weight of active material in grams"
        )
        
        # Theoretical capacity
        theoretical_capacity = st.number_input(
            "Theoretical capacity (Ah)",
            min_value=0.001,
            max_value=10.0,
            value=0.050,
            step=0.001,
            format="%.3f",
            help="Theoretical capacity in Ah"
        )
        
        # C-rate configuration
        st.subheader("C-Rate Configuration")
        c_rates = PreprocessingComponent._render_crate_config()
        
        # Boundary detection
        st.subheader("Boundary Detection")
        boundary_method = st.selectbox(
            "Detection method",
            ["State-based", "Zero-crossing"],
            help="Method for detecting cycle boundaries"
        )
        
        # Baseline cycle
        baseline_cycle = st.number_input(
            "Baseline cycle for retention",
            min_value=1,
            max_value=1000,
            value=30,
            help="Cycle number to use as 100% retention baseline"
        )
        
        return ProcessingParameters(
            active_material_weight=active_material,
            theoretical_capacity=theoretical_capacity,
            c_rates=c_rates,
            boundary_method=boundary_method,
            baseline_cycle=baseline_cycle
        )
    
    @staticmethod
    def _render_crate_config() -> List[Tuple[int, int, float, float]]:
        """Render C-rate configuration interface"""
        
        # Check if we have parsed test plan configuration
        if 'test_plan_config' in st.session_state and st.session_state.test_plan_config:
            config = st.session_state.test_plan_config
            if config.c_rate_periods:
                st.info("Using C-rates from test plan. Uncheck to customize.")
                
                use_test_plan = st.checkbox("Use test plan C-rates", value=True, key="use_test_plan")
                
                if use_test_plan:
                    # Convert CRatePeriod objects to tuples
                    return [period.to_tuple() for period in config.c_rate_periods]
        
        # Initialize C-rates in session state if not present
        if 'c_rates' not in st.session_state:
            st.session_state.c_rates = [(1, 1000, 0.333, 0.333)]
        
        # Simple vs custom mode
        use_custom = st.checkbox("Use custom C-rate periods", value=False)
        
        if not use_custom:
            # Simple uniform C-rate
            c_rate = st.number_input(
                "C-rate for all cycles",
                min_value=0.1,
                max_value=10.0,
                value=0.333,
                step=0.1,
                format="%.3f"
            )
            return [(1, 1000, c_rate, c_rate)]
        
        else:
            # Advanced C-rate configuration
            st.write("Define C-rate periods:")
            
            # Control buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Add Period"):
                    st.session_state.c_rates.append((1, 30, 0.333, 0.333))
                    st.rerun()
            with col2:
                if st.button("Reset"):
                    st.session_state.c_rates = [(1, 1000, 0.333, 0.333)]
                    st.rerun()
            
            # Display periods
            updated_rates = []
            for i, (start, end, charge, discharge) in enumerate(st.session_state.c_rates):
                with st.expander(f"Period {i+1}", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        new_start = st.number_input(
                            "Start",
                            min_value=1,
                            value=start,
                            key=f"cr_start_{i}"
                        )
                    
                    with col2:
                        new_end = st.number_input(
                            "End",
                            min_value=1,
                            value=end,
                            key=f"cr_end_{i}"
                        )
                    
                    with col3:
                        new_charge = st.number_input(
                            "Charge",
                            min_value=0.1,
                            max_value=10.0,
                            value=charge,
                            step=0.1,
                            format="%.3f",
                            key=f"cr_charge_{i}"
                        )
                    
                    with col4:
                        new_discharge = st.number_input(
                            "Discharge",
                            min_value=0.1,
                            max_value=10.0,
                            value=discharge,
                            step=0.1,
                            format="%.3f",
                            key=f"cr_discharge_{i}"
                        )
                    
                    if st.button(f"Remove", key=f"cr_remove_{i}"):
                        # Skip this period
                        continue
                    
                    updated_rates.append((new_start, new_end, new_charge, new_discharge))
            
            if updated_rates != st.session_state.c_rates:
                st.session_state.c_rates = updated_rates
            
            return updated_rates
    
    @staticmethod
    def render_preprocessing_button(
        raw_data: Optional[RawBatteryData],
        parameters: Optional[ProcessingParameters]
    ) -> Optional[PreprocessedData]:
        """Render preprocessing button and execute if clicked"""
        
        st.markdown("---")
        
        # Check if ready to preprocess
        ready = raw_data is not None and parameters is not None
        
        if st.button(
            "Prepare Data",
            type="primary",
            disabled=not ready,
            use_container_width=True,
            help="Preprocess data with selected parameters"
        ):
            if ready:
                with st.spinner("Preprocessing data..."):
                    try:
                        preprocessor = DataPreprocessor()
                        preprocessed = preprocessor.preprocess(raw_data, parameters)
                        
                        # Store in session state
                        st.session_state.preprocessed_data = preprocessed
                        
                        # Show success message
                        st.success(
                            f"Data prepared: {len(preprocessed.cycle_boundaries)} cycles detected"
                        )
                        
                        # Show warnings if any
                        if preprocessed.validation_warnings:
                            with st.expander("Validation Warnings", expanded=True):
                                for warning in preprocessed.validation_warnings:
                                    st.warning(warning)
                        
                        return preprocessed
                        
                    except Exception as e:
                        st.error(f"Preprocessing failed: {str(e)}")
                        logger.exception("Preprocessing error")
                        return None
        
        # Show current status
        if st.session_state.get('preprocessed_data'):
            st.success("Data ready for analysis")
        elif raw_data:
            st.info("Click 'Prepare Data' to continue")
        else:
            st.info("Upload a file to begin")
        
        return st.session_state.get('preprocessed_data')