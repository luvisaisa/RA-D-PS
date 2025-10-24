"""
Base parser interface for RA-D-PS

Defines the abstract interface that all parsers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

from ..schemas.canonical import CanonicalDocument


class BaseParser(ABC):
    """
    Abstract base class for all document parsers.
    
    All parsers must implement these core methods to ensure consistent
    behavior across different document formats.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parser with optional configuration.
        
        Args:
            config: Parser-specific configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        Determine if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate that the file is well-formed and parseable.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file is valid, False otherwise
            - error_message: Description of validation error if any, None if valid
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> CanonicalDocument:
        """
        Parse the file and return a canonical document representation.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            CanonicalDocument instance containing parsed data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or cannot be parsed
            Exception: For other parsing errors
        """
        pass
    
    def parse_batch(self, file_paths: list[str]) -> list[CanonicalDocument]:
        """
        Parse multiple files in batch.
        
        Default implementation calls parse() for each file. Subclasses
        can override for optimized batch processing.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of CanonicalDocument instances
        """
        results = []
        for file_path in file_paths:
            try:
                doc = self.parse(file_path)
                results.append(doc)
            except Exception as e:
                # Log error but continue processing other files
                print(f"Error parsing {file_path}: {e}")
                continue
        return results
    
    def _validate_file_exists(self, file_path: str) -> None:
        """
        Helper method to validate file existence.
        
        Args:
            file_path: Path to check
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def _validate_file_readable(self, file_path: str) -> None:
        """
        Helper method to validate file is readable.
        
        Args:
            file_path: Path to check
            
        Raises:
            PermissionError: If file cannot be read
        """
        path = Path(file_path)
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        if not path.stat().st_size > 0:
            raise ValueError(f"File is empty: {file_path}")


class ParserError(Exception):
    """Base exception for parser-related errors"""
    pass


class ValidationError(ParserError):
    """Raised when document validation fails"""
    pass


class ParseError(ParserError):
    """Raised when parsing fails"""
    pass
