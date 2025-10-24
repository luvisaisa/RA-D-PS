# Phase 4: Generic XML Parser Core - Implementation Plan

## Objective
Refactor parser.py into a generic XMLParser class that:
1. Consumes profiles from the profile system (Phase 3)
2. Outputs canonical schema (Phase 2)
3. Preserves backward compatibility with existing radiology parsing
4. Enables future extensibility for different XML formats

## Architecture

### New Components

#### 1. Base Parser Interface (`/src/ra_d_ps/parsers/base.py`)
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> CanonicalDocument
    
    @abstractmethod
    def validate(self, file_path: str) -> bool
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool
```

#### 2. Generic XML Parser (`/src/ra_d_ps/parsers/xml_parser.py`)
```python
class XMLParser(BaseParser):
    def __init__(self, profile: Profile):
        self.profile = profile
    
    def parse(self, file_path: str) -> RadiologyCanonicalDocument:
        # Profile-driven parsing
        # Extract data based on profile.field_mappings
        # Return canonical schema instance
    
    def _extract_with_xpath(self, tree, xpath_expr):
        # Helper for XPath-based extraction
    
    def _apply_transformations(self, value, transforms):
        # Apply profile-defined transformations
```

#### 3. Legacy Wrapper (`/src/ra_d_ps/parsers/legacy_radiology.py`)
```python
class LegacyRadiologyParser:
    """Wrapper for backward compatibility with existing parser.py"""
    
    def __init__(self):
        self.xml_parser = XMLParser(self._get_default_profile())
    
    def parse_radiology_sample(self, file_path):
        # Convert canonical output to old DataFrame format
        canonical = self.xml_parser.parse(file_path)
        return self._to_legacy_format(canonical)
```

## Implementation Steps

### Step 1: Create Parser Module Structure
- Create `/src/ra_d_ps/parsers/` directory
- Create `__init__.py`
- Create `base.py` with BaseParser interface

### Step 2: Implement Generic XMLParser
- Create `xml_parser.py`
- Implement profile-driven parsing logic
- Support XPath extraction
- Support profile transformations
- Output RadiologyCanonicalDocument

### Step 3: Create Legacy Wrapper
- Create `legacy_radiology.py`
- Wrap XMLParser
- Convert canonical schema back to old DataFrame format
- Ensure 100% backward compatibility

### Step 4: Update Existing parser.py
- Import legacy wrapper
- Redirect parse_radiology_sample() to wrapper
- Maintain all existing function signatures
- Add deprecation warnings (optional)

### Step 5: Testing
- Verify all existing tests pass
- Test with XML-COMP dataset
- Compare outputs: old vs new parser
- Ensure DataFrame formats match exactly

### Step 6: Documentation
- Document new parser architecture
- Migration guide for users
- Examples using canonical schema directly

## Profile Integration

The XMLParser will consume profiles like:

```json
{
  "profile_id": "lidc_idri_radiology",
  "name": "LIDC-IDRI Radiology XML",
  "version": "1.0",
  "document_type": "radiology",
  "source_format": "xml",
  "field_mappings": {
    "study_uid": {
      "xpath": "//StudyInstanceUID",
      "type": "string"
    },
    "series_uid": {
      "xpath": "//SeriesInstanceUid",
      "type": "string"
    },
    "nodules": {
      "xpath": "//unblindedReadNodule",
      "type": "array",
      "item_mappings": {
        "nodule_id": {
          "xpath": "./noduleID",
          "type": "integer"
        },
        "characteristics": {
          "subtlety": "./characteristics/subtlety",
          "malignancy": "./characteristics/malignancy"
        }
      }
    }
  }
}
```

## Backward Compatibility Strategy

### Old API (preserved):
```python
from src.ra_d_ps.parser import parse_radiology_sample

main_df, unblinded_df = parse_radiology_sample(file_path)
```

### New API (added):
```python
from src.ra_d_ps.parsers import XMLParser
from src.ra_d_ps.profile_manager import ProfileManager

profile = ProfileManager.get_profile("lidc_idri_radiology")
parser = XMLParser(profile)
canonical_doc = parser.parse(file_path)
```

## Success Criteria

1. All existing tests pass without modification
2. XML-COMP dataset parses correctly
3. Output DataFrames match existing format exactly
4. New canonical schema output is also available
5. Profile system is fully integrated
6. Code is cleaner and more maintainable
7. Future XML formats can be added via profiles only

## Timeline

- Step 1-2: 2-3 hours (core parser implementation)
- Step 3: 1 hour (legacy wrapper)
- Step 4: 30 minutes (integration)
- Step 5: 1-2 hours (comprehensive testing)
- Step 6: 30 minutes (documentation)

**Total Estimated Time**: 5-7 hours

## Dependencies

- Phase 1: PostgreSQL schema (complete)
- Phase 2: Canonical schema (complete)
- Phase 3: Profile system (complete)
- pylidc integration (complete, optional)

## Next Phase Preview

After Phase 4 completion:
- **Phase 5**: Create the actual LIDC-IDRI profile JSON
- **Phase 6**: Build ingestion orchestrator using the new parser
- **Phase 7**: Connect to PostgreSQL via repository pattern

---

**Status**: Ready to implement  
**Risk Level**: Low (backward compatibility maintained)  
**Impact**: High (enables all future phases)
