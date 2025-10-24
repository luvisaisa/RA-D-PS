"""
Parser module for RA-D-PS

This module provides a generic, profile-driven parsing system that converts
various document formats into canonical schema representations.

Components:
- BaseParser: Abstract interface for all parsers
- XMLParser: Profile-driven XML parser
- LegacyRadiologyParser: Backward compatibility wrapper
"""

from .base import BaseParser
from .xml_parser import XMLParser
from .legacy_radiology import LegacyRadiologyParser

__all__ = [
    'BaseParser',
    'XMLParser',
    'LegacyRadiologyParser',
]
