"""
Validation Tests for Schema-Agnostic Foundation
Run these tests to verify Phases 1-3 are working correctly before proceeding.

Usage:
    python3 tests/test_foundation_validation.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all new modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.ra_d_ps.schemas.canonical import (
            CanonicalDocument,
            RadiologyCanonicalDocument,
            DocumentMetadata,
            ExtractedEntities,
            Entity,
            EntityType
        )
        print("  ✅ Canonical schema imports successfully")
    except Exception as e:
        print(f"  ❌ Canonical schema import failed: {e}")
        return False
    
    try:
        from src.ra_d_ps.schemas.profile import (
            Profile,
            FieldMapping,
            DataType,
            FileType,
            Transformation,
            TransformationType
        )
        print("  ✅ Profile schema imports successfully")
    except Exception as e:
        print(f"  ❌ Profile schema import failed: {e}")
        return False
    
    try:
        from src.ra_d_ps.profile_manager import ProfileManager, get_profile_manager
        print("  ✅ Profile manager imports successfully")
    except Exception as e:
        print(f"  ❌ Profile manager import failed: {e}")
        return False
    
    return True


def test_canonical_schema():
    """Test canonical schema creation and validation"""
    print("\n🧪 Testing canonical schema...")
    
    from src.ra_d_ps.schemas.canonical import (
        CanonicalDocument,
        RadiologyCanonicalDocument,
        DocumentMetadata,
        ExtractedEntities,
        Entity,
        EntityType,
        canonical_to_dict
    )
    
    # Test basic document creation
    try:
        doc = CanonicalDocument(
            document_metadata=DocumentMetadata(
                title="Test Document",
                date=datetime.now(),
                author="Test Author"
            ),
            fields={
                "custom_field": "test_value",
                "number_field": 42
            }
        )
        print("  ✅ Basic CanonicalDocument creation works")
    except Exception as e:
        print(f"  ❌ CanonicalDocument creation failed: {e}")
        return False
    
    # Test radiology document
    try:
        rad_doc = RadiologyCanonicalDocument(
            document_metadata=DocumentMetadata(
                title="CT Scan Report",
                date=datetime.now()
            ),
            study_instance_uid="1.2.3.4.5",
            modality="CT",
            nodules=[
                {
                    "nodule_id": "1",
                    "location": {"x": 100, "y": 200, "z": 50}
                }
            ]
        )
        assert rad_doc.document_metadata.document_type == "radiology_report"
        print("  ✅ RadiologyCanonicalDocument creation works")
        print(f"     Document type auto-set to: {rad_doc.document_metadata.document_type}")
    except Exception as e:
        print(f"  ❌ RadiologyCanonicalDocument creation failed: {e}")
        return False
    
    # Test entity extraction
    try:
        entities = ExtractedEntities(
            dates=[
                Entity(
                    entity_type=EntityType.DATE,
                    value="2024-01-15",
                    normalized_value="2024-01-15",
                    confidence=Decimal("0.95")
                )
            ],
            people=[
                Entity(
                    entity_type=EntityType.PERSON,
                    value="Dr. Smith",
                    confidence=Decimal("0.88")
                )
            ]
        )
        print("  ✅ Entity extraction models work")
    except Exception as e:
        print(f"  ❌ Entity models failed: {e}")
        return False
    
    # Test serialization
    try:
        doc_dict = canonical_to_dict(rad_doc)
        assert isinstance(doc_dict, dict)
        assert "document_metadata" in doc_dict
        print("  ✅ Serialization to dict works")
    except Exception as e:
        print(f"  ❌ Serialization failed: {e}")
        return False
    
    return True


def test_profile_schema():
    """Test profile schema creation and validation"""
    print("\n🧪 Testing profile schema...")
    
    from src.ra_d_ps.schemas.profile import (
        Profile,
        FieldMapping,
        DataType,
        FileType,
        Transformation,
        TransformationType,
        ValidationRules,
        profile_to_dict
    )
    
    # Test profile creation
    try:
        profile = Profile(
            profile_name="test_profile",
            file_type=FileType.XML,
            description="Test profile for validation",
            mappings=[
                FieldMapping(
                    source_path="/root/element",
                    target_path="document_metadata.title",
                    data_type=DataType.STRING,
                    required=True
                ),
                FieldMapping(
                    source_path="/root/date",
                    target_path="document_metadata.date",
                    data_type=DataType.DATE,
                    required=False,
                    transformations=[
                        Transformation(
                            transformation_type=TransformationType.PARSE_DATE,
                            parameters={"format": "YYYY-MM-DD"}
                        )
                    ]
                )
            ],
            validation_rules=ValidationRules(
                required_fields=["document_metadata.title"]
            )
        )
        print("  ✅ Profile creation works")
        print(f"     Profile: {profile.profile_name}")
        print(f"     Mappings: {len(profile.mappings)}")
    except Exception as e:
        print(f"  ❌ Profile creation failed: {e}")
        return False
    
    # Test profile serialization
    try:
        profile_dict = profile_to_dict(profile)
        assert isinstance(profile_dict, dict)
        assert profile_dict["profile_name"] == "test_profile"
        print("  ✅ Profile serialization works")
    except Exception as e:
        print(f"  ❌ Profile serialization failed: {e}")
        return False
    
    # Test profile helper methods
    try:
        mapping = profile.get_mapping_by_source_path("/root/element")
        assert mapping is not None
        assert mapping.target_path == "document_metadata.title"
        
        required_fields = profile.get_required_source_fields()
        assert len(required_fields) == 1
        print("  ✅ Profile helper methods work")
    except Exception as e:
        print(f"  ❌ Profile helper methods failed: {e}")
        return False
    
    return True


def test_profile_manager():
    """Test profile manager functionality"""
    print("\n🧪 Testing profile manager...")
    
    from src.ra_d_ps.profile_manager import ProfileManager, get_profile_manager
    from src.ra_d_ps.schemas.profile import (
        Profile,
        FieldMapping,
        DataType,
        FileType
    )
    
    # Test manager initialization
    try:
        manager = get_profile_manager()
        print("  ✅ ProfileManager initialization works")
    except Exception as e:
        print(f"  ❌ ProfileManager initialization failed: {e}")
        return False
    
    # Test profile creation and saving
    try:
        test_profile = Profile(
            profile_name="validation_test_profile",
            file_type=FileType.XML,
            description="Profile for validation testing",
            mappings=[
                FieldMapping(
                    source_path="/test/field",
                    target_path="fields.test_field",
                    data_type=DataType.STRING,
                    required=True
                )
            ]
        )
        
        success = manager.save_profile(test_profile)
        assert success
        print("  ✅ Profile saving works")
    except Exception as e:
        print(f"  ❌ Profile saving failed: {e}")
        return False
    
    # Test profile loading
    try:
        loaded = manager.load_profile("validation_test_profile")
        assert loaded is not None
        assert loaded.profile_name == "validation_test_profile"
        print("  ✅ Profile loading works")
    except Exception as e:
        print(f"  ❌ Profile loading failed: {e}")
        return False
    
    # Test profile validation
    try:
        is_valid, errors = manager.validate_profile(loaded)
        assert is_valid, f"Profile validation failed: {errors}"
        print("  ✅ Profile validation works")
    except Exception as e:
        print(f"  ❌ Profile validation failed: {e}")
        return False
    
    # Test listing profiles
    try:
        profiles = manager.list_profiles()
        assert len(profiles) > 0
        print(f"  ✅ Profile listing works ({len(profiles)} profiles found)")
    except Exception as e:
        print(f"  ❌ Profile listing failed: {e}")
        return False
    
    # Cleanup
    try:
        manager.delete_profile("validation_test_profile")
        print("  ✅ Profile deletion works")
    except Exception as e:
        print(f"  ⚠️  Profile cleanup failed (non-critical): {e}")
    
    return True


def test_dependencies():
    """Test that all required dependencies are installed"""
    print("\n🧪 Testing dependencies...")
    
    required = [
        ("pydantic", "2.0.0"),
        ("pandas", "1.3.0"),
        ("openpyxl", "3.0.0"),
        ("lxml", "4.6.0"),
    ]
    
    all_ok = True
    for package, min_version in required:
        try:
            if package == "pydantic":
                import pydantic
                version = pydantic.VERSION
            elif package == "pandas":
                import pandas
                version = pandas.__version__
            elif package == "openpyxl":
                import openpyxl
                version = openpyxl.__version__
            elif package == "lxml":
                import lxml
                version = lxml.__version__
            
            print(f"  ✅ {package} {version} installed (min: {min_version})")
        except ImportError:
            print(f"  ❌ {package} not installed (required: >={min_version})")
            all_ok = False
    
    return all_ok


def test_file_structure():
    """Test that all required files exist"""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        "migrations/001_initial_schema.sql",
        "src/ra_d_ps/schemas/__init__.py",
        "src/ra_d_ps/schemas/canonical.py",
        "src/ra_d_ps/schemas/profile.py",
        "src/ra_d_ps/profile_manager.py",
        "docker-compose.yml",
        "Dockerfile",
        "configs/.env.example",
        "docs/IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md",
        "docs/SCHEMA_AGNOSTIC_SUMMARY.md",
        "QUICKSTART_SCHEMA_AGNOSTIC.md",
        "Makefile"
    ]
    
    all_exist = True
    base_path = Path(__file__).parent.parent
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("SCHEMA-AGNOSTIC FOUNDATION VALIDATION")
    print("=" * 70)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Canonical Schema", test_canonical_schema),
        ("Profile Schema", test_profile_schema),
        ("Profile Manager", test_profile_manager),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed! Foundation is solid.")
        print("✅ Ready to proceed to Phase 4: Generic XML Parser Core")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
