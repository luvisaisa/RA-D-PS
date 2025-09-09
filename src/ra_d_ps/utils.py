"""
Utility functions for the RA-D-PS package
"""
import re
import datetime
from typing import Any, Dict, List, Optional


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def format_timestamp(dt: datetime.datetime = None) -> str:
    """Format timestamp for file naming"""
    if dt is None:
        dt = datetime.datetime.now()
    return dt.strftime("%Y-%m-%d_%H%M%S")


def validate_xml_file(file_path: str) -> bool:
    """Validate that file is a readable XML file"""
    try:
        import xml.etree.ElementTree as ET
        ET.parse(file_path)
        return True
    except Exception:
        return False


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    try:
        import os
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0
