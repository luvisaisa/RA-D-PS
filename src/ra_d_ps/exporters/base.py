"""
Base exporter interface for RA-D-PS export system.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class ExportError(Exception):
    """Raised when export operation fails"""
    pass


class BaseExporter(ABC):
    """
    Abstract base class for all exporters.
    
    Provides common functionality and defines the interface
    that all exporters must implement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize exporter with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.export_timestamp = datetime.now()
    
    @abstractmethod
    def export(self, data: Any, output_path: Path, **kwargs) -> Path:
        """
        Export data to specified output path.
        
        Args:
            data: Data to export (format depends on exporter)
            output_path: Path where output should be written
            **kwargs: Additional exporter-specific options
            
        Returns:
            Path to exported file
            
        Raises:
            ExportError: If export fails
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """
        Validate that data is in correct format for this exporter.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid
            
        Raises:
            ExportError: If data is invalid
        """
        pass
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename by replacing invalid characters.
        
        Args:
            name: Original filename
            
        Returns:
            Sanitized filename safe for all platforms
        """
        import re
        return re.sub(r'[^A-Za-z0-9_\-]+', '_', name.strip())
    
    def _get_timestamp(self) -> str:
        """
        Get formatted timestamp for filenames.
        
        Returns:
            Timestamp string in format YYYY-MM-DD_HHMMSS
        """
        return self.export_timestamp.strftime("%Y-%m-%d_%H%M%S")
    
    def _next_versioned_path(self, base_path: Path) -> Path:
        """
        Get next available versioned path if file exists.
        
        Appends _v2, _v3, etc. until unused filename found.
        
        Args:
            base_path: Original desired path
            
        Returns:
            Available path (original or versioned)
        """
        if not base_path.exists():
            return base_path
        
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        version = 2
        while True:
            versioned_path = parent / f"{stem}_v{version}{suffix}"
            if not versioned_path.exists():
                return versioned_path
            version += 1
