"""
Excel export functionality for radiology data
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import Rule
import re
import datetime
from typing import Dict, List, Any, Optional


def _sanitize_name(name: str) -> str:
    """Keep A-Z a-z 0-9 _ -, replace others with underscore."""
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", name.strip())


def _timestamp() -> str:
    """Return local timestamp YYYY-MM-DD_HHMMSS."""
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def export_excel(records, folder_path, sheet="radiology_data", blue_argb="FFCCE5FF", force_blocks=None):
    """Export records to Excel with formatting"""
    # ... (move implementation from parser.py)
    pass


def convert_parsed_data_to_ra_d_ps_format(dataframes):
    """Convert parsed data to RA-D-PS format"""
    # ... (move implementation from parser.py)
    pass
