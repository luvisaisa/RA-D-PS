"""
RA-D-PS: Radiology XML Data Processing System

A comprehensive Python package for parsing, analyzing, and exporting 
radiology XML data from various medical imaging systems.
"""

# Import from the main parser module
from .parser import (
    parse_radiology_sample,
    parse_multiple,
    export_excel,
    convert_parsed_data_to_ra_d_ps_format,
    open_file_cross_platform,
    detect_parse_case,
    get_expected_attributes_for_case
)

# Import GUI from separate module
from .gui import NYTXMLGuiApp

# Import database functionality
try:
    from .database import RadiologyDatabase
except ImportError:
    # Database might not be available in all environments
    RadiologyDatabase = None

# Import structure detection and batch processing
try:
    from .structure_detector import XMLStructureDetector, batch_detect_parse_cases
    from .batch_processor import BatchProcessor, analyze_batch_structure, create_optimized_processing_plan
except ImportError:
    # Structure detection might not be available in all environments
    XMLStructureDetector = None
    BatchProcessor = None
    batch_detect_parse_cases = None
    analyze_batch_structure = None
    create_optimized_processing_plan = None

__version__ = "1.0.0"
__author__ = "RA-D-PS Team"

# Define public API
__all__ = [
    'parse_radiology_sample',
    'parse_multiple', 
    'export_excel',
    'convert_parsed_data_to_ra_d_ps_format',
    'NYTXMLGuiApp',
    'RadiologyDatabase',
    'open_file_cross_platform',
    'detect_parse_case',
    'get_expected_attributes_for_case',
    'XMLStructureDetector',
    'BatchProcessor',
    'batch_detect_parse_cases',
    'analyze_batch_structure',
    'create_optimized_processing_plan'
]
