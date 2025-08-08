"""
Test Plan Parser Module

Parses battery test plan files to extract C-rate configurations
and other test parameters automatically.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CRatePeriod:
    """Represents a C-rate configuration for a range of cycles"""
    start_cycle: int
    end_cycle: int
    charge_rate: float
    discharge_rate: float
    
    def to_tuple(self) -> Tuple[int, int, float, float]:
        """Convert to tuple format for compatibility"""
        return (self.start_cycle, self.end_cycle, self.charge_rate, self.discharge_rate)


@dataclass
class TestPlanConfig:
    """Configuration extracted from test plan"""
    c_rate_periods: List[CRatePeriod] = field(default_factory=list)
    total_cycles: Optional[int] = None
    test_name: Optional[str] = None
    additional_params: Dict[str, any] = field(default_factory=dict)


class TestPlanParser:
    """Parses test plan files to extract configuration"""
    
    # Common patterns in test plan files (support both . and , for decimals)
    CHARGE_PATTERN = re.compile(r'Charge.*?I=([0-9.,]+)CA', re.IGNORECASE)
    DISCHARGE_PATTERN = re.compile(r'Discharge.*?I=([0-9.,]+)CA', re.IGNORECASE)
    CYCLE_COUNT_PATTERN = re.compile(r'Cycle-?end.*?Count=([0-9]+)', re.IGNORECASE)
    CYCLE_PATTERN = re.compile(r'Cycle.*?Count=([0-9]+)', re.IGNORECASE)
    
    # Alternative patterns for different formats
    CHARGE_ALT_PATTERN = re.compile(r'CC.*?charge.*?([0-9.,]+)\s*C', re.IGNORECASE)
    DISCHARGE_ALT_PATTERN = re.compile(r'CC.*?discharge.*?([0-9.,]+)\s*C', re.IGNORECASE)
    
    @staticmethod
    def parse(file_content: str) -> TestPlanConfig:
        """
        Parse test plan file content to extract configuration
        
        Args:
            file_content: Raw test plan file content
            
        Returns:
            TestPlanConfig object with extracted parameters
        """
        config = TestPlanConfig()
        lines = file_content.split('\n')
        
        # Extract test name if present
        for line in lines[:10]:  # Check first 10 lines for test name
            if 'Test:' in line or 'Name:' in line:
                config.test_name = line.split(':', 1)[1].strip()
                break
        
        # Parse C-rate configurations
        c_rate_periods = TestPlanParser._parse_crate_periods(lines)
        config.c_rate_periods = c_rate_periods
        
        # Calculate total cycles
        if c_rate_periods:
            config.total_cycles = max(p.end_cycle for p in c_rate_periods)
        
        logger.info(f"Parsed test plan: {len(c_rate_periods)} C-rate periods, "
                   f"total cycles: {config.total_cycles}")
        
        return config
    
    @staticmethod
    def _parse_crate_periods(lines: List[str]) -> List[CRatePeriod]:
        """
        Extract C-rate periods from test plan lines
        
        Args:
            lines: List of lines from test plan file
            
        Returns:
            List of CRatePeriod objects
        """
        periods = []
        current_cycle = 1
        
        # Track current configuration being built
        charge_rate = None
        discharge_rate = None
        cycle_count = None
        
        # State tracking
        in_cycle_block = False
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            # Check for charge command
            charge_match = TestPlanParser.CHARGE_PATTERN.search(line)
            if not charge_match:
                charge_match = TestPlanParser.CHARGE_ALT_PATTERN.search(line)
            
            if charge_match:
                try:
                    # Handle both comma and dot decimals
                    rate_str = charge_match.group(1).replace(',', '.')
                    charge_rate = float(rate_str)
                    in_cycle_block = True
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse charge rate from: {line}")
            
            # Check for discharge command
            discharge_match = TestPlanParser.DISCHARGE_PATTERN.search(line)
            if not discharge_match:
                discharge_match = TestPlanParser.DISCHARGE_ALT_PATTERN.search(line)
            
            if discharge_match:
                try:
                    # Handle both comma and dot decimals
                    rate_str = discharge_match.group(1).replace(',', '.')
                    discharge_rate = float(rate_str)
                    in_cycle_block = True
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse discharge rate from: {line}")
            
            # Check for cycle count/end
            cycle_match = TestPlanParser.CYCLE_COUNT_PATTERN.search(line)
            if not cycle_match:
                cycle_match = TestPlanParser.CYCLE_PATTERN.search(line)
            
            if cycle_match and in_cycle_block:
                try:
                    cycle_count = int(cycle_match.group(1))
                    
                    # If we have all required info, create a period
                    if charge_rate is not None and discharge_rate is not None:
                        period = CRatePeriod(
                            start_cycle=current_cycle,
                            end_cycle=current_cycle + cycle_count - 1,
                            charge_rate=charge_rate,
                            discharge_rate=discharge_rate
                        )
                        periods.append(period)
                        
                        logger.debug(f"Added C-rate period: cycles {period.start_cycle}-{period.end_cycle}, "
                                   f"charge: {period.charge_rate}C, discharge: {period.discharge_rate}C")
                        
                        # Update for next period
                        current_cycle += cycle_count
                        
                        # Reset for next block
                        charge_rate = None
                        discharge_rate = None
                        cycle_count = None
                        in_cycle_block = False
                        
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse cycle count from: {line}")
        
        # If no periods found, return a default configuration
        if not periods:
            logger.info("No C-rate periods found in test plan, using default")
            periods = [CRatePeriod(
                start_cycle=1,
                end_cycle=1000,
                charge_rate=0.333,
                discharge_rate=0.333
            )]
        
        return periods
    
    @staticmethod
    def format_periods_for_display(periods: List[CRatePeriod]) -> str:
        """
        Format C-rate periods for display in UI
        
        Args:
            periods: List of CRatePeriod objects
            
        Returns:
            Formatted string for display
        """
        if not periods:
            return "No C-rate periods defined"
        
        lines = []
        for i, period in enumerate(periods, 1):
            lines.append(
                f"Period {i}: Cycles {period.start_cycle}-{period.end_cycle} | "
                f"Charge: {period.charge_rate:.3f}C | Discharge: {period.discharge_rate:.3f}C"
            )
        
        return "\n".join(lines)