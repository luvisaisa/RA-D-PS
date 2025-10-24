"""
Adapters for Various Data Sources

This module provides adapters to convert various data sources
(pylidc, custom XML, JSON, etc.) into the canonical schema format.
"""

from .pylidc_adapter import PyLIDCAdapter

__all__ = ['PyLIDCAdapter']
