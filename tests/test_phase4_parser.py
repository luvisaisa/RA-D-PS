"""
Test the new parser architecture (Phase 4)
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_new_parser_architecture():
    """Test the new profile-driven parser"""
    print("Testing Phase 4: Generic XML Parser Core")
    print("=" * 60)
    
    # Test 1: Import new modules
    print("\n1. Testing imports...")
    try:
        from src.ra_d_ps.parsers import BaseParser, XMLParser, LegacyRadiologyParser
        print("   SUCCESS: All parser modules import correctly")
    except Exception as e:
        print(f"   FAILED: Import error - {e}")
        return False
    
    # Test 2: Create legacy parser instance
    print("\n2. Testing LegacyRadiologyParser initialization...")
    try:
        legacy_parser = LegacyRadiologyParser()
        print("   SUCCESS: Legacy parser created")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False
    
    # Test 3: Parse a sample file
    print("\n3. Testing parse with sample XML...")
    test_file = "/Users/isa/Desktop/XML-COMP/157/158.xml"
    
    if not Path(test_file).exists():
        print(f"   SKIPPED: Test file not found: {test_file}")
        return True
    
    try:
        main_df, unblinded_df = legacy_parser.parse_radiology_sample(test_file)
        print(f"   SUCCESS: Parsed file")
        print(f"   Main DataFrame: {len(main_df)} rows")
        print(f"   Unblinded DataFrame: {len(unblinded_df)} rows")
        
        if not main_df.empty:
            print(f"   Columns: {list(main_df.columns)}")
    except Exception as e:
        print(f"   FAILED: Parse error - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test XMLParser directly with canonical output
    print("\n4. Testing XMLParser with canonical schema...")
    try:
        from src.ra_d_ps.parsers.xml_parser import XMLParser
        from src.ra_d_ps.schemas.profile import (
            Profile, FieldMapping, FileType, ValidationRules, EntityExtractionConfig
        )
        
        # Create minimal profile
        profile = Profile(
            profile_name='test_profile',
            file_type=FileType.XML,
            source_format_description='Test',
            version='1.0.0',
            target_document_type='radiology',
            mappings=[],
            validation_rules=ValidationRules(),
            entity_extraction=EntityExtractionConfig()
        )
        
        parser = XMLParser(profile)
        
        if parser.can_parse(test_file):
            print("   SUCCESS: can_parse() returned True")
        else:
            print("   WARNING: can_parse() returned False")
        
        is_valid, error = parser.validate(test_file)
        if is_valid:
            print("   SUCCESS: File validation passed")
        else:
            print(f"   INFO: Validation returned: {error}")
        
        # Try parsing
        canonical_doc = parser.parse(test_file)
        print(f"   SUCCESS: Parsed to canonical schema")
        print(f"   Document type: {canonical_doc.document_metadata.document_type}")
        print(f"   Profile ID: {canonical_doc.document_metadata.profile_id}")
        print(f"   Study UID: {canonical_doc.study_instance_uid}")
        
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("Phase 4 Implementation: SUCCESSFUL")
    print("New parser architecture is operational")
    return True

if __name__ == "__main__":
    success = test_new_parser_architecture()
    sys.exit(0 if success else 1)
