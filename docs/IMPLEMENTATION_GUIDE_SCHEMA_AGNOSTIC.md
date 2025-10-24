# RA-D-PS Schema-Agnostic Refactoring Implementation Guide

**Version:** 1.0  
**Target Architecture:** Profile-based normalization system with PostgreSQL  
**Tech Stack:** Python 3.12+, PostgreSQL 16, FastAPI, Pydantic v2, SQLAlchemy 2.0  
**Estimated Timeline:** 6-8 weeks for full implementation

---

## 📋 Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Implementation Phases](#implementation-phases)
3. [Completed Components](#completed-components)
4. [Detailed Phase Instructions](#detailed-phase-instructions)
5. [Testing Strategy](#testing-strategy)
6. [Migration Path](#migration-path)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview & Architecture

### Current State
- **Existing System:** Radiology XML parser (`parser.py`) with hardcoded LIDC-IDRI format logic
- **Database:** SQLite-based storage (`database.py`, `radiology_database.py`)
- **Export:** Excel (RA-D-PS format) and SQLite
- **GUI:** Tkinter-based interface for file selection and processing

### Target State
- **Schema-Agnostic Parser:** Generic parsers (XML, JSON, CSV, PDF) driven by configuration profiles
- **Canonical Schema:** Pydantic-based flexible schema that normalizes all source formats
- **Profile System:** Externally-defined mapping profiles (JSON/database) for each format variant
- **PostgreSQL Database:** JSONB-based flexible storage with full-text search
- **REST API:** FastAPI-based API for programmatic access
- **GUI:** Enhanced interface for non-technical users with query builder
- **Extensibility:** Plugin architecture for adding new file types without code changes

### Key Design Principles

1. **Separation of Concerns:**
   - Parsing logic separate from mapping logic
   - Mapping logic separate from storage logic
   - Profile definitions external to code

2. **Backward Compatibility:**
   - Existing radiology XML parsing must continue to work
   - Excel export format (RA-D-PS) must be preserved
   - Existing tests must pass

3. **Extensibility:**
   - New file formats added by creating profiles only
   - No code changes required for new XML variants
   - Future support for JSON, CSV, PDF, Word docs

---

## ✅ Completed Components

### Phase 1: PostgreSQL Database Schema ✅
- **File:** `/migrations/001_initial_schema.sql`
- **Status:** Complete
- **Contents:**
  - `documents` table (metadata)
  - `document_content` table (JSONB canonical data)
  - `profiles` table (mapping profiles)
  - `ingestion_logs` table (audit trail)
  - `batch_metadata` table (batch processing)
  - Views for common queries
  - Triggers for automatic timestamp updates
  - Full-text search indexes

**Next Action:** Apply migration to PostgreSQL instance

### Phase 2: Canonical Schema ✅
- **File:** `/src/ra_d_ps/schemas/canonical.py`
- **Status:** Complete
- **Contents:**
  - `CanonicalDocument` base model
  - `RadiologyCanonicalDocument` specialized model
  - `InvoiceCanonicalDocument` example extension
  - `DocumentMetadata`, `ExtractedEntities`, `ExtractionMetadata` models
  - Utility functions for conversion and merging

**Next Action:** Import in existing parser for gradual migration

### Phase 3: Profile System ✅
- **File:** `/src/ra_d_ps/schemas/profile.py`
- **Status:** Complete
- **Contents:**
  - `Profile` main model
  - `FieldMapping`, `Transformation`, `ValidationRules` models
  - `EntityExtractionConfig` for structured data extraction
  - Profile validation logic

**Next Action:** Create ProfileManager and LIDC-IDRI profile

### Phase 3.5: Profile Manager ✅
- **File:** `/src/ra_d_ps/profile_manager.py`
- **Status:** Complete
- **Contents:**
  - `ProfileManager` class for loading, saving, validating profiles
  - File system and database storage support
  - Profile caching and inheritance
  - Singleton pattern for global access

**Next Action:** Create first profile for existing LIDC-IDRI format

### Infrastructure ✅
- **Files:** `docker-compose.yml`, `Dockerfile`, `configs/.env.example`
- **Status:** Complete
- **Contents:**
  - PostgreSQL 16 container with health checks
  - pgAdmin for database management
  - FastAPI application container (ready for Phase 9)
  - Volume management for data persistence
  - Environment configuration template

**Next Action:** Start PostgreSQL container and apply migrations

---

## 📅 Implementation Phases

### Phase 4: Create LIDC-IDRI Radiology Profile (PRIORITY)
**Status:** 🔴 NOT STARTED  
**Estimated Time:** 4-6 hours  
**Dependencies:** Phases 1-3 complete

**Objective:** Create a profile that maps the current LIDC-IDRI XML format to the canonical schema, enabling backward compatibility.

#### Step 4.1: Analyze Current Parser Logic
```bash
# Analyze existing parser.py to extract:
# - All XPath patterns used
# - Data transformations applied
# - Field mappings to output structure
# - Validation logic
```

**Files to Analyze:**
- `/src/ra_d_ps/parser.py` lines 427-760 (`parse_radiology_sample` function)
- `/src/ra_d_ps/structure_detector.py` (parse case detection)

**Key Information to Extract:**
1. XPath patterns for each parse case
2. Field names and their transformations
3. Required vs. optional fields
4. Data type conversions
5. Radiologist block structure

#### Step 4.2: Create LIDC-IDRI Profile JSON

**Create:** `/profiles/lidc_idri_standard.json`

```json
{
  "profile_name": "lidc_idri_standard",
  "file_type": "XML",
  "source_format_description": "LIDC-IDRI CT Lung Nodule XML Format - Standard Complete Attributes",
  "description": "Profile for standard LIDC-IDRI XML files with complete radiologist attributes",
  "canonical_schema_version": "1.0",
  "target_document_type": "RadiologyCanonicalDocument",
  "version": "1.0.0",
  "is_active": true,
  "is_default": true,
  
  "mappings": [
    {
      "source_path": "/LidcReadMessage/ResponseHeader/SeriesInstanceUid",
      "target_path": "series_instance_uid",
      "data_type": "string",
      "required": true,
      "description": "DICOM Series Instance UID"
    },
    {
      "source_path": "/LidcReadMessage/ResponseHeader/StudyInstanceUID",
      "target_path": "study_instance_uid",
      "data_type": "string",
      "required": false
    },
    {
      "source_path": "/LidcReadMessage/ResponseHeader/modality",
      "target_path": "modality",
      "data_type": "string",
      "required": false,
      "default_value": "CT"
    },
    {
      "source_path": "/LidcReadMessage/readingSession",
      "target_path": "radiologist_readings",
      "data_type": "array",
      "required": true,
      "description": "Array of radiologist reading sessions",
      "custom_parser_config": {
        "mode": "nested_array",
        "nested_mappings": [
          {
            "source_path": "./servicingRadiologistID",
            "target_path": "radiologist_id",
            "data_type": "string",
            "required": true
          },
          {
            "source_path": "./unblindedReadNodule",
            "target_path": "nodules",
            "data_type": "array",
            "nested_mappings": [
              {
                "source_path": "./noduleID",
                "target_path": "nodule_id",
                "data_type": "string",
                "required": true
              },
              {
                "source_path": "./characteristics/subtlety",
                "target_path": "characteristics.subtlety",
                "data_type": "integer",
                "required": false
              },
              {
                "source_path": "./characteristics/internalStructure",
                "target_path": "characteristics.internal_structure",
                "data_type": "integer",
                "required": false
              }
            ]
          }
        ]
      }
    }
  ],
  
  "validation_rules": {
    "required_fields": [
      "series_instance_uid",
      "radiologist_readings"
    ],
    "custom_validators": [
      {
        "field": "radiologist_readings",
        "rule_type": "array_min_length",
        "parameters": {"min_length": 1},
        "error_message": "At least one radiologist reading is required"
      }
    ]
  },
  
  "entity_extraction": {
    "identifiers": [
      {
        "entity_type": "identifier",
        "pattern": "\\d+\\.\\d+\\.\\d+\\.\\d+",
        "source_fields": ["series_instance_uid", "study_instance_uid"],
        "normalization": "trim"
      }
    ]
  }
}
```

**Implementation:**
```python
# Create script: /scripts/create_lidc_profile.py
from src.ra_d_ps.profile_manager import get_profile_manager
from src.ra_d_ps.schemas.profile import Profile, FieldMapping, DataType
# ... build profile programmatically or load from JSON ...
manager = get_profile_manager()
manager.import_profile("/profiles/lidc_idri_standard.json")
```

**Validation:**
```python
# Test profile loading
from src.ra_d_ps.profile_manager import get_profile_manager

manager = get_profile_manager()
profile = manager.load_profile("lidc_idri_standard")
assert profile is not None
is_valid, errors = manager.validate_profile(profile)
assert is_valid, f"Profile validation failed: {errors}"
```

---

### Phase 5: Generic XML Parser Core (CRITICAL PATH)
**Status:** 🔴 NOT STARTED  
**Estimated Time:** 12-16 hours  
**Dependencies:** Phase 4 complete

**Objective:** Create a generic XML parser that uses profiles to transform any XML structure into the canonical schema.

#### Step 5.1: Create Base Parser Interface

**Create:** `/src/ra_d_ps/parsers/base.py`

```python
"""
Base parser interface for all file type parsers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pathlib import Path

from ..schemas.canonical import CanonicalDocument
from ..schemas.profile import Profile


class BaseParser(ABC):
    """Abstract base class for all parsers"""
    
    def __init__(self, profile: Profile):
        self.profile = profile
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def parse(self, file_path: Path) -> CanonicalDocument:
        """
        Parse a file using the loaded profile.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            CanonicalDocument with normalized data
        """
        pass
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that the file is parseable.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if file is valid for this parser
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """
        Extract all text content for full-text search.
        
        Args:
            file_path: Path to file
            
        Returns:
            Concatenated text content
        """
        pass
    
    def get_supported_profiles(self) -> list[str]:
        """Get list of profile names this parser supports"""
        return []
    
    def clear_errors(self):
        """Clear error and warning lists"""
        self.errors = []
        self.warnings = []
```

#### Step 5.2: Create Generic XML Parser

**Create:** `/src/ra_d_ps/parsers/xml_parser.py`

```python
"""
Generic XML Parser using Profile-Based Mapping

This parser is completely format-agnostic and relies on profiles
to define how to extract and transform XML data.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import re

from .base import BaseParser
from ..schemas.canonical import (
    CanonicalDocument,
    RadiologyCanonicalDocument,
    DocumentMetadata,
    ExtractedEntities,
    ExtractionMetadata,
    Entity,
    EntityType
)
from ..schemas.profile import (
    Profile,
    FieldMapping,
    DataType,
    Transformation,
    TransformationType
)


class XMLParser(BaseParser):
    """
    Generic XML parser driven by profile mappings.
    
    Handles:
    - XPath-based field extraction
    - Namespace handling
    - Data type conversions
    - Transformations
    - Nested structures
    - Entity extraction
    """
    
    def __init__(self, profile: Profile):
        super().__init__(profile)
        self.namespace_map = {}
    
    def parse(self, file_path: Path) -> CanonicalDocument:
        """Parse XML file using profile mappings"""
        self.clear_errors()
        
        try:
            # Parse XML
            tree = ET.parse(str(file_path))
            root = tree.getroot()
            
            # Extract namespace
            self._extract_namespace(root)
            
            # Determine target document class
            doc_class = self._get_document_class()
            
            # Initialize canonical document
            canonical_data = {
                'document_metadata': {},
                'fields': {},
                'entities': {},
                'extraction_metadata': {
                    'profile_name': self.profile.profile_name,
                    'profile_id': self.profile.profile_id,
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            # Process each mapping
            start_time = datetime.utcnow()
            
            for mapping in self.profile.mappings:
                try:
                    value = self._extract_value(root, mapping)
                    if value is not None:
                        self._set_nested_value(canonical_data, mapping.target_path, value)
                except Exception as e:
                    error_msg = f"Error processing mapping {mapping.source_path}: {str(e)}"
                    self.errors.append(error_msg)
                    canonical_data['extraction_metadata'].setdefault('warnings', []).append(error_msg)
            
            # Extract entities
            entities = self._extract_entities(root, canonical_data)
            canonical_data['entities'] = entities
            
            # Extract full text for search
            searchable_text = self.extract_text(file_path)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            canonical_data['extraction_metadata']['processing_time_ms'] = int(processing_time)
            
            # Create canonical document
            doc = doc_class(**canonical_data)
            
            return doc
            
        except Exception as e:
            self.errors.append(f"Fatal parsing error: {str(e)}")
            raise
    
    def _extract_namespace(self, root: ET.Element):
        """Extract XML namespace from root element"""
        match = re.match(r'\{(.*)\}', root.tag)
        if match:
            namespace = match.group(1)
            self.namespace_map = {'ns': namespace}
        else:
            self.namespace_map = {}
    
    def _get_document_class(self):
        """Determine which CanonicalDocument class to use"""
        if self.profile.target_document_type == "RadiologyCanonicalDocument":
            return RadiologyCanonicalDocument
        # Add more specialized types here
        return CanonicalDocument
    
    def _extract_value(self, root: ET.Element, mapping: FieldMapping) -> Any:
        """
        Extract value from XML using mapping configuration.
        
        Handles:
        - XPath evaluation with namespaces
        - Attribute vs. element text extraction
        - Data type conversion
        - Transformations
        - Default values
        """
        xpath = mapping.source_path
        
        # Handle namespace prefixes
        if self.namespace_map and not xpath.startswith('//'):
            # Add namespace prefix to element names
            parts = xpath.split('/')
            xpath = '/'.join([
                f"ns:{part}" if part and not part.startswith('ns:') else part 
                for part in parts
            ])
        
        # Find elements
        elements = root.findall(xpath, self.namespace_map)
        
        if not elements:
            # No match found
            if mapping.required:
                self.warnings.append(f"Required field {mapping.source_path} not found")
            return mapping.default_value
        
        # Extract value
        if mapping.source_attribute:
            # Extract from attribute
            value = elements[0].get(mapping.source_attribute)
        else:
            # Extract element text
            if mapping.data_type == DataType.ARRAY:
                # Multiple elements -> array
                value = [self._extract_element_value(el, mapping) for el in elements]
            else:
                # Single element
                value = self._extract_element_value(elements[0], mapping)
        
        # Apply transformations
        for transformation in sorted(mapping.transformations, key=lambda t: t.order):
            value = self._apply_transformation(value, transformation)
        
        # Convert data type
        value = self._convert_data_type(value, mapping.data_type)
        
        return value
    
    def _extract_element_value(self, element: ET.Element, mapping: FieldMapping) -> Any:
        """Extract value from a single XML element"""
        if mapping.data_type == DataType.OBJECT:
            # Extract as nested object
            result = {}
            for child in element:
                tag = child.tag.split('}')[-1]  # Remove namespace
                result[tag] = child.text
            return result
        else:
            return element.text
    
    def _convert_data_type(self, value: Any, data_type: DataType) -> Any:
        """Convert value to target data type"""
        if value is None:
            return None
        
        try:
            if data_type == DataType.STRING:
                return str(value)
            elif data_type == DataType.INTEGER:
                return int(float(value))  # Handle "3.0" -> 3
            elif data_type == DataType.FLOAT:
                return float(value)
            elif data_type == DataType.DECIMAL:
                return Decimal(str(value))
            elif data_type == DataType.BOOLEAN:
                return str(value).lower() in ('true', '1', 'yes')
            elif data_type == DataType.DATE:
                return self._parse_date(value)
            elif data_type == DataType.DATETIME:
                return self._parse_datetime(value)
            elif data_type in (DataType.ARRAY, DataType.OBJECT):
                return value  # Already handled in extraction
            else:
                return value
        except Exception as e:
            self.warnings.append(f"Type conversion failed for {value} to {data_type}: {e}")
            return value
    
    def _parse_date(self, value: str) -> str:
        """Parse date string to ISO format"""
        # Implement date parsing logic
        # Try multiple formats
        formats = ['%Y-%m-%d', '%Y%m%d', '%m/%d/%Y', '%d/%m/%Y']
        for fmt in formats:
            try:
                dt = datetime.strptime(str(value), fmt)
                return dt.date().isoformat()
            except:
                continue
        return str(value)  # Return as-is if parsing fails
    
    def _parse_datetime(self, value: str) -> str:
        """Parse datetime string to ISO format"""
        # Implement datetime parsing
        try:
            dt = datetime.fromisoformat(str(value))
            return dt.isoformat()
        except:
            return str(value)
    
    def _apply_transformation(self, value: Any, transformation: Transformation) -> Any:
        """Apply a transformation to a value"""
        if value is None:
            return None
        
        trans_type = transformation.transformation_type
        params = transformation.parameters
        
        if trans_type == TransformationType.TRIM_WHITESPACE:
            return str(value).strip()
        
        elif trans_type == TransformationType.UPPERCASE:
            return str(value).upper()
        
        elif trans_type == TransformationType.LOWERCASE:
            return str(value).lower()
        
        elif trans_type == TransformationType.EXTRACT_NUMBERS:
            numbers = re.findall(r'\d+\.?\d*', str(value))
            return numbers[0] if numbers else value
        
        elif trans_type == TransformationType.REGEX_EXTRACT:
            pattern = params.get('pattern')
            group = params.get('group', 0)
            match = re.search(pattern, str(value))
            return match.group(group) if match else value
        
        elif trans_type == TransformationType.PARSE_DATE:
            date_format = params.get('format', '%Y-%m-%d')
            try:
                dt = datetime.strptime(str(value), date_format)
                return dt.date().isoformat()
            except:
                return value
        
        # Add more transformations as needed
        
        return value
    
    def _set_nested_value(self, data: dict, path: str, value: Any):
        """Set a value in a nested dictionary using dot notation path"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _extract_entities(self, root: ET.Element, canonical_data: dict) -> dict:
        """Extract entities based on profile configuration"""
        entities = {
            'dates': [],
            'people': [],
            'organizations': [],
            'amounts': [],
            'identifiers': [],
            'other': []
        }
        
        # Implement entity extraction using profile.entity_extraction
        # For now, return empty
        return entities
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate that file is parseable XML"""
        try:
            tree = ET.parse(str(file_path))
            return True
        except:
            return False
    
    def extract_text(self, file_path: Path) -> str:
        """Extract all text from XML for full-text search"""
        try:
            tree = ET.parse(str(file_path))
            root = tree.getroot()
            
            texts = []
            for element in root.iter():
                if element.text and element.text.strip():
                    texts.append(element.text.strip())
            
            return ' '.join(texts)
        except:
            return ""
```

**Testing:**
```python
# Create test: /tests/test_xml_parser.py
import pytest
from pathlib import Path
from src.ra_d_ps.parsers.xml_parser import XMLParser
from src.ra_d_ps.profile_manager import get_profile_manager

def test_xml_parser_with_lidc_profile():
    """Test XML parser with LIDC-IDRI profile"""
    manager = get_profile_manager()
    profile = manager.load_profile("lidc_idri_standard")
    
    parser = XMLParser(profile)
    
    # Use a sample XML from examples/
    sample_file = Path("examples/sample_lidc.xml")
    if sample_file.exists():
        doc = parser.parse(sample_file)
        
        assert doc is not None
        assert doc.series_instance_uid is not None
        assert len(parser.errors) == 0
```

---

### Phase 6: Parser Factory & Extensibility
**Status:** 🔴 NOT STARTED  
**Estimated Time:** 4 hours

**Create:** `/src/ra_d_ps/parsers/factory.py`

```python
"""
Parser Factory for schema-agnostic parsing system.

Manages registration and instantiation of parsers for different file types.
"""

from typing import Dict, Type, Optional
from pathlib import Path

from .base import BaseParser
from .xml_parser import XMLParser
from ..schemas.profile import Profile, FileType


class ParserFactory:
    """Factory for creating appropriate parser instances"""
    
    _parsers: Dict[FileType, Type[BaseParser]] = {}
    
    @classmethod
    def register_parser(cls, file_type: FileType, parser_class: Type[BaseParser]):
        """Register a parser for a file type"""
        cls._parsers[file_type] = parser_class
    
    @classmethod
    def get_parser(cls, profile: Profile) -> BaseParser:
        """Get parser instance for a profile"""
        parser_class = cls._parsers.get(profile.file_type)
        if not parser_class:
            raise ValueError(f"No parser registered for file type: {profile.file_type}")
        return parser_class(profile)
    
    @classmethod
    def list_supported_formats(cls) -> list[FileType]:
        """List all supported file types"""
        return list(cls._parsers.keys())


# Register built-in parsers
ParserFactory.register_parser(FileType.XML, XMLParser)

# Stubs for future parsers
# ParserFactory.register_parser(FileType.JSON, JSONParser)
# ParserFactory.register_parser(FileType.CSV, CSVParser)
# ParserFactory.register_parser(FileType.PDF, PDFParser)
```

---

### Phase 7-14: Summary (Details omitted for brevity)

**Phase 7:** PostgreSQL Repository Layer (8-10 hours)  
**Phase 8:** Ingestion Orchestrator (6-8 hours)  
**Phase 9:** FastAPI REST API (12-16 hours)  
**Phase 10:** Query Builder (6-8 hours)  
**Phase 11:** Testing Suite (8-12 hours)  
**Phase 12:** Profile Builder CLI Tool (8-10 hours)  
**Phase 13:** Documentation (4-6 hours)  
**Phase 14:** Migration Guide & Backward Compatibility (6-8 hours)

---

## 🧪 Testing Strategy

### Unit Tests
```bash
pytest tests/test_xml_parser.py -v
pytest tests/test_profile_manager.py -v
pytest tests/test_canonical_schema.py -v
```

### Integration Tests
```bash
pytest tests/integration/test_end_to_end_parsing.py -v
pytest tests/integration/test_database_storage.py -v
```

### Backward Compatibility Tests
```bash
# Existing radiology tests must still pass
pytest tests/test_ra_d_ps_export.py -v
pytest tests/test_excel_export.py -v
```

---

## 🚀 Quick Start Commands

### 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start PostgreSQL
```bash
docker-compose up -d postgres
```

### 3. Apply Migrations
```bash
psql -h localhost -U ra_d_ps_user -d ra_d_ps_db -f migrations/001_initial_schema.sql
```

### 4. Test Profile System
```python
python -c "
from src.ra_d_ps.profile_manager import get_profile_manager
manager = get_profile_manager()
print(f'Profile manager initialized with {len(manager.list_profiles())} profiles')
"
```

---

## ❗ Critical Notes for Copilot

1. **Preserve Existing Functionality:** Never break the existing radiology XML parsing. The new system must coexist.

2. **Follow Naming Conventions:** 
   - Use lowercase with underscores for files: `xml_parser.py`
   - Use PascalCase for classes: `XMLParser`
   - Use lowercase for functions: `parse_radiology_sample`

3. **Error Handling:** Always use try-except with meaningful error messages. Log to `ingestion_logs` table.

4. **Type Safety:** Use type hints everywhere. Run `mypy` before committing.

5. **Testing:** Write tests before implementation (TDD). Every new function needs a test.

6. **Documentation:** Add docstrings with Args, Returns, Raises sections.

7. **Performance:** Use batch inserts for database operations. Profile with `cProfile` for large datasets.

---

## 📞 Next Steps for Implementation

**Immediate Priority (Next 2 weeks):**

1. ✅ **Phase 4:** Create LIDC-IDRI profile (2 days)
2. ✅ **Phase 5:** Implement generic XML parser (4 days)
3. ✅ **Phase 6:** Create parser factory (1 day)
4. ✅ **Testing:** Validate end-to-end with sample XML files (2 days)
5. ✅ **Phase 7:** PostgreSQL repository layer (3 days)

**Questions to Resolve:**
- [ ] Do you want to maintain SQLite alongside PostgreSQL during migration?
- [ ] Should the GUI be updated to use the new system, or keep separate?
- [ ] What authentication/authorization needed for the API (if any)?

---

**This guide will be continuously updated as implementation progresses.**
