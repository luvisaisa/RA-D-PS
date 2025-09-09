"""
RA-D-PS: Radiology XML Data Processing System

A comprehensive Python package for parsing, analyzing, and exporting 
radiology XML data from various medical imaging systems.
"""

# Import from the main parser module (copied from XMLPARSE.py)
from .parser import (
    parse_radiology_sample,
    parse_multiple,
    export_excel,
    convert_parsed_data_to_ra_d_ps_format,
    NYTXMLGuiApp,
    open_file_cross_platform,
    detect_parse_case,
    get_expected_attributes_for_case
)

# Import database functionality
try:
    from .database import RadiologyDatabase
except ImportError:
    # Database might not be available in all environments
    RadiologyDatabase = None

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
    'get_expected_attributes_for_case'
]

# Ensure backward compatibility
__all__ = [
    'parse_radiology_sample',
    'parse_multiple', 
    'export_excel',
    'convert_parsed_data_to_ra_d_ps_format',
    'NYTXMLGuiApp',
    'RadiologyDatabase',
    'open_file_cross_platform',
    'detect_parse_case',
    'get_expected_attributes_for_case'
]
