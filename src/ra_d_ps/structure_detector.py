"""
Structure Detection Module for RA-D-PS XML Parsing

This module provides intelligent XML structure detection and parse case determination
for batch processing of radiology annotation files. It separates the structure
analysis logic from the core parsing engine for better maintainability.

Version 3.0: Pure database-driven parse case detection (PostgreSQL required)
- All parse case definitions stored in PostgreSQL database
- In-memory caching for performance optimization
- No hardcoded fallback logic - database connection required
- Detection history and statistics tracking
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional database support
try:
    from src.ra_d_ps.database import ParseCaseRepository
    from src.ra_d_ps.database.models import ParseCase
    DATABASE_AVAILABLE = True
except ImportError:
    logger.error("Database module not available. Pure DB-driven detection requires database module.")
    DATABASE_AVAILABLE = False


@dataclass
class ParseCaseCache:
    """Cache entry for parse cases with TTL"""
    parse_cases: List
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes default
    
    def is_expired(self) -> bool:
        """Check if cache has expired"""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)


class XMLStructureDetector:
    """
    Intelligent XML structure detector for radiology annotation files.
    
    Version 2.0: Database-driven with in-memory caching for performance
    
    This class analyzes XML files to determine their structure type (parse case)
    without fully parsing them, enabling efficient batch processing and
    appropriate parsing strategy selection.
    
    Features:
    - Pure database-driven parse case definitions (PostgreSQL)
    - In-memory caching with configurable TTL (default 5 minutes)
    - Detection history tracking for analytics
    - No hardcoded fallback logic - all parse cases must be in database
    """
    
    # Standard characteristic fields to check for (legacy format)
    CHARACTERISTIC_FIELDS = ['confidence', 'subtlety', 'obscuration', 'reason']
    
    # LIDC v2 characteristic fields (modern format)
    LIDC_V2_FIELDS = ['subtlety', 'malignancy', 'internalStructure', 'calcification', 
                      'sphericity', 'margin', 'lobulation', 'spiculation', 'texture']
    
    def __init__(self, use_database: bool = True, cache_ttl: int = 300):
        """
        Initialize the structure detector (pure DB-driven mode).
        
        Args:
            use_database: Must be True (kept for API compatibility)
            cache_ttl: Time-to-live for cache in seconds (default 300 = 5 minutes)
            
        Raises:
            ImportError: If database module is not available
            RuntimeError: If database connection fails
        """
        if not DATABASE_AVAILABLE:
            raise ImportError(
                "Database module not available. Pure DB-driven detection requires "
                "PostgreSQL connection and database module."
            )
        
        self.detection_cache = {}  # Cache results for performance
        self.use_database = True  # Always True in pure DB mode
        self.cache_ttl = cache_ttl
        self._parse_case_cache: Optional[ParseCaseCache] = None
        self._repository: Optional[ParseCaseRepository] = None
        
        # Initialize database connection (required)
        try:
            self._repository = ParseCaseRepository()
            logger.info("Structure detector initialized with database connection (pure DB-driven mode)")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}")
    
    def _get_parse_cases_from_db(self) -> List:
        """
        Get parse cases from database with caching.
        
        Returns:
            List of ParseCase objects sorted by priority (descending)
        """
        # Check if cache exists and is valid
        if self._parse_case_cache and not self._parse_case_cache.is_expired():
            return self._parse_case_cache.parse_cases
        
        # Fetch from database
        try:
            parse_cases = self._repository.get_all_parse_cases()
            
            # Update cache
            self._parse_case_cache = ParseCaseCache(
                parse_cases=parse_cases,
                timestamp=datetime.now(),
                ttl_seconds=self.cache_ttl
            )
            
            logger.debug(f"Loaded {len(parse_cases)} parse cases from database (cached for {self.cache_ttl}s)")
            return parse_cases
            
        except Exception as e:
            logger.error(f"Failed to load parse cases from database: {e}")
            # Return empty list on error
            return []
    
    def _match_parse_case_from_db(self, header_info: Dict, session_info: Dict, 
                                   char_info: Dict) -> Optional[str]:
        """
        Match XML structure against database parse cases.
        
        Args:
            header_info: Header analysis results
            session_info: Session analysis results
            char_info: Characteristics analysis results
            
        Returns:
            Parse case name if matched, None otherwise
        """
        parse_cases = self._get_parse_cases_from_db()
        
        if not parse_cases:
            return None
        
        # Extract detection features
        char_count = char_info['count']
        has_reason = char_info['has_reason']
        session_count = session_info['count']
        header_present = header_info['present']
        header_complete = header_info['complete']
        has_modality = header_info['has_modality']
        available_chars = set(char_info['available'])
        is_v2_format = char_info.get('is_v2_format', False)
        v2_chars = set(char_info.get('v2_chars', []))
        v2_count = char_info.get('v2_count', 0)
        
        # Try each parse case in priority order
        for parse_case in parse_cases:
            if not parse_case.is_active:
                continue
            
            criteria = parse_case.detection_criteria
            
            # Check v2 format first (high priority)
            if criteria.get('v2_fields'):
                required_v2_fields = set(criteria['v2_fields'])
                min_v2_count = criteria.get('min_v2_count', 5)
                
                # Check if we have enough v2 fields
                if v2_count >= min_v2_count:
                    # Check if required v2 fields are present
                    if criteria.get('expected_fields'):
                        required_fields = set(criteria['expected_fields'])
                        if required_fields.issubset(v2_chars):
                            return parse_case.name
                    else:
                        return parse_case.name
            
            # Check session count criteria
            if 'session_count' in criteria:
                if session_count == criteria['session_count']:
                    return parse_case.name
            
            # Check characteristic count criteria
            min_chars = criteria.get('min_chars')
            max_chars = criteria.get('max_chars')
            
            if min_chars is not None:
                if char_count < min_chars:
                    continue
            
            if max_chars is not None:
                if char_count > max_chars:
                    continue
            
            # Check reason requirement
            if criteria.get('requires_reason', False):
                if not has_reason:
                    continue
            
            # Check header requirements
            if criteria.get('requires_header', False):
                if not header_present:
                    continue
            
            # Check modality requirement
            if criteria.get('requires_modality', False):
                if not has_modality:
                    continue
            
            # Check required characteristics
            if criteria.get('required_chars'):
                required = set(criteria['required_chars'])
                if not required.issubset(available_chars):
                    continue
            
            # Check expected fields
            if criteria.get('expected_fields') and not criteria.get('v2_fields'):
                expected = set(criteria['expected_fields'])
                if not expected.issubset(available_chars):
                    continue
            
            # All criteria matched
            return parse_case.name
        
        # No match found
        return None
        
    def detect_structure_type(self, file_path: str, record_detection: bool = True) -> str:
        """
        Detect the XML structure type (parse case) for a given file.
        
        Args:
            file_path: Path to the XML file to analyze
            record_detection: If True and database is enabled, record detection in history
            
        Returns:
            String identifier for the detected parse case
        """
        # Check cache first
        if file_path in self.detection_cache:
            return self.detection_cache[file_path]
            
        start_time = datetime.now()
        
        try:
            parse_case = self._analyze_xml_structure(file_path)
            self.detection_cache[file_path] = parse_case
            
            # Record detection in database if enabled
            if record_detection and self.use_database and self._repository:
                try:
                    detection_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    # Get parse case from database to get ID
                    db_parse_case = self._repository.get_parse_case_by_name(parse_case)
                    if db_parse_case:
                        self._repository.record_detection(
                            parse_case_id=db_parse_case.id,
                            file_path=file_path,
                            detection_metadata={
                                "detection_time_ms": detection_time_ms,
                                "cache_hit": False,
                                "database_driven": True
                            }
                        )
                        
                        # Update statistics
                        self._repository.update_statistics(
                            parse_case_id=db_parse_case.id,
                            detection_time_ms=detection_time_ms,
                            success=True
                        )
                except Exception as e:
                    logger.debug(f"Failed to record detection in database: {e}")
            
            return parse_case
            
        except Exception as e:
            logger.error(f"Error detecting structure for {file_path}: {e}")
            return "XML_Parse_Error"
    
    def _analyze_xml_structure(self, file_path: str) -> str:
        """
        Internal method to analyze XML structure and determine parse case.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            Parse case identifier string
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Extract namespace if present
        namespace = self._extract_namespace(root)
        
        # Analyze key structural elements
        header_info = self._analyze_header(root, namespace)
        session_info = self._analyze_sessions(root, namespace)
        char_info = self._analyze_characteristics(root, namespace)
        
        # Apply classification logic
        return self._classify_structure(header_info, session_info, char_info)
    
    def _extract_namespace(self, root) -> str:
        """Extract namespace URI from root element."""
        match = re.match(r'\{(.*)\}', root.tag)
        return match.group(1) if match else ''
    
    def _make_tag(self, name: str, namespace: str) -> str:
        """Create namespaced tag if namespace exists."""
        return f"{{{namespace}}}{name}" if namespace else name
    
    def _analyze_header(self, root, namespace: str) -> Dict:
        """Analyze header completeness and content."""
        tag = lambda name: self._make_tag(name, namespace)
        header = root.find(tag('ResponseHeader'))
        
        if header is None:
            return {
                'present': False,
                'has_modality': False,
                'complete': False
            }
        
        modality_elem = header.find(tag('Modality'))
        has_modality = modality_elem is not None and modality_elem.text
        
        # Check for other important header fields
        required_fields = ['StudyInstanceUID', 'SeriesInstanceUID']
        field_count = sum(1 for field in required_fields 
                         if header.find(tag(field)) is not None)
        
        return {
            'present': True,
            'has_modality': has_modality,
            'complete': field_count >= len(required_fields),
            'field_count': field_count
        }
    
    def _analyze_sessions(self, root, namespace: str) -> Dict:
        """Analyze reading sessions structure."""
        tag = lambda name: self._make_tag(name, namespace)
        
        sessions = (root.findall(tag('readingSession')) or 
                   root.findall(tag('CXRreadingSession')))
        
        session_count = len(sessions)
        
        return {
            'count': session_count,
            'present': session_count > 0,
            'sessions': sessions[:1] if sessions else []  # Keep first for analysis
        }
    
    def _analyze_characteristics(self, root, namespace: str) -> Dict:
        """Analyze characteristics availability across sessions."""
        tag = lambda name: self._make_tag(name, namespace)
        
        sessions = (root.findall(tag('readingSession')) or 
                   root.findall(tag('CXRreadingSession')))
        
        if not sessions:
            return {
                'available': [],
                'count': 0,
                'has_reason': False
            }
        
        # Analyze first session's first read
        first_session = sessions[0]
        unblinded_reads = (first_session.findall(tag('unblindedReadNodule')) or 
                          first_session.findall(tag('unblindedRead')))
        
        if not unblinded_reads:
            return {
                'available': [],
                'count': 0,
                'has_reason': False
            }
        
        first_read = unblinded_reads[0]
        characteristics = first_read.find(tag('characteristics'))
        
        if characteristics is None:
            return {
                'available': [],
                'count': 0,
                'has_reason': False,
                'is_v2_format': False,
                'v2_chars': []
            }
        
        # Check which characteristics are available (legacy format)
        available_chars = []
        for field in self.CHARACTERISTIC_FIELDS:
            elem = characteristics.find(tag(field))
            if elem is not None and elem.text:
                available_chars.append(field)
        
        # Check for LIDC v2 format characteristics
        v2_chars = []
        for field in self.LIDC_V2_FIELDS:
            elem = characteristics.find(tag(field))
            if elem is not None and elem.text:
                v2_chars.append(field)
        
        is_v2_format = len(v2_chars) >= 5  # v2 format has many more fields
        
        return {
            'available': available_chars,
            'count': len(available_chars),
            'has_reason': 'reason' in available_chars,
            'is_v2_format': is_v2_format,
            'v2_chars': v2_chars,
            'v2_count': len(v2_chars)
        }
    
    def _classify_structure(self, header_info: Dict, session_info: Dict, 
                          char_info: Dict) -> str:
        """
        Apply classification logic to determine parse case (pure DB-driven).
        
        All parse case logic is stored in the database. No hardcoded fallback.
        
        Args:
            header_info: Header analysis results
            session_info: Session analysis results  
            char_info: Characteristics analysis results
            
        Returns:
            Parse case identifier from database
        """
        db_match = self._match_parse_case_from_db(header_info, session_info, char_info)
        
        if db_match:
            logger.debug(f"Matched parse case from database: {db_match}")
            return db_match
        else:
            logger.error("No parse case matched in database. Check parse case definitions and detection criteria.")
            return "Unknown_Structure"
    
    def batch_detect_structures(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Detect structures for a batch of files efficiently.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Dictionary mapping file paths to their parse cases
        """
        results = {}
        total_files = len(file_paths)
        
        logger.info(f"🔍 Starting structure detection for {total_files} files...")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                parse_case = self.detect_structure_type(file_path)
                results[file_path] = parse_case
                
                if i % 10 == 0 or i == total_files:
                    logger.info(f"🔍 Structure detection progress: {i}/{total_files}")
                    
            except Exception as e:
                logger.error(f"Failed to detect structure for {file_path}: {e}")
                results[file_path] = "XML_Parse_Error"
        
        # Print summary
        case_counts = {}
        for case in results.values():
            case_counts[case] = case_counts.get(case, 0) + 1
            
        logger.info("📊 Structure Detection Summary:")
        for case, count in sorted(case_counts.items()):
            logger.info(f"  {case}: {count} files")
        
        return results
    
    def get_parse_case_info(self, parse_case: str) -> Dict:
        """
        Get detailed information about a specific parse case from database.
        
        Args:
            parse_case: Parse case identifier
            
        Returns:
            Dictionary with parse case information from database
        """
        try:
            db_case = self._repository.get_parse_case_by_name(parse_case)
            if db_case:
                return {
                    "name": db_case.name,
                    "description": db_case.description,
                    "version": db_case.version,
                    "format_type": db_case.format_type,
                    "detection_priority": db_case.detection_priority,
                    "min_chars": db_case.detection_criteria.get("min_chars", 0),
                    "characteristic_fields": db_case.characteristic_fields or [],
                    "is_legacy_format": db_case.is_legacy_format,
                    "detection_criteria": db_case.detection_criteria
                }
        except Exception as e:
            logger.debug(f"Failed to get parse case info from database: {e}")
        
        # Return minimal info if not found
        return {
            "description": "Unknown or custom parse case",
            "min_chars": 0
        }
    
    def close(self):
        """
        Close database connection and cleanup resources.
        Should be called when detector is no longer needed.
        """
        if self._repository:
            try:
                self._repository.close()
                logger.debug("Closed database connection")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        
        # Clear caches
        self.detection_cache.clear()
        self._parse_case_cache = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.close()
        return False
    
    def refresh_cache(self):
        """
        Force refresh of parse case cache from database.
        Useful after database updates.
        """
        if self.use_database:
            self._parse_case_cache = None
            logger.info("Parse case cache cleared, will refresh on next detection")
    
    def validate_batch_consistency(self, file_paths: List[str]) -> Dict:
        """
        Validate that a batch of files has consistent structure types.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            Dictionary with consistency analysis results
        """
        structure_map = self.batch_detect_structures(file_paths)
        
        # Count occurrences of each structure type
        case_counts = {}
        for case in structure_map.values():
            case_counts[case] = case_counts.get(case, 0) + 1
        
        total_files = len(file_paths)
        most_common_case = max(case_counts.items(), key=lambda x: x[1])
        consistency_ratio = most_common_case[1] / total_files
        
        return {
            'total_files': total_files,
            'unique_structures': len(case_counts),
            'case_distribution': case_counts,
            'most_common_case': most_common_case[0],
            'most_common_count': most_common_case[1],
            'consistency_ratio': consistency_ratio,
            'is_highly_consistent': consistency_ratio >= 0.8,
            'structure_map': structure_map
        }


# Convenience functions for backward compatibility
def detect_parse_case(file_path: str) -> str:
    """
    Convenience function for single file structure detection.
    Maintains compatibility with existing parser.py code.
    
    Args:
        file_path: Path to XML file
        
    Returns:
        Parse case identifier string
    """
    detector = XMLStructureDetector()
    return detector.detect_structure_type(file_path)


def batch_detect_parse_cases(file_paths: List[str]) -> Dict[str, str]:
    """
    Convenience function for batch structure detection.
    
    Args:
        file_paths: List of file paths
        
    Returns:
        Dictionary mapping file paths to parse cases
    """
    detector = XMLStructureDetector()
    return detector.batch_detect_structures(file_paths)


if __name__ == "__main__":
    # Example usage and testing
    import sys
    
    if len(sys.argv) > 1:
        detector = XMLStructureDetector()
        
        for file_path in sys.argv[1:]:
            if Path(file_path).exists():
                parse_case = detector.detect_structure_type(file_path)
                case_info = detector.get_parse_case_info(parse_case)
                print(f"\nFile: {file_path}")
                print(f"Parse Case: {parse_case}")
                print(f"Description: {case_info.get('description', 'N/A')}")
            else:
                print(f"File not found: {file_path}")
    else:
        print("Usage: python structure_detector.py <xml_file1> [xml_file2] ...")